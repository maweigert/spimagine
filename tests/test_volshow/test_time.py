"""


mweigert@mpi-cbg.de

"""

from __future__ import absolute_import, print_function
import numpy as np
import sys
from PyQt5 import QtCore, QtWidgets

import time
import logging
from spimagine import volshow, volfig, logger, qt_exec
from spimagine import MainWidget, DataModel, NumpyData
from spimagine.gui.glwidget import GLWidget

if len(sys.argv)>1 and sys.argv[1]=="-d":
    logger.setLevel(logging.DEBUG)


def _with_mainwidget( data):
    app = QtWidgets.QApplication(sys.argv)

    win = MainWidget()

    d = DataModel(NumpyData(data))
    t = time.time()
    win.setModel(d)
    print("time to set model in mainwidget: ", time.time()-t)
    win.show()
    win.raise_()
    app.win = win
    QtCore.QTimer.singleShot(100, app.quit)
    app.exec_()

def _with_glwidget(data):
    app = QtWidgets.QApplication(sys.argv)

    win = GLWidget()

    d = DataModel(NumpyData(data))
    t = time.time()
    win.setModel(d)
    print("time to set model in glwidget: ", time.time()-t)
    win.show()
    win.raise_()
    app.win = win
    QtCore.QTimer.singleShot(200, app.quit)
    app.exec_()

def _with_volshow(data, **kwargs):
    app = QtWidgets.QApplication(sys.argv)


    t = time.time()
    w = volshow(data, **kwargs)
    print("time to volshow: ", time.time() - t)



    QtCore.QTimer.singleShot(100, app.quit)
    app.exec_()


def data_model(data):
    app = QtWidgets.QApplication(sys.argv)
    t = time.time()
    app.d = DataModel(NumpyData(data))
    print("time to datamodel: ", time.time() - t)
    QtCore.QTimer.singleShot(100, app.quit)
    app.exec_()

if __name__ == '__main__':
    d = np.zeros((700,) * 3, np.uint8)

    print("rendering %s MB"%int(d.nbytes/1.e6))


    _with_glwidget(d)

    # _with_mainwidget(d)

    #
    # data_model(d)

