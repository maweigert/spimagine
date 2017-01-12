"""


mweigert@mpi-cbg.de

"""

from __future__ import absolute_import
import numpy as np
from PyQt5 import QtCore
import logging
from spimagine import volshow, volfig, logger, qt_exec, SphericalMesh
import time
from six.moves import zip


def test_mesh():
    np.random.seed(0)

    N = 300
    ps = np.random.uniform(-1, 1, (N, 3))
    cols = np.random.uniform(.0, 1., (N, 3))

    rs = np.random.uniform(.05, .1, N)

    phi = np.random.uniform(0, 2.*np.pi, N)
    t = np.arccos(np.random.uniform(-1, 1, N))
    ps = np.stack([np.cos(phi)*np.sin(t), np.sin(phi)*np.sin(t), np.cos(t)]).T

    w = volfig()

    for p, r, col in zip(ps, rs, cols):
        n = 1.*p
        # n[1] *= -1.
        phi = np.arctan2(n[1], n[0])
        theta = np.arccos(n[2]/np.sqrt(np.sum(n**2)))
        m = SphericalMesh(r=r, pos=p, facecolor=col, light=(-1, -1, 1))
        w.glWidget.add_mesh(m)

    QtCore.QTimer.singleShot(2000, w.closeMe)
    qt_exec()


if __name__=='__main__':
    test_mesh()
