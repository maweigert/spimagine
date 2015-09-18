
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


#this is due to some pyinstaller bug!
from scipy.integrate import *


from scipy.misc import imsave
import numpy as np
from scipy.linalg import inv

from time import time


import sys

from gputools import init_device, get_device, OCLProgram, OCLArray, OCLImage
from gputools.core.config import cl_datatype_dict

from spimagine.utils.transform_matrices import *

import spimagine

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

            # self.dev = OCLDevice(useGPU = True, 
            #                      useDevice = spimagine.__OPENCLDEVICE__)
            init_device(useGPU = True, 
                                 useDevice = spimagine.config.__OPENCLDEVICE__)
            self.isGPU = True
            self.dtypes = [np.float32,np.uint16]

        except Exception as e:
            print e
            print "could not find GPU OpenCL device -  trying CPU..."

            try:
                init_device(useGPU = False)
                self.isGPU = False
                self.dtypes = [np.float32]
            except Exception as e:
                print e
                print "could not find any OpenCL device ... sorry"

        self.memMax = .4*get_device().get_info("MAX_MEM_ALLOC_SIZE")

        self.memMax = 2.*get_device().get_info("MAX_MEM_ALLOC_SIZE")

        try:
            self.proc = OCLProgram(absPath("kernels/volume_render.cl"),
                                   build_options =
                                   ["-cl-fast-relaxed-math",
                                    "-cl-unsafe-math-optimizations",
                                    "-cl-mad-enable",
                                    "-I %s" %absPath("kernels/"),
                                    "-D maxSteps=%s"%spimagine.config.__DEFAULTMAXSTEPS__]
                                   )
        except Exception as e:
            logger.debug(str(e))
            self.proc = OCLProgram(absPath("kernels/volume_render.cl"),
                                   build_options =
                                   ["-I %s" %absPath("kernels/"),
                                    "-D maxSteps=%s"%spimagine.config.__DEFAULTMAXSTEPS__]
            )


        self.invMBuf = OCLArray.empty(16,dtype=np.float32)
        
        self.invPBuf = OCLArray.empty(16,dtype=np.float32)
        
        self.projection = np.zeros((4,4))
        self.modelView = np.zeros((4,4))
                
        if size:
            self.resize(size)
        else:
            self.resize((200,200))

        self.set_dtype()
        self.set_gamma()
        self.set_max_val()
        self.set_min_val()

        self.set_alpha_pow()
        self.set_box_boundaries()
        self.set_units()

        self.set_modelView()
        self.set_projection()

    def set_dtype(self,dtype = None):
        if hasattr(self,"dtype") and  dtype is self.dtype:
            return

        if dtype is None:
            dtype = self.dtypes[0]

        if dtype in self.dtypes:
            self.dtype = dtype
        else:
            raise NotImplementedError("data type should be either %s not %s"%(self.dtypes,dtype))

        self.reset_buffer()


    def resize(self,size):
        self.width, self.height = size
        self.reset_buffer()


    def reset_buffer(self):
        self.buf = OCLArray.empty((self.height,self.width),dtype=np.float32)
        self.bufAlpha = OCLArray.empty((self.height,self.width),dtype=np.float32)
        self.bufDepth = OCLArray.empty((self.height,self.width),dtype=np.float32)

        # self.bufNormals = OCLArray.empty(3*self.height*self.width,dtype=np.float32)

        # self.bufNormalsScratch = OCLArray.empty(3*self.height*self.width,dtype=np.float32)
        


    def _get_downsampled_data_slices(self,data):
        """in case data is bigger then gpu texture memory, we should downsample it
        if so returns the slice of data to be rendered
        else returns None (no downsampling)
        """
        # Nstep = int(np.ceil(np.sqrt(1.*data.nbytes/self.memMax)))
        Nstep = int(np.ceil((1.*data.nbytes/self.memMax)**(1./3)))

        slices = [slice(0,d,Nstep) for d in data.shape]
        if Nstep>1:
            logger.info("downsample image by factor of  %s"%Nstep)
            return slices
        else:
            return None

    def set_max_val(self,maxVal = 0.):
        self.maxVal = maxVal

    def set_min_val(self,minVal = 0.):
        self.minVal = minVal
        
    def set_gamma(self,gamma = 1.):
        self.gamma = gamma

    def set_alpha_pow(self,alphaPow = 10.):
        self.alphaPow = alphaPow


    def set_data(self,data, autoConvert = True, copyData = False):
        if not autoConvert and not data.dtype in self.dtypes:
            raise NotImplementedError("data type should be either %s not %s"%(self.dtypes,data.dtype))

        if data.dtype.type in self.dtypes:
            self.set_dtype(data.dtype.type)
            _data = data
        else:
            print "converting type from %s to %s"%(data.dtype.type,self.dtype)
            _data = data.astype(self.dtype,copy = False)

        self.dataSlices = self._get_downsampled_data_slices(_data)

        if self.dataSlices is not None:
            self.set_shape(_data[self.dataSlices].shape[::-1])
        else:
            self.set_shape(_data.shape[::-1])

        t = time()
        self.update_data(_data, copyData = copyData)
        logger.debug("update data: %s ms"%(1000.*(time()-t))) 
        self.update_matrices()

    def set_shape(self,dataShape):
        if self.isGPU:
            self.dataImg = OCLImage.empty(dataShape[::-1],dtype= self.dtype)
        else:
            raise NotImplementedError("TODO")
            # self.dataImg = self.dev.createImage(dataShape,
            #     mem_flags = cl.mem_flags.READ_ONLY,
            #     channel_order = cl.channel_order.INTENSITY,
            #     channel_type = cl_datatype_dict[self.dtype])

        # if self.isGPU:
        #     self.dataImg = self.dev.createImage(dataShape,
        #         mem_flags = cl.mem_flags.READ_ONLY,
        #         channel_type = cl_datatype_dict[self.dtype])
        # else:
        #     self.dataImg = self.dev.createImage(dataShape,
        #         mem_flags = cl.mem_flags.READ_ONLY,
        #         channel_order = cl.channel_order.INTENSITY,
        #         channel_type = cl_datatype_dict[self.dtype])

    def update_data(self,data, copyData = False):
        #do we really want to copy here?
        
        if self.dataSlices is not None:
            self._data = data[self.dataSlices].copy()
        else:
            if copyData:
                self._data = data.copy()
            else:
                self._data = data

        if self._data.dtype != self.dtype:
            self._data = self._data.astype(self.dtype,copy=False)

        self.dataImg.write_array(self._data)

    def set_box_boundaries(self,boxBounds = [-1,1,-1,1,-1,1]):
        self.boxBounds = np.array(boxBounds)

    def set_units(self,stackUnits = np.ones(3)):
        self.stackUnits = np.array(stackUnits)

    def set_projection(self,projection = mat4_identity()):
        self.projection = projection
        self.update_matrices()

        
    def set_modelView(self, modelView = mat4_identity()):
        self.modelView = 1.*modelView
        self.update_matrices()

    def update_matrices(self):
        if hasattr(self,"dataImg"):
            mScale = self._stack_scale_mat()
            invM = inv(np.dot(self.modelView,mScale))
            self.invMBuf.write_array(invM.flatten().astype(np.float32))
            invP = inv(self.projection)
            self.invPBuf.write_array(invP.flatten().astype(np.float32))

    # def _get_user_coords(self,x,y,z):
    #     p = array([x,y,z,1])
    #     worldp = dot(self.modelView,p)[:-2]
    #     userp = (worldp+[1.,1.])*.5*array([self.width,self.height])
    #     return userp[0],userp[1]

    def _stack_scale_mat(self):
        # scaling the data according to size and units
        Nx,Ny,Nz = self.dataImg.shape
        dx,dy,dz = self.stackUnits

        # mScale =  scaleMat(1.,1.*dx*Nx/dy/Ny,1.*dx*Nx/dz/Nz)
        maxDim = max(d*N for d,N in zip([dx,dy,dz],[Nx,Ny,Nz]))
        return mat4_scale(1.*dx*Nx/maxDim,1.*dy*Ny/maxDim,1.*dz*Nz/maxDim)


    def render(self,data = None, stackUnits = None,
               minVal = None, maxVal = None, gamma = None,
               modelView = None, projection = None,
               boxBounds = None, return_alpha = False, method="max_project",
               numParts = 1, currentPart = 0):

        if data is not None:
            self.set_data(data)

        if maxVal is not None:
            self.set_max_val(maxVal)

        if minVal is not None:
            self.set_min_val(minVal)

        if gamma is not None:
            self.set_gamma(gamma)

        if stackUnits is not None:
            self.set_units(stackUnits)

        if modelView is not None:
            self.set_modelView(modelView)

        if projection is not None:
            self.set_projection(projection)

        if not hasattr(self,'dataImg'):
            print "no data provided, set_data(data) before"
            if return_alpha:
                return self.buf.get(), self.bufAlpha.get()
            else:
                return self.buf.get()


        if  modelView is None and not hasattr(self,'modelView'):
            print "no modelView provided and set_modelView() not called before!"
            if return_alpha:
                return self.buf.get(), self.bufAlpha.get()
            else:
                return self.buf.get()

        # mScale = self._stack_scale_mat()
        # invM = inv(np.dot(self.modelView,mScale))
        # self.dev.writeBuffer(self.invMBuf,invM.flatten().astype(np.float32))

        # invP = inv(self.projection)
        # self.dev.writeBuffer(self.invPBuf,invP.flatten().astype(np.float32))

        if method=="max_project":
            if self.dtype == np.uint16:
                method = "max_project_short"
            else:
                method = "max_project_float"

            self.proc.run_kernel(method,
                            (self.width,self.height),
                            None,
                            self.buf.data,self.bufAlpha.data,
                            np.int32(self.width),np.int32(self.height),
                            np.float32(self.boxBounds[0]),
                            np.float32(self.boxBounds[1]),
                            np.float32(self.boxBounds[2]),
                            np.float32(self.boxBounds[3]),
                            np.float32(self.boxBounds[4]),
                            np.float32(self.boxBounds[5]),
                            np.float32(self.minVal),                                
                            np.float32(self.maxVal),
                            np.float32(self.gamma),
                            np.float32(self.alphaPow),
                            self.invPBuf.data,
                            self.invMBuf.data,
                            self.dataImg)


        if method=="max_project_part":
            if self.dtype == np.uint16:
                method = "max_project_part_short"
            else:
                method = "max_project_part_float"

            self.proc.run_kernel(method,
                            (self.width,self.height),
                            None,
                            self.buf.data,self.bufAlpha.data,
                            np.int32(self.width),np.int32(self.height),
                            np.float32(self.boxBounds[0]),
                            np.float32(self.boxBounds[1]),
                            np.float32(self.boxBounds[2]),
                            np.float32(self.boxBounds[3]),
                            np.float32(self.boxBounds[4]),
                            np.float32(self.boxBounds[5]),
                            np.float32(self.minVal),                                
                            np.float32(self.maxVal),
                            np.float32(self.gamma),
                            np.float32(self.alphaPow),
                            np.int32(numParts),
                            np.int32(currentPart),
                            self.invPBuf.data,
                            self.invMBuf.data,
                            self.dataImg)

        if method=="iso_surface":
            self.proc.run_kernel("iso_surface",
                            (self.width,self.height),
                            None,
                            self.buf.data,self.bufAlpha.data,
                            np.int32(self.width),np.int32(self.height),
                            np.float32(self.boxBounds[0]),
                            np.float32(self.boxBounds[1]),
                            np.float32(self.boxBounds[2]),
                            np.float32(self.boxBounds[3]),
                            np.float32(self.boxBounds[4]),
                            np.float32(self.boxBounds[5]),
                            np.float32(self.maxVal/2),
                            np.float32(self.gamma),
                            self.invPBuf.data,
                            self.invMBuf.data,
                            self.dataImg,
                            np.int32(self.dtype == np.uint16)
                            )

        if return_alpha:
            return self.buf.get(), self.bufAlpha.get()
        else:
            return self.buf.get()


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


def test_simple():
    import pylab
    
    N= 64
    d = np.linspace(0,1,N**3).reshape((N,)*3).astype(np.float32)

    rend = VolumeRenderer((400,400))

    rend.set_data(d)
    out = rend.render()
    pylab.imshow(out)
    pylab.show()

def test_simple2():
    import time

    N = 64

    x = np.linspace(-1,1,N)
    Z,Y,X = np.meshgrid(x,x,x,indexing="ij")
    R = np.sqrt(X**2+Y**2+Z**2)

    
    d = 10000*np.exp(-10*R**2)

    rend = VolumeRenderer((600,600))

    # rend.set_modelView(mat4_rotation(.5,0,1.,0))
    rend.set_modelView(mat4_translate(0,0,-10.))

    # rend.set_box_boundaries(.3*np.array([-1,1,-1,1,-1,1]))
    t1 = time.time()

    rend.dev.queue.finish()
    rend.set_data(d, autoConvert = True)
    rend.dev.queue.finish()

    t2 = time.time()

    rend.dev.queue.finish()
    out = rend.render(maxVal = 10000.)
    rend.dev.queue.finish()

    print "time to set data %s^3:\t %.2f ms"%(N,1000*(t2-t1))

    print "time to render %s^3:\t %.2f ms"%(N,1000*(time.time()-t2))

    return d, rend, out

def test_new_iso():
    import time

    N = 128

    x = np.linspace(-1,1,N)
    Z,Y,X = np.meshgrid(x,x,x,indexing="ij")
    R = np.sqrt(X**2+Y**2+Z**2)

    
    d = 10000*np.exp(-10*R**2)
    d += 00*np.random.uniform(-1,1,d.shape) 

    rend = VolumeRenderer((600,600))

    # rend.set_modelView(mat4_rotation(.5,0,1.,0))
    rend.set_modelView(mat4_translate(0,0,-1.))

    # rend.set_box_boundaries(.3*np.array([-1,1,-1,1,-1,1]))
    t1 = time.time()

    rend.dev.queue.finish()
    rend.set_data(d, autoConvert = True)
    rend.dev.queue.finish()

    t2 = time.time()

    rend.dev.queue.finish()
    out = rend.render(maxVal = 1000., method="iso_surface_new")
    rend.dev.queue.finish()

    print "time to set data %s^3:\t %.2f ms"%(N,1000*(t2-t1))

    print "time to render %s^3:\t %.2f ms"%(N,1000*(time.time()-t2))

    return d, rend, out

def test_real():
    import imgtools
    import time

    d = imgtools.read3dTiff("/Users/mweigert/Data/sqeazy_corpus/Norden_GFP-LAP_4-1.tif")

    rend = VolumeRenderer((600,600))

    rend.set_modelView(mat4_rotation(.5,0,1.,0))

    # rend.set_box_boundaries(.3*np.array([-1,1,-1,1,-1,1]))
    t1 = time.time()

    rend.set_data(d, autoConvert = True)
    rend.set_units([1.,1.,6.])
    t2 = time.time()

    out = rend.render(maxVal = 200.)

    print "time to set data :\t %.2f ms"%(1000*(t2-t1))

    print "time to render:\t %.2f ms"%(1000*(time.time()-t2))

    return d, rend, out


def test_speed(N=128,renderWidth = 400, numParts = 1):
    import time

    d = np.ones((N,)*3,dtype=np.float32)
    rend = VolumeRenderer((renderWidth,)*2)


    # rend.set_box_boundaries(.3*np.array([-1,1,-1,1,-1,1]))
    t1 = time.time()

    rend.dev.queue.finish()
    rend.set_data(d, autoConvert = True)
    rend.dev.queue.finish()

    rend.set_modelView(mat4_rotation(.5,0,1.,0))

    t2 = time.time()
    rend.dev.queue.finish()
    for i in range(10):
        out = rend.render(method = "max_project_part", maxVal = 200.,
                          currentPart=0,numParts=numParts)
    rend.dev.queue.finish()

    t3 = time.time()

    print "time to set data %s^3:\t %.2f ms"%(N,1000.*(t2-t1))

    print "time to render %s^3:\t %.2f ms"%(N,1000./10.*(t3-t2))

    return 1000./10.*(t3-t2)

    
if __name__ == "__main__":
    # test_simple()
    # test_speed(256)

    import os
    os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'
    os.environ['PYOPENCL_NO_CACHE'] = '1'
    
    N= 64

    x = np.linspace(-1,1,N)
    R = np.sqrt(np.sum([_X**2 for _X in np.meshgrid(x,x,x,indexing="ij")],axis=0))

    d = np.exp(-50*(R-.3)**2)
    
    rend = VolumeRenderer((400,400))
    rend.set_modelView(mat4_translate(0,0,5.))

    rend.set_data(d.astype(np.float32))
    out = rend.render(maxVal = 1., method = "max_project_part")
    # out = rend.render(maxVal = 1., method = "iso_surface")

    import pylab
    pylab.figure(1)
    pylab.clf()
    pylab.imshow(out)
    pylab.show()
