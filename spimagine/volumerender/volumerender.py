# !/usr/bin/env python

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

from __future__ import absolute_import, print_function

import logging
from six.moves import range
from six.moves import zip

logger = logging.getLogger(__name__)

import os
# this is due to some pyinstaller bug!
from scipy.integrate import *
from scipy.misc import imsave
import numpy as np
from scipy.linalg import inv
from time import time
import sys
from gputools import init_device, get_device, OCLProgram, OCLArray, OCLImage
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
    dtypes = [np.float32, np.uint16, np.uint8]

    def __init__(self, size=None):
        """ e.g. size = (300,300)"""

        try:
            # simulate GPU fail...
            # raise Exception()

            # self.dev = OCLDevice(useGPU = True, 
            #                      useDevice = spimagine.__OPENCLDEVICE__)

            # FIXME
            # device should not be reinitialized as then
            # every other queue becomes invalid
            # init_device(useGPU = True,
            #             useDevice = spimagine.config.__OPENCLDEVICE__)
            self.isGPU = True


        except Exception as e:
            print(e)
            print("could not find GPU OpenCL device -  trying CPU...")

            try:
                init_device(useGPU=False)
                self.isGPU = False
                self.dtypes = [np.float32]
            except Exception as e:
                print(e)
                print("could not find any OpenCL device ... sorry")

        self.memMax = .7*get_device().get_info("MAX_MEM_ALLOC_SIZE")

        # self.memMax = 2.*get_device().get_info("MAX_MEM_ALLOC_SIZE")

        build_options_basic = ["-I", "%s"%absPath("kernels/"),
                               "-D", "maxSteps=%s"%spimagine.config.__DEFAULTMAXSTEPS__]

        self.proc = OCLProgram(absPath("kernels/all_render_kernels.cl"),
                               build_options=
                               build_options_basic+
                               ["-cl-finite-math-only",
                                "-cl-fast-relaxed-math",
                                "-cl-unsafe-math-optimizations",
                                "-cl-mad-enable"])
        try:
            pass

        except Exception as e:

            logger.debug(str(e))
            self.proc = OCLProgram(absPath("kernels/all_render_kernels.cl"),
                                   build_options=
                                   build_options_basic)

        self.invMBuf = OCLArray.empty(16, dtype=np.float32)

        self.invPBuf = OCLArray.empty(16, dtype=np.float32)

        self.projection = np.zeros((4, 4))
        self.modelView = np.zeros((4, 4))

        if size:
            self.resize(size)
        else:
            self.resize((200, 200))

        self.set_dtype()
        self.set_gamma()
        self.set_max_val()
        self.set_min_val()

        self.set_occ_strength(.1)
        self.set_occ_radius(21)
        self.set_occ_n_points(30)

        self.set_alpha_pow()
        self.set_box_boundaries()
        self.set_units()

        self.set_modelView()
        self.set_projection()

    def set_dtype(self, dtype=None):
        if hasattr(self, "dtype") and dtype is self.dtype:
            return

        if dtype is None:
            dtype = self.dtypes[0]

        if dtype in self.dtypes:
            self.dtype = dtype
        else:
            raise NotImplementedError("data type should be either %s not %s"%(self.dtypes, dtype))

        self.reset_buffer()

    def resize(self, size):
        self.width, self.height = size
        self.reset_buffer()

    def reset_buffer(self):
        self.buf = OCLArray.empty((self.height, self.width), dtype=np.float32)
        self.buf_alpha = OCLArray.empty((self.height, self.width), dtype=np.float32)
        self.buf_depth = OCLArray.empty((self.height, self.width), dtype=np.float32)
        self.buf_normals = OCLArray.empty((self.height, self.width, 3), dtype=np.float32)
        self.buf_tmp = OCLArray.empty((self.height, self.width), dtype=np.float32)
        self.buf_tmp_vec = OCLArray.empty((self.height, self.width, 3), dtype=np.float32)

        self.buf_occlusion = OCLArray.empty((self.height, self.width), dtype=np.float32)

        self.output = np.zeros((self.height, self.width), dtype=np.float32)
        self.output_alpha = np.zeros((self.height, self.width), dtype=np.float32)
        self.output_depth = np.zeros((self.height, self.width), dtype=np.float32)

    def _get_downsampled_data_slices(self, data):
        """in case data is bigger then gpu texture memory, we should downsample it
        if so returns the slice of data to be rendered
        else returns None (no downsampling)
        """
        # Nstep = int(np.ceil(np.sqrt(1.*data.nbytes/self.memMax)))
        Nstep = int(np.ceil((1.*data.nbytes/self.memMax)**(1./3)))

        slices = [slice(0, d, Nstep) for d in data.shape]
        if Nstep>1:
            logger.info("downsample image by factor of  %s"%Nstep)
            return slices
        else:
            return None

    def set_max_val(self, maxVal=0.):
        self.maxVal = maxVal

    def set_min_val(self, minVal=0.):
        self.minVal = minVal

    def set_gamma(self, gamma=1.):
        self.gamma = gamma

    def set_occ_strength(self, occ=.2):
        self.occ_strength = occ

    def set_occ_radius(self, rad=21):
        self.occ_radius = rad

    def set_occ_n_points(self, n_points=31):
        self.occ_n_points = n_points

    def set_alpha_pow(self, alphaPow=0.):
        self.alphaPow = alphaPow

    def set_data(self, data, autoConvert=True, copyData=False):
        logger.debug("set_data")

        if not autoConvert and not data.dtype in self.dtypes:
            raise NotImplementedError("data type should be either %s not %s"%(self.dtypes, data.dtype))

        if data.dtype.type in self.dtypes:
            self.set_dtype(data.dtype.type)
            _data = data
        else:
            print("converting type from %s to %s"%(data.dtype.type, self.dtype))
            _data = data.astype(self.dtype, copy=False)

        self.dataSlices = self._get_downsampled_data_slices(_data)

        if self.dataSlices is not None:
            self.set_shape(_data[self.dataSlices].shape[::-1])
        else:
            self.set_shape(_data.shape[::-1])

        t = time()
        self.update_data(_data, copyData=copyData)
        logger.debug("update data: %s ms"%(1000.*(time()-t)))
        self.update_matrices()

    def set_shape(self, dataShape):
        if self.isGPU:
            self.dataImg = OCLImage.empty(dataShape[::-1], dtype=self.dtype)
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

    def update_data(self, data, copyData=False):
        # do we really want to copy here?

        if self.dataSlices is not None:
            self._data = data[self.dataSlices].copy()
        else:
            if copyData:
                self._data = data.copy()
            else:
                self._data = data

        if self._data.dtype!=self.dtype:
            self._data = self._data.astype(self.dtype, copy=False)

        self.dataImg.write_array(self._data)

    def set_box_boundaries(self, boxBounds=[-1, 1, -1, 1, -1, 1]):
        self.boxBounds = np.array(boxBounds)

    def set_units(self, stackUnits=np.ones(3)):
        self.stackUnits = np.array(stackUnits)

    def set_projection(self, projection=mat4_perspective()):
        self.projection = projection
        self.update_matrices()

    def set_modelView(self, modelView=mat4_identity()):
        self.modelView = 1.*modelView
        self.update_matrices()

    def update_matrices(self):
        if hasattr(self, "dataImg"):
            mScale = self._stack_scale_mat()
            invM = inv(np.dot(self.modelView, mScale))
            self.invMBuf.write_array(invM.flatten().astype(np.float32))
            invP = inv(self.projection)
            self.invPBuf.write_array(invP.flatten().astype(np.float32))

    def _stack_scale_mat(self):
        # scaling the data according to size and units
        Nx, Ny, Nz = self.dataImg.shape
        dx, dy, dz = self.stackUnits

        # mScale =  scaleMat(1.,1.*dx*Nx/dy/Ny,1.*dx*Nx/dz/Nz)
        maxDim = max(d*N for d, N in zip([dx, dy, dz], [Nx, Ny, Nz]))
        return mat4_scale(1.*dx*Nx/maxDim, 1.*dy*Ny/maxDim, 1.*dz*Nz/maxDim)

    def _render_max_project(self, dtype=np.float32, numParts=1, currentPart=0):
        if dtype in [np.uint16, np.uint8]:
            method = "max_project_short"
        elif dtype==np.float32:
            method = "max_project_float"
        else:
            raise NotImplementedError("wrong dtype: %s", dtype)

        self.proc.run_kernel(method,
                             (self.width, self.height),
                             None,
                             self.buf.data, self.buf_alpha.data,
                             self.buf_depth.data,
                             np.int32(self.width), np.int32(self.height),
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
        self.output = self.buf.get()
        self.output_alpha = self.buf_alpha.get()
        self.output_depth = self.buf_depth.get()

    def _convolve_scalar(self, buf, radius=11):

        self.proc.run_kernel("conv_x",
                             (self.width, self.height), None,
                             buf.data,
                             self.buf_tmp.data,
                             np.int32(radius))
        self.proc.run_kernel("conv_y",
                             (self.width, self.height), None,
                             self.buf_tmp.data,
                             buf.data,
                             np.int32(radius))

    def _convolve_vec(self, buf, radius=11):
        self.proc.run_kernel("conv_vec_x",
                             (self.width, self.height), None,
                             buf.data,
                             self.buf_tmp_vec.data,
                             np.int32(radius))

        self.proc.run_kernel("conv_vec_y",
                             (self.width, self.height), None,
                             self.buf_tmp_vec.data,
                             buf.data,
                             np.int32(radius))

    def _render_isosurface2(self):
        self.proc.run_kernel("iso_surface",
                             (self.width, self.height),
                             None,
                             self.buf.data, self.buf_alpha.data,
                             self.buf_depth.data, self.buf_normals.data,
                             np.int32(self.width), np.int32(self.height),
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
                             np.int32(self.dtype in [np.uint16, np.uint8])
                             )

        self._convolve_vec(self.buf_normals, 5)

        self.output = self.buf.get()
        self.output_alpha = self.buf_alpha.get()
        self.output_depth = self.buf_depth.get()
        self.output_normals = self.buf_normals.get()

    def _render_isosurface(self):
        """
        with ambient occlusion
        """

        self.proc.run_kernel("iso_surface",
                             (self.width, self.height),
                             None,
                             self.buf.data, self.buf_alpha.data,
                             self.buf_depth.data, self.buf_normals.data,
                             np.int32(self.width), np.int32(self.height),
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
                             np.int32(self.dtype in [np.uint16, np.uint8])
                             )
        self._convolve_vec(self.buf_normals, 7)

        self.proc.run_kernel("occlusion",
                             (self.width, self.height),
                             None,
                             self.buf_occlusion.data,
                             np.int32(self.width), np.int32(self.height),
                             np.int32(self.occ_radius),
                             np.int32(self.occ_n_points),
                             self.buf_depth.data,
                             self.buf_normals.data,
                             )

        self._convolve_scalar(self.buf_occlusion, 5)

        self.proc.run_kernel("shading",
                             (self.width, self.height),
                             None,
                             self.buf.data, self.buf_alpha.data,
                             np.int32(self.width), np.int32(self.height),
                             self.invPBuf.data,
                             self.invMBuf.data,
                             np.float32(self.occ_strength),
                             self.buf_normals.data,
                             self.buf_depth.data,
                             self.buf_occlusion.data,

                             )

        # self._convolve_scalar(self.buf,13)
        # self._convolve_vec(self.buf_normals,101)

        self.output = self.buf.get()
        self.output_alpha = self.buf_alpha.get()
        self.output_depth = self.buf_depth.get()
        self.output_normals = self.buf_normals.get()
        self.output_occlusion = self.buf_occlusion.get()

    def render(self, data=None, stackUnits=None,
               minVal=None, maxVal=None, gamma=None,
               modelView=None, projection=None,
               boxBounds=None, return_alpha=False, method="max_project",
               numParts=1, currentPart=0):

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

        if not hasattr(self, 'dataImg'):
            print("no data provided, set_data(data) before")
            return

        if modelView is None and not hasattr(self, 'modelView'):
            print("no modelView provided and set_modelView() not called before!")
            return

        if method=="max_project":
            self._render_max_project(self.dtype, numParts, currentPart)

        if method=="iso_surface":
            self._render_isosurface()

