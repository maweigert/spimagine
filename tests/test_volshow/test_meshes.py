"""


mweigert@mpi-cbg.de

"""

import numpy as np
from PyQt4 import QtCore


import logging
from spimagine import volshow, volfig, logger,qt_exec,  EllipsoidMesh

import time

def test_mesh():

    data = 10*np.ones((100,)*3)


    mesh = EllipsoidMesh(rs = (.3,.2,.6), pos = (0,0,0), facecolor = (1.,.3,.2))


    w = volshow(data)
    w.glWidget.add_mesh(mesh)

    qt_exec()



if __name__ == '__main__':
    test_mesh()

