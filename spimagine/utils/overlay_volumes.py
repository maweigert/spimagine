"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import numpy as np
from spimagine.models.data_model import GenericData

class OverlayData(GenericData):
    """create a data object that overlays to 3d arrays 
    along an axis and displays a portion of each for each timepoint
     
     e.g. data = OverlayData(x,y)
     
     then data[0] = x
     data[len(x)//2] = half x, half y 
     data[len(x)-1] = y
    """

    def __init__(self, x, y, axis = 0):
        super(OverlayData, self).__init__()
        if x.shape != y.shape:
            raise ValueError("shapes of the two arrays have to be equal!")

        self.out = x.copy()
        self.x = x
        self.y = y
        self._last_index = 0
        self.axis = axis

    def _make_slice(self, i,j):
        slices = [slice(None,None),]*self.out.ndim
        slices[self.axis] = slice(i,j)
        return tuple(slices)




    def __getitem__(self, i):

        if i > self._last_index:
            ss = self._make_slice(self._last_index,i)
            self.out[ss] = self.y[ss]
            self._last_index = i
        elif i < self._last_index:
            ss = self._make_slice(i,self._last_index)
            self.out[ss] = self.x[ss]
            self._last_index = i

        return self.out

    def size(self):
        d = list((self.out.shape[self.axis]+1,) + self.out.shape)
        return tuple(d)