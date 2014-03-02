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
        if size:
            self.resize(size)
        else:
            self.resize((200,200))
        self.set_modelView(scaleMat())

    def resize(self,size):
        self.width, self.height = size
        self._modelView = transMat(0,0,12)

        self.buf = self.dev.createBuffer(self.height*self.width,dtype=uint16)

    def set_data(self,data, stackUnits = ones(3)):
        self._data = data
        self.dataImg = self.dev.createImage(self._data.shape[::-1],
                                            mem_flags = cl.mem_flags.READ_ONLY)
        self.dev.writeImage(self.dataImg,self._data.astype(uint16))
        self.set_scale(self._data.shape[::-1],stackUnits)



    def update_data(self,data):
        self._data = data
        self.dev.writeImage(self.dataImg,self._data.astype(uint16))

    def set_scale(self,stackSize,stackUnits):
        Nx,Ny,Nz = stackSize
        dx,dy,dz = stackUnits
        self.mScale =  scaleMat(1.,1.*dx*Nx/dy/Ny,1.*dx*Nx/dz/Nz)

    def set_dataFromFolder(self,fName,pos=0):
        try:
            data = SpimUtils.fromSpimFolder(
                fName,pos=pos,count=1)[0,:,:,:]
            self.set_data(data)
        except:
            print "set_dataFromFolder: couldnt open %s" % fName
            return
        try:
            stackSize = SpimUtils.parseIndexFile(
                os.path.join(fName,"data/index.txt"))[1:][::-1]
            stackUnits = SpimUtils.parseMetaFile(
                os.path.join(fName,"metadata.txt"))
            print stackSize, stackUnits
            self.set_scale(stackSize,stackUnits)
        except:
            print "couldnt open/parse index/meta file"



    def set_modelView(self, modelView = scaleMat()):
        self.modelView = dot(self._modelView,modelView)

    def _get_user_coords(self,x,y,z):
        p = array([x,y,z,1])
        worldp = dot(self.modelView,p)[:-2]
        userp = (worldp+[1.,1.])*.5*array([self.width,self.height])
        return userp[0],userp[1]


    def render(self,modelView = None, data = None,
               density= .1, gamma = 1., offset = 0., scale = 1.,
               isStackScale = True, render_func = "d_render"):
        """  render_func = "d_render", "max_proj" """

        if data != None:
            self.set_data(data)

        if modelView:
            self.set_modelView(modelView)
        if not modelView and not hasattr(self,'modelView'):
            print "no modelView provided and set_modelView() not called before!"
            return self.dev.readBuffer(self.buf,dtype = uint16).reshape(self.width,self.height)

        if isStackScale and hasattr(self,'mScale'):
            modelView = dot(self.modelView,self.mScale)
        else:
            modelView = 1.*self.modelView

        invViewMatrix = modelView.transpose()[:-1,:]

        self.dev.writeBuffer(self.matBuf,invViewMatrix.flatten().astype(float32))

        if render_func == "max_proj":
            self.proc.runKernel("max_projectShort",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   self.matBuf,
                   self.dataImg)
        else:
            self.proc.runKernel("d_render",(self.width,self.height),None,
                   self.buf,
                   int32(self.width),int32(self.height),
                   float32(density), float32(gamma),
                   float32(offset), float32(scale),
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
    rend.set_dataFromFolder("../Data/Drosophila_Single")

    rend.set_modelView(rotMatX(pi/2.))
    out = rend.render(render_func="max_proj")
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


    test_render_simple()

    # from time import time

    # t = time()
    # rend = VolumeRenderer((400,400))
    # print time()-t

    # d = ones([200,200,200])


    # t = time()
    # rend.set_data(d)
    # print time()-t

    # t = time()
    # out = rend.render()
    # print time()-t


    # pylab.imshow(out)

    # pylab.show()
