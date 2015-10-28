"""


mweigert@mpi-cbg.de

"""

#!/usr/bin/env python

"""
Description
A class encapulsating transfer functions/ maps
author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import spimagine

import logging

logger = logging.getLogger(__name__)

import numpy as np

from OpenGL.GL import *

class TransferMap(object):
    """
    """

    def __init__(self, rgb_or_name = None):
        if rgb_or_name is None:
            rgb_or_name = (1.,.4,.2)
        self._texture = None

        self.set_cmap(rgb_or_name)

    def init_GL(self):
        self._texture = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self._texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glTexParameterf (GL_TEXTURE_2D,
                         GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf (GL_TEXTURE_2D,
                         GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def fill_texture(self):
        """ data.shape == (Ny,Nx)
        file texture with GL_RED
        data.shape == (Ny,Nx,3)
        file texture with GL_RGB
        data.shape == (Ny,Nx,4)
        file texture with GL_RGBA
        """
        if self._texture is None:
            return

        glBindTexture(GL_TEXTURE_2D, self._texture)

        if self._arr.ndim == 2:
            Ny, Nx = self._arr.shape
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                     0, GL_RED, GL_FLOAT, self._arr.astype(np.float32))


        elif self._arr.ndim == 3:
            if self._arr.shape[2]==3:
                Ny,Nx = self._arr.shape[:2]
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                         0, GL_RGB, GL_FLOAT, self._arr.astype(np.float32))
            elif self._arr.shape[2]==4:
                Ny,Nx = self._arr.shape[:2]
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, Nx, Ny,
                         0, GL_RGBA, GL_FLOAT, self._arr.astype(np.float32))
            else:
                raise Exception("data format not supported! \ndata.shape should be either (Ny,Nx), (Ny,Nx,3) or (Ny,Nx,4)")
        else:
            raise Exception("data format not supported! \ndata.shape should be either (Ny,Nx), (Ny,Nx,3) or (Ny,Nx,4)")


    def _set_array(self,arr):
        """set the colormap from an array of shape (N,4)"""
        self._arr = arr.reshape((1,)+arr.shape)


    def set_cmap(self, rgb_or_name = None):
        if rgb_or_name is None:
            self._set_cmap_rgb([1.,1.,1.])
        else:
            if isinstance(rgb_or_name,str):
                self._set_cmap_name(rgb_or_name)
            else:
                self._set_cmap_rgb(rgb_or_name)
        self.fill_texture()



    def _set_cmap_rgb(self, col = [1.,1.,1.,1.]):
        """set the colormap by name"""
        self._set_array(np.outer(np.linspace(0,1.,256),np.array(col)))


    def _set_cmap_name(self, name = "hot"):
        """set the colormap by name"""

        try:
            self._set_array(spimagine.__COLORMAPDICT__[name])
        except KeyError:
            logger.info("not a valid color map: %s  "%name)
            logger.info("valid keys: %s"%(spimagine.__COLORMAPDICT__.keys()))

    def _fill_texture(self):
        """ data.shape == (Ny,Nx)
        file texture with GL_RED
        data.shape == (Ny,Nx,3)
        file texture with GL_RGB
        data.shape == (Ny,Nx,4)
        file texture with GL_RGBA
        """

        glBindTexture(GL_TEXTURE_2D, self._texture)

        if self._arr.ndim == 2:
            Ny,Nx = self._arr.shape
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                     0, GL_RED, GL_FLOAT, self._arr.astype(np.float32))

        elif self._arr.ndim == 3:
            if self._arr.shape[2]==3:
                Ny,Nx = self._arr.shape[:2]
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                         0, GL_RGB, GL_FLOAT, self._arr.astype(np.float32))
            elif self._arr.shape[2]==4:
                Ny,Nx = self._arr.shape[:2]
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, Nx, Ny,
                         0, GL_RGBA, GL_FLOAT, self._arr.astype(np.float32))
            else:
                raise Exception("data format not supported! \ndata.shape should be either (Ny,Nx), (Ny,Nx,3) or (Ny,Nx,4)")
        else:
            raise Exception("data format not supported! \ndata.shape should be either (Ny,Nx), (Ny,Nx,3) or (Ny,Nx,4)")


    def apply(self,img):
        """ apply the colormap to a 2d array"""
        raise NotImplementedError()


    def __del__(self):
        if self._texture is not None:
            glDeleteTextures([self._texture])


if __name__ == '__main__':


    map = TransferMap("hot")
