"""


mweigert@mpi-cbg.de

"""
import numpy as np
from spimagine import volfig, Mesh, qt_exec
from spimagine.utils import alpha_shape


if __name__ == '__main__':

    N = 5000

    # generate a concave shape
    phi = np.random.uniform(0, 2*np.pi, N)
    theta = np.arccos(np.random.uniform(-1,1, N))

    points = np.stack([np.cos(phi)*np.sin(theta)*np.cos(theta), np.sin(phi)*np.sin(theta)*np.cos(theta), np.cos(theta)]).T
    points += .1*np.random.uniform(-1, 1, (N,3))


    #get the alpha shape indices and normals (set alpha = -1 for the convex hull)
    indices, normals = alpha_shape(points, alpha = .1)

    m = Mesh(vertices = points.flatten(),
             normals = normals.flatten(),
             indices = indices.flatten(),
             facecolor = (1.,1.,.3))

    w = volfig(1)

    w.glWidget.add_mesh(m)

    qt_exec()

