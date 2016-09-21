__author__ = 'mweigert'

import sys
import numpy as np
from PyQt4 import QtGui, QtCore
from spimagine.gui.glwidget import GLWidget
from spimagine.gui.mainwidget import MainWidget
from spimagine import EllipsoidMesh, SphericalMesh, EllipsoidMesh, Mesh, DemoData, DataModel
from spimagine.utils.transform_matrices import *

def test_widget():
    app = QtGui.QApplication(sys.argv)

    np.random.seed(0)
    win = MainWidget()
    win.resize(800, 800)

    # win.setModel(DataModel(DemoData()))
    N = 200
    ps = np.random.uniform(-1, 1, (N, 3))
    cols = np.random.uniform(.0, 1., (N, 3))
    r0 = .5/(1.*N**(1./3))
    rs = r0*np.random.uniform(.1, 2., (N, 3))

    phi = np.random.uniform(0, 2.*np.pi, N)
    t = np.arccos(np.random.uniform(-1, 1, N))
    ps = np.stack([np.cos(phi)*np.sin(t), np.sin(phi)*np.sin(t), np.cos(t)]).T

    # mesh0 = SphericalMesh(r=r0, pos=(0, 0, 0))
    #

    # verts = mesh0.vertices
    # norms = mesh0.normals

    # m = EllipsoidMesh(rs=(.3,.3,.8), pos=(0,0,0), facecolor = (.3,.6,.2), light = (-1,-1,1))

    # n = np.array([-.2,-.2,-1])
    # phi = np.arctan2(n[1],n[0])
    # theta = np.arccos(n[2]/np.sqrt(np.sum(n**2)))
    # print phi, theta
    # m.transform(mat4_rotation_euler(phi,theta))


    # win.glWidget.add_mesh(mesh0)
    #

    for p, r, col in zip(ps, rs, cols):
        col = (1., .5, .2)
        n = 1.*p
        #n[1] *= -1.
        phi = np.arctan2(n[1],n[0])
        theta = np.arccos(n[2]/np.sqrt(np.sum(n**2)))

        m = EllipsoidMesh(rs=r, pos=p, facecolor = col, light = (-1,-1,1), transform_mat=mat4_rotation_euler(phi,theta))

        # print phi, theta
        # m.transform(mat4_rotation_euler(phi,theta))

        win.glWidget.add_mesh(m)

    win.show()
    win.raise_()
    # QtCore.QTimer.singleShot(100,win.close)
    app.exec_()

    return win


if __name__=='__main__':
    win = test_widget()
