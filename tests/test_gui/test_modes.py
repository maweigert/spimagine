"""


mweigert@mpi-cbg.de

"""

from __future__ import absolute_import, print_function

import sys

from PyQt5 import QtGui, QtCore, QtWidgets
from time import time
from spimagine import MainWidget, DemoData, DataModel
from gputools.utils import remove_cache_dir

def test_widget(blocking = False):
    app = QtWidgets.QApplication(sys.argv)

    win = MainWidget()

    t = time()
    win.setModel(DataModel(DemoData()))
    print("time to set model: ", time()-t)
    win.show()
    win.transform.setRenderMode(2)

    if not blocking:
        QtCore.QTimer.singleShot(100,win.closeMe)



    app.exec_()



if __name__ == '__main__':

    remove_cache_dir()

    test_widget(blocking = True)