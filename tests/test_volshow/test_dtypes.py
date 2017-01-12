"""


mweigert@mpi-cbg.de

"""
from __future__ import absolute_import, print_function

import numpy as np
from PyQt5 import QtCore
import logging
from spimagine import volshow, volfig, logger, qt_exec, NumpyData, DataModel

def single_data(data):
    w = volshow(data)
    QtCore.QTimer.singleShot(1000,w.closeMe)
    qt_exec()




def test_volumes():
    d = np.random.uniform(0,100,(100,)*3)

    for dtype in (np.float32, np.int8, np.uint16, np.int32):
        print("testing: %s" %dtype)
        single_data(d.astype(dtype))



if __name__ == '__main__':
    data = np.linspace(0,255,100**3).reshape((100,)*3).transpose((1,2,0))


    m = DataModel(NumpyData(data.astype(np.uint8)))
    w = volshow(m)

    QtCore.QTimer.singleShot(1000, w.closeMe)
    qt_exec()


