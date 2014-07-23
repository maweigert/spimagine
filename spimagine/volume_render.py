#!/usr/bin/env python

"""
the actual renderer class to max project 3d data

the modelView and projection matrices are compatible with OpenGL

usage:

rend = VolumeRenderer((400,400))

Nx,Ny,Nz = 200,150,50
d = linspace(0,10000,Nx*Ny*Nz).reshape([Nz,Ny,Nx])

rend.set_data(d)
rend.set_units([1.,1.,.1])
rend.set_projection(projMatPerspective(60,1.,1,10))
rend.set_modelView(dot(transMatReal(0,0,-7),scaleMat(.7,.7,.7)))

out = rend.render()



author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import logging
logger = logging.getLogger(__name__)



import os
from PyOCL import cl, OCLDevice, OCLProcessor
from scipy.misc import imsave
from transform_matrices import *
from numpy import *
from scipy.linalg import inv
import sys

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)

class VolumeRenderer:
    """ renders a data volume by ray casting/max projection

    usage:
               rend = VolumeRenderer((400,400))
               rend.set_data(d)
               rend.set_units(1.,1.,2.)
               rend.set_modelView(rotMatX(.7))
    """

    def __init__(self, size = None):
        """ e.g. size = (300,300)"""

        try:
            # simulate GPU fail...
            # raise Exception()

            self.dev = OCLDevice(useGPU = True)

            self.isGPU = True
            self.dtype = uint16

        except Exception as e:
            print e
            print "could not find GPU OpenCL device -  trying CPU..."

            try:
                self.dev = OCLDevice(useGPU = False)
                self.isGPU = False
                self.dtype = float32
            except Exception as e:
                print e
                print "could not find any OpenCL device ... sorry"

        self.memMax = self.dev.device.get_info(getattr(
            cl.device_info,"MAX_MEM_ALLOC_SIZE"))

        self.proc = OCLProcessor(self.dev,absPath("kernels/volume_render.cl"))

        self.invMBuf = self.dev.createBuffer(16,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)

        self.invPBuf = self.dev.createBuffer(16,dtype=float32,
                                            mem_flags = cl.mem_flags.READ_ONLY)

        self.set_units()

        if size:
            self.resize(size)
        else:
            self.resize((200,200))
        self.set_modelView()
        self.set_projection()


    def resize(self,size):
        self.width, self.height = size
        self.buf = self.dev.createBuffer(self.height*self.width,dtype=self.dtype)


    def get_data_slices(self,data):
        """returns the slice of data to be rendered
        in case data is bigger then gpu texture memory, we should downsample it
        """
        Nstep = int(ceil(sqrt(1.*data.nbytes/self.memMax)))
        slices = [slice(0,d,Nstep) for d in data.shape]
        if Nstep>1: 
            logger.info("downsample image by factor of  %s"%Nstep)

        return slices

    def set_data(self,data):
        self.dataSlices = self.get_data_slices(data)
        self.set_shape(data[self.dataSlices].shape[::-1])
        self.update_data(data)

    def set_shape(self,dataShape):
        if self.isGPU:
            self.dataImg = self.dev.createImage(dataShape,
                                            mem_flags = cl.mem_flags.READ_ONLY)
        else:
            self.dataImg = self.dev.createImage(dataShape,
                                            mem_flags = cl.mem_flags.READ_ONLY,
                                            channel_order = cl.channel_order.Rx,
                                            channel_type = cl.channel_type.FLOAT)

    def update_data(self,data):
        self._data = data[self.dataSlices].copy()
        if self._data.dtype != self.dtype:
            self._data = self._data.astype(self.dtype)

        self.dev.writeImage(self.dataImg,self._data)

    def set_units(self,stackUnits = ones(3)):
        self.stackUnits = np.array(stackUnits)

    def set_projection(self,projection = scaleMat()):
        self.projection = projection

    def set_modelView(self, modelView = scaleMat()):
        self.modelView = 1.*modelView

    def _get_user_coords(self,x,y,z):
        p = array([x,y,z,1])
        worldp = dot(self.modelView,p)[:-2]
        userp = (worldp+[1.,1.])*.5*array([self.width,self.height])
        return userp[0],userp[1]

    def _stack_scale_mat(self):
        # scaling the data according to size and units
        Nx,Ny,Nz = self.dataImg.shape
        dx,dy,dz = self.stackUnits

        # mScale =  scaleMat(1.,1.*dx*Nx/dy/Ny,1.*dx*Nx/dz/Nz)
        maxDim = max(d*N for d,N in zip([dx,dy,dz],[Nx,Ny,Nz]))
        return scaleMat(1.*dx*Nx/maxDim,1.*dy*Ny/maxDim,1.*dz*Nz/maxDim)


    def render(self,data = None, stackUnits = None, modelView = None):
        if data != None:
            self.set_data(data)

        if stackUnits != None:
            self.set_units(stackUnits)

        if modelView != None:
            self.set_modelView(modelView)

        if not hasattr(self,'dataImg'):
            print "no data provided, set_data(data) before"
            return self.dev.readBuffer(self.buf,dtype = self.dtype).reshape(self.width,self.height)

        if not modelView and not hasattr(self,'modelView'):
            print "no modelView provided and set_modelView() not called before!"
            return self.dev.readBuffer(self.buf,dtype = self.dtype).reshape(self.width,self.height)

        mScale = self._stack_scale_mat()

        invM = inv(dot(self.modelView,mScale))
        self.dev.writeBuffer(self.invMBuf,invM.flatten().astype(float32))

        invP = inv(self.projection)
        self.dev.writeBuffer(self.invPBuf,invP.flatten().astype(float32))

        if self.isGPU:
            self.proc.runKernel("max_project_Short",(self.width,self.height),None,
                                self.buf,
                                int32(self.width),int32(self.height),
                                self.invPBuf,
                                self.invMBuf,
                                self.dataImg)
        else:
            self.proc.runKernel("max_project_Float",(self.width,self.height),None,
                                self.buf,
                                int32(self.width),int32(self.height),
                                self.invPBuf,
                                self.invMBuf,
                                self.dataImg)


        return self.dev.readBuffer(self.buf,dtype = self.dtype).reshape(self.width,self.height)

def renderSpimFolder(fName, outName,width, height, start =0, count =-1,
                     rot = 0, isStackScale = True):
    """legacy"""

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


# def test_simple():

#     from time import time, sleep
#     from spimagine.data_model import DemoData
#     import pylab

#     rend = VolumeRenderer((400,400))

#     # Nx,Ny,Nz = 200,150,50
#     # d = linspace(0,10000,Nx*Ny*Nz).reshape([Nz,Ny,Nx])

#     d = DemoData(100)[0]
#     rend.set_data(d)
#     rend.set_units([1.,1.,.1])
#     rend.set_projection(projMatPerspective(60,1.,1,10))
#     rend.set_projection(projMatOrtho(-1,1,-1,1,-1,1))


#     img = None
#     pylab.figure()
#     pylab.ion()
#     for t in linspace(0,pi,10):
#         print t
#         rend.set_modelView(dot(transMatReal(0,0,-7),dot(rotMatX(t),scaleMat(.7,.7,.7))))

#         out = rend.render()

#         if not img:
#             img = pylab.imshow(out)
#         else:
#             img.set_data(out)
#         pylab.draw()

#         sleep(.4)



# two test functions to get the ray coordinates in the kernel...
def _getOrig(P,M,u=1,v=0):
    orig0 = dot(inv(P),[u,v,-1,1])
    orig0 = dot(inv(M),orig0)
    orig0 = orig0/orig0[-1]
    return orig0
def _getDirec(P,M,u=1,v=0):
    direc0 = dot(inv(P),[u,v,1,1])
    direc0 = direc0/direc0[-1];orig0 = dot(inv(P),[u,v,-1,1]);
    direc0 = direc0 - orig0; direc0 = direc0/norm(direc0)
    return dot(inv(M),direc0)


# def test_simple():
#     from spimagine.data_model import TiffData
#     import pylab

#     # d = TiffData("/Users/mweigert/Data/C1-wing_disc.tif")[0]
#     d = TiffData("/Users/mweigert/Data/Droso07.tif")[0]

#     rend = VolumeRenderer((400,400))

#     rend.set_data(d)
#     out = rend.render
#     pylab.imshow(out)
#     pylab.show()


if __name__ == "__main__":
    pass
    # test_simple()
