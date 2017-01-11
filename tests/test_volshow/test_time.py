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

# logger.setLevel(logging.DEBUG)


def _with_widget(data):
    app = QtWidgets.QApplication(sys.argv)

    win = MainWidget()
    #win = GLWidget()

    t = time.time()
    win.setModel(DataModel(NumpyData(data)))
    print("time to set model in mainwindow: ", time.time()-t)
    win.show()
    win.raise_()

    QtCore.QTimer.singleShot(1,win.closeMe)


def _with_volshow(data, **kwargs):
    app = QtWidgets.QApplication(sys.argv)
    t = time.time()
    w = volshow(data, **kwargs)
    print("time to volshow: ", time.time() - t)

    QtCore.QTimer.singleShot(1, w.closeMe)
    print(w.glWidget.renderer.dataImg.dtype)
    app.exec_()




if __name__ == '__main__':
    d = np.zeros((700,) * 3, np.uint8)


    _with_widget(d)
    time.sleep(1)

    _with_volshow(d, autoscale = False)


