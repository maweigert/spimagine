"""
Implements generic classes for processing of volumetric data
"""

from __future__ import absolute_import, print_function
import sys
import numpy as np
import gputools
from six.moves import zip



# try:
#     import imgtools
#     import lucy_richardson_gpu
# except:
#     print "could not import imgtools or lucy_richardson module"

class ImageProcessor(object):
    def __init__(self,name = "",**kwargs):
        self.name = name
        self.set_params(**kwargs)

    def set_params(self,**kwargs):
        self.kwargs = kwargs

    def apply(self, data):
        raise NotImplementedError()

    def __getattr__(self,attr):
        if attr in self.kwargs:
            return self.kwargs[attr]
        else:
            return super(ImageProcessor,self).__getattr__(attr)



class CopyProcessor(ImageProcessor):

    def __init__(self):
        super(CopyProcessor,self).__init__("copy")

    def apply(self,data):
        return data


class BlurProcessor(ImageProcessor):

    def __init__(self,sigma = 4.):
        super(BlurProcessor,self).__init__("blur",sigma = sigma)

    def apply(self,data):
        N  = 2*self.sigma+1
        x = np.arange(-N,N+1)
        h = np.exp(-x**2/2./self.sigma**2)
        h *= 1./sum(h)
        return gputools.convolve_sep3(data, h, h, h)


class BlurXYZProcessor(ImageProcessor):

    def __init__(self,sx=4.,sy=4.,sz=4.):
        super(BlurXYZProcessor,self).__init__("blur_xyz",sx=sx,sy=sy,sz=sz)

    def apply(self,data):
        sigs = (self.sx,self.sy,self.sz)
        Ns  = [2*s+1 for s in sigs]

        xs = [np.arange(-N,N+1) for N in Ns]
        hs = [np.exp(-x**2/2./s**2) for x,s in zip(xs,sigs)]
        hs = [1.*h/sum(h) for h in hs]
        return gputools.convolve_sep3(data, *hs)

class NoiseProcessor(ImageProcessor):
    def __init__(self,sigma = 10):
        super(NoiseProcessor,self).__init__("noise",sigma = sigma)

    def apply(self,data):
        return np.maximum(0,data+self.sigma*np.random.normal(0,1,data.shape))


class FFTProcessor(ImageProcessor):
    def __init__(self, log = False):
        super(FFTProcessor,self).__init__("fft", log = log)
        self.log = log

    def apply(self,data):
        dshape = data.shape
        
        res = gputools.pad_to_power2(data.astype(np.complex64), mode = "wrap")

        res = 1./np.sqrt(res.size)*np.fft.fftshift(abs(gputools.fft(res)))
        
        res = gputools.pad_to_shape(res,dshape)
        
        if self.log:
            return np.log2(0.001+res)
        else:
            return res


class LucyRichProcessor(ImageProcessor):

    def __init__(self,rad = 4., niter = 6):
        super(LucyRichProcessor,self).__init__("RL-Deconv",rad = rad, niter = niter)
        self.rad0 = rad
        self.niter0 = niter
        self.hshape = (1,)*3

    def reset_psf(self,dshape):
        # self.h = imgtools.blur_psf(dshape,self.rad)
        pass

    def apply(self,data):
        if self.hshape != data.shape or self.rad != self.rad0:
            self.reset_psf(data.shape)
            self.rad0 = self.rad

        return data
        # return lucy_richardson_gpu.lucy_richardson(data, self.h,self.niter)


class FuncProcessor(ImageProcessor):

    def __init__(self,func, name = "func processor", **kwargs):
        super(FuncProcessor,self).__init__(name,**kwargs)
        self.func = func

    def apply(self,data):
        return self.func(data,**self.kwargs)


    
if __name__ == '__main__':
    from numpy import *


    # p = LucyRichProcessor()

    # p2 = FFTProcessor()

    # print p.name

    # print p2.name


