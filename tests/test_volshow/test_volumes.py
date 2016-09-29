"""


mweigert@mpi-cbg.de

"""

import numpy as np
from PyQt4 import QtCore


import logging
from spimagine import volshow, volfig, logger, qt_exec

# logger.setLevel(logging.DEBUG)

import time

def single_data(data):
    w = volshow(data)
    QtCore.QTimer.singleShot(1000,w.closeMe)
    qt_exec()




def test_volumes():
    single_data(10*np.ones((100,)*3))
    single_data(np.random.uniform(-1,1,(100,)*3))
    single_data(np.linspace(0,100,60*70*80).reshape((60,70,80)).astype(np.float32))



if __name__ == '__main__':
    test_volumes()

