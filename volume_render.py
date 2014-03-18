import os
from PyOCL import *
import SpimUtils
from scipy.misc import imsave
from numpy import *
import pylab

def absPath(s):
    return os.path.join(os.path.dirname(__file__),s)

def rotMatX(phi):
    return array([cos(phi),0,sin(phi),0,
                  0,1, 0,0,
                  -sin(phi),0, cos(phi),0,
                  0,0,0,1]).reshape(4,4)


def quaternionToRotMat(q):
    a,b,c,d = q
    return array([
        [a**2+b**2-c**2-d**2, 2*(b*c-a*d), 2*(b*d+a*c),0],
        [2*(b*c+a*d), a**2-b**2+c**2-d**2, 2*(c*d-a*b),0],
        [2*(b*d-a*c), 2*(c*d+a*b),  a**2-b**2-c**2+d**2,0],
        [0,0,0,1]
        ])

def transMat(x=0,y=0,z=0):
    return array([1.0, 0.0, 0.0, 0.,
                          0.0, 1.0, 0.0, 0.0,
                          0.0, 0.0, 1.0, 0.0,
                          x, y, z, 1.0]).reshape(4,4)
def scaleMat(x =1.,y=1.,z=1.):
    return array([x, 0.0, 0.0, 0.,
                  0.0, y, 0.0, 0.0,
                  0.0, 0.0, z, 0.0,
                  0, 0, 0, 1.0]).reshape(4,4)


class VolumeRenderer:
    """ renders a data volume by ray casting/max projection

    usage:
               rend = VolumeRenderer((400,400))
               rend.set_data(d)
               rend.set_modelView(rotMatX(.7))
               out = rend.render(render_func="max_proj")
    """

    def __init__(self, size = None, useDevice = 0):
        """ e.g. size = (300,300)"""

        self.dev = OCLDevice(useDevice = useDevice)
        self.proc = OCLProcessor(self.dev,absPath("simple2.cl"))
        self.matBuf = self.dev.createBuffer(12,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)

        self._defaultModelView = transMat(0,0,4)
        self.set_units()

        if size:
            self.resize(size)
        else:
            self.resize((200,200))
        self.set_modelView(scaleMat())


    def resize(self,size):
        self.width, self.height = size
        self.buf = self.dev.createBuffer(self.height*self.width,dtype=uint16)

    def set_data(self,data):
        self._data = data
        self.set_shape(self._data.shape[::-1])
        self.dev.writeImage(self.dataImg,self._data.astype(uint16))

    def set_shape(self,dataShape):
        self.dataImg = self.dev.createImage(dataShape,
                                            mem_flags = cl.mem_flags.READ_ONLY)

    def setCLImg(self,dataImg):
        self.dataImg = dataImg

    def update_data(self,data):
        self._data = data
        # self.dev.writeImage(self.dataImg,self._data.astype(uint16))
        self.dev.writeImage(self.dataImg,data)

    def set_units(self,stackUnits = ones(3)):
        self.stackUnits = stackUnits

    def set_dataFromFolder(self,fName,pos=0):
        try:
            data = SpimUtils.fromSpimFolder(
                fName,pos=pos,count=1)[0,:,:,:]
            self.set_data(data)
        except Exception as e:
            print "set_dataFromFolder: couldnt open %s" % fName
            print e
            return
        try:
            stackSize = SpimUtils.parseIndexFile(
                os.path.join(fName,"data/index.txt"))[1:][::-1]
            stackUnits = SpimUtils.parseMetaFile(
                os.path.join(fName,"metadata.txt"))
            print stackSize, stackUnits
            self.set_units(stackUnits)
        except Exception as e:
            print e
            print "couldnt open/parse index/meta file"



    def set_modelView(self, modelView = scaleMat()):
        self.modelView = dot(self._defaultModelView,modelView)

    def _get_user_coords(self,x,y,z):
        p = array([x,y,z,1])
        worldp = dot(self.modelView,p)[:-2]
        userp = (worldp+[1.,1.])*.5*array([self.width,self.height])
        return userp[0],userp[1]


    def render(self,data = None, modelView = None,
               # density= .1, gamma = 1., offset = 0., scale = 1.,
            render_func = "max_proj"):
        """  render_func = "d_render", "max_proj" """

        if data != None:
            self.set_data(data)

        if not hasattr(self,'dataImg'):
            print "no data provided, set_data(data) before"
            return self.dev.readBuffer(self.buf,dtype = uint16).reshape(self.width,self.height)

        if not modelView and not hasattr(self,'modelView'):
            print "no modelView provided and set_modelView() not called before!"
            return self.dev.readBuffer(self.buf,dtype = uint16).reshape(self.width,self.height)

        if modelView:
            self.set_modelView(modelView)

        # scaling the data according to size and units
        Nx,Ny,Nz = self.dataImg.shape
        dx,dy,dz = self.stackUnits
        mScale =  scaleMat(1.,1.*dx*Nx/dy/Ny,1.*dx*Nx/dz/Nz)

        modelView = dot(self.modelView,mScale)

        invViewMatrix = modelView.transpose()[:-1,:]

        self.dev.writeBuffer(self.matBuf,invViewMatrix.flatten().astype(float32))

        if render_func == "max_proj":
            self.proc.runKernel("max_projectShort",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   self.matBuf,
                   self.dataImg)
        if render_func == "d_render":
            self.proc.runKernel("d_render",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   float32(density), float32(gamma),
                   float32(offset), float32(scale),
                   self.matBuf,
                   self.dataImg)

        if render_func == "test_proj":
            self.proc.runKernel("test_project",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   self.matBuf,
                   self.dataImg)


        return self.dev.readBuffer(self.buf,dtype = uint16).reshape(self.width,self.height)


# def plot_with_bounding_cube(modelView,out):
#     ppairs = [[-1,-1,-1],[-1,-1,1]
#                   ]
#     for ppair in ppairs:
#         x1,y1 = rend.get_user_coords(*ppair[0])
#         x2,y2 = rend.get_user_coords(*ppair[1])



def renderSpimFolder(fName, outName,width, height, start =0, count =-1,
                     rot = 0, isStackScale = True):
    rend = VolumeRenderer((500,500))
    for t in range(start,start+count):
        print "%i/%i"%(t+1,count)
        modelView = scaleMat()
        modelView =  dot(rotMatX(t*rot),modelView)
        modelView =  dot(transMat(0,0,4),modelView)

        rend.set_dataFromFolder(fName,pos=start+t)

        rend.set_modelView(modelView)
        out = rend.render(scale = 1200, density=.01,gamma=2,
                          isStackScale = isStackScale)

        imsave("%s_%s.png"%(outName,str(t+1).zfill(int(ceil(log10(count+1))))),out)


def test_render_simple():
    import pylab

    rend = VolumeRenderer((600,600))
    rend.set_dataFromFolder("../Data/ExampleData")

    rend.set_modelView(rotMatX(pi/2.))
    out = rend.render(render_func="max_proj")
    out = minimum(out,400)
    print rend.mScale

    # pylab.ion()

    pylab.imshow(out)
    pylab.axis('off')
    pylab.show()


def test_render_movie():

    renderSpimFolder("/Users/mweigert/Desktop/Phd/Denoise/SpimData/TestData/",
                     "output/out", 400,400,0,100,rot = .2)



if __name__ == "__main__":

    # test_render_movie()
    # test_render_simple()

    from time import time, sleep

    rend = VolumeRenderer((400,400))

    Nx,Ny,Nz = 200,150,50
    d = linspace(0,10000,Nx*Ny*Nz).reshape([Nz,Ny,Nx])

    d = SpimUtils.fromSpimFolder("../Data/Drosophila_Long",count=1)[0,...]

    rend.set_data(d)
    # rend.set_modelView(dot(transMat(0,0,0),rotMatX(1*pi/2.)))

    rend.set_units([1.,1.,4.])
    # rend._defaultModelView = transMat(0,0,0)
    print rend.modelView
    img = None
    pylab.ion()
    for t in linspace(0,pi/2.+.4,4):
        print t
        rend.set_modelView(dot(transMat(0,0,t),rotMatX(t)))
        # rend.set_modelView(transMat(0,0,2-2*t))

        print rend.modelView

        out = rend.render(render_func = "max_proj")

        if not img:
            img = pylab.imshow(out)
        else:
            img.set_data(out)
        pylab.draw()

        sleep(1)
