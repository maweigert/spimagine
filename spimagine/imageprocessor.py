"""
Implements generic classes for processing of volumetric data
"""

import numpy as np
import imgtools

class ImageProcessor(object):
    def __init__(self,**kwargs):
        self.set_params(**kwargs)

    def set_params(self,**kwargs):
        self.kwargs = kwargs

    def apply(self, data):
        raise NotImplementedError()

    def __getattr__(self,attr):
        if self.kwargs.has_key(attr):
            return self.kwargs[attr]
        else:
            return super(ImageProcessor,self).__getattr__(attr)



class CopyProcessor(ImageProcessor):

    def __init__(self):
        super(CopyProcessor,self).__init__()

    def apply(self,data):
        return data

import PyOCL

class BlurProcessor(ImageProcessor):

    def __init__(self,size = 7):
        super(BlurProcessor,self).__init__(size = size)

    def apply(self,data):
        x = np.linspace(-1.,1.,self.size)
        h = np.exp(-4.*x**2)
        h *= 1./sum(h)
        return imgtools.convolve_sep3(data, h, h, h)



class FFTProcessor(ImageProcessor):

    def apply(self,data):
        return np.fft.fftshift(abs(imgtools.ocl_fft(data)))





if __name__ == '__main__':
    from numpy import *


    p = FFTProcessor()


    Z,Y,X = imgtools.ZYX(128)

    u = 100*exp(-100*(X**2+Y**2+Z**2))

    u += 10.*np.random.normal(0,1.,u.shape)


    y = p.apply(u)
