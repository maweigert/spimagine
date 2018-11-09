"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division
import numpy as np
from spimagine.models.keyframe_model import KeyFrameList, KeyFrame, TransformData
from spimagine import Quaternion

import matplotlib.pyplot as plt

if __name__ == '__main__':

    elast = 2


    k = KeyFrameList()


    k.addItem(KeyFrame(0, TransformData(zoom = 1.),interp_elasticity=elast))
    k.addItem(KeyFrame(.5, TransformData(zoom=.2, quatRot=Quaternion(.71, .71, 0, 0), bounds=[0] * 6),interp_elasticity=elast))
    k.addItem(KeyFrame(1, TransformData(zoom=1., quatRot=Quaternion(.71, .71, 0, 0), bounds=[0] * 6),interp_elasticity=elast))


    ts = np.linspace(0,1,100)
    trans = tuple(k.getTransform(t) for t in ts)

    zooms = np.array([tran.zoom for tran in trans])

    plt.figure(num=1)
    plt.clf()
    plt.plot(ts, zooms)
    plt.show()
