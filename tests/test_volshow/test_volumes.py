"""


mweigert@mpi-cbg.de

"""

import numpy as np
from PyQt4 import QtCore


import logging
from spimagine import volshow, volfig, logger

# logger.setLevel(logging.DEBUG)

import time

def test_data(data):
    w = volfig(1)
    QtCore.QTimer.singleShot(1000,w.closeMe)
    volshow(data,  blocking=True)




def test_volumes():
    test_data(10*np.ones((100,)*3))
    test_data(np.random.uniform(-1,1,(100,)*3))
    test_data(np.linspace(0,100,60*70*80).reshape((60,70,80)).astype(np.float32))



if __name__ == '__main__':
    test_volumes()

