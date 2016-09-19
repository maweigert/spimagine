__author__ = 'mweigert'

import sys
import numpy as np
from PyQt4 import QtGui, QtCore
from spimagine.gui.glwidget import GLWidget
from spimagine import EllipsoidMesh, SphericalMesh, Mesh


def test_widget():
    app = QtGui.QApplication(sys.argv)

    np.random.seed(0)
    win = GLWidget()
    win.resize(800, 800)

    N = 200
    ps = np.random.uniform(-1, 1, (N, 3))
    cols = np.random.uniform(.0, 1., (N, 3))

    r = .2/(1.*N**(1./3))

    verts = SphericalMesh(r=r, pos=(0,0,0)).vertices
    norms = SphericalMesh(r=r, pos=(0,0,0)).normals

    for p, col in zip(ps, cols):
        m = Mesh(vertices = verts+p, normals=norms+0, facecolor = col, light = (-1,-1,-1))
        #m = Mesh(vertices = verts+p, normals=norms+0, facecolor = col, light = None)

        win.add_mesh(m)



    win.show()
    win.raise_()
    # QtCore.QTimer.singleShot(100,win.close)
    app.exec_()

    return win


if __name__=='__main__':
    win = test_widget()
