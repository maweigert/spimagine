"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import numpy as np
from stardist.plot import random_label_cmap
from tifffile import imread
from spimagine import volshow
from skimage.segmentation import relabel_sequential
from time import sleep
if __name__ == '__main__':

    d,_,_ = relabel_sequential(imread("worm_stack.tif"))

    cmap = random_label_cmap(d.max() + 1)
    cols = cmap(np.arange(d.max() + 1))[:,:3]

    w = volshow(d, autoscale=False)
    w.transform.setZoom(1.5)
    w.glWidget._set_colormap_array(cols)
    w.glWidget.set_interpolation(interpolate=False)
    w.glWidget.refresh()


