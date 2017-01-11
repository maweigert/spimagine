"""


mweigert@mpi-cbg.de

"""
from __future__ import absolute_import
import numpy as np
from spimagine import volfig, Mesh, qt_exec
from spimagine.utils import alpha_shape


def test_2d():
    import matplotlib.pyplot as plt

    plt.ion()
    np.random.seed(0)

    N = 500
    phi = np.random.uniform(0, 2*np.pi, N)

    points = np.stack([np.cos(phi), np.sin(phi)*np.cos(phi)]).T
    #points += .1*np.random.uniform(-1, 1, (N, 2))
    #points = np.concatenate([points,.9*points])

    points, normals, indices = alpha_shape(points, .1)


    plt.clf()



    _x = points[indices].reshape(len(indices)*2,2)
    _n = normals[indices].reshape(len(indices)*2,2)


    plt.quiver(_x[:,0],_x[:,1],_n[:,0],_n[:,1], color = (.5,)*3)
    plt.plot(points[:,0],points[:,1],".")
    for edge in indices:
        plt.plot(points[edge, 0], points[edge, 1], "k", lw=2)

    plt.axis("equal")


    return points, normals, indices



def test_3d():
    N = 1000

    # generate a concave shape
    phi = np.random.uniform(0, 2*np.pi, N)
    theta = np.arccos(np.random.uniform(-1,1, N))

    points = np.stack([np.cos(phi)*np.sin(theta)*np.cos(theta), np.sin(phi)*np.sin(theta)*np.cos(theta), np.cos(theta)]).T
    #points += .1*np.random.uniform(-1, 1, (N,3))
    #points = np.concatenate([points,.9*points])

    #get the alpha shape indices and normals (set alpha = -1 for the convex hull)
    points, normals, indices  = alpha_shape(points, alpha = .2)

    m = Mesh(vertices = points.flatten(),
             normals = normals.flatten(),
             indices = indices.flatten(),
             facecolor = (1.,1.,.3))

    w = volfig(1)

    w.glWidget.add_mesh(m)
    w.transform.setRotation(0.4,0,1,0)
    w.show()
    # add this when run from command line
    from PyQt5 import QtCore
    QtCore.QTimer.singleShot(1000,w.closeMe)
    qt_exec()

    return points, normals, indices



if __name__ == '__main__':



    #points, normals, indices = test_2d()
    points, normals, indices = test_3d()
