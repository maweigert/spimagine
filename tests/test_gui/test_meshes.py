__author__ = 'mweigert'

import sys
import numpy as np
from PyQt4 import QtGui, QtCore
from spimagine.gui.glwidget import GLWidget
from spimagine import EllipsoidMesh, SphericalMesh


def test_widget():
    app = QtGui.QApplication(sys.argv)

    win = GLWidget()
    win.resize(800, 800)

    N = 5
    ps = np.random.uniform(-1, 1, (N, 3))
    rs = np.random.uniform(.1, .3, N)
    cols = np.random.uniform(.0, 1., (N, 3))

    for p, r, col in zip(ps, rs, cols):
        win.add_mesh(SphericalMesh(r=r, pos=p, facecolor = col, light = None))

    win.show()
    win.raise_()
    # QtCore.QTimer.singleShot(100,win.close)
    app.exec_()

    return win


if __name__=='__main__':
    win = test_widget()
