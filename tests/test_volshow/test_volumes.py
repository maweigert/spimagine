"""


mweigert@mpi-cbg.de

"""

from __future__ import absolute_import
from __future__ import print_function
import numpy as np
from PyQt5 import QtCore


import logging
from spimagine import volshow, volfig, logger, qt_exec

# logger.setLevel(logging.DEBUG)

import time

def single_data(data, t_close_ms= 1000, **kwargs):
    w = volshow(data,**kwargs)
    QtCore.QTimer.singleShot(t_close_ms,w.closeMe)
    print(w.glWidget.renderer.dataImg.dtype)
    qt_exec()



def test_volumes():
    single_data(10*np.ones((100,)*3))
    single_data(np.random.uniform(-1,1,(100,)*3))
    d = np.linspace(0,100,60*70*80).reshape((60,70,80)).T
    single_data(d.astype(np.float32))
    single_data(d.astype(np.uint8))
    single_data(d.astype(np.uint16))




if __name__ == '__main__':

    single_data(np.zeros((100,) * 3, np.float32),
            autoscale=False,
            t_close_ms=10000)


