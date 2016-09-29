__author__ = 'mweigert'

import sys

from PyQt4 import QtGui, QtCore

from spimagine import MainWidget, DemoData, DataModel, qt_exec
from spimagine.gui.glwidget import GLWidget

from spimagine import logger
#logger.setLevel(logger.DEBUG)


def test_widget():
    app = QtGui.QApplication(sys.argv)

    win = MainWidget()
    #win = GLWidget()

    win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    QtCore.QTimer.singleShot(100,win.closeMe)
    #QtCore.QTimer.singleShot(100,win.close)


    app.exec_()



if __name__ == '__main__':
    test_widget()