"""


mweigert@mpi-cbg.de

"""

import numpy as np
from PyQt4 import QtCore


import logging
from spimagine import volshow, volfig, logger, qt_exec

# logger.setLevel(logging.DEBUG)

import time

def single_data(data, t_close_ms= 1000, **kwargs):
    w = volshow(data,**kwargs)
    QtCore.QTimer.singleShot(t_close_ms,w.closeMe)
    print w.glWidget.renderer.dataImg.dtype
    qt_exec()



def test_volumes():
    single_data(10*np.ones((100,)*3))
    single_data(np.random.uniform(-1,1,(100,)*3))
    single_data(np.linspace(0,100,60*70*80).reshape((60,70,80)).astype(np.float32))

    single_data(np.linspace(0,100,60*70*80).reshape((60,70,80)).astype(np.uint8))
    single_data(np.linspace(0,100,60*70*80).reshape((60,70,80)).astype(np.uint16))



if __name__ == '__main__':
    single_data(np.random.randint(0,100,(100,)*3).astype(np.uint8),
                autoscale = False,
                t_close_ms = 100000000)

