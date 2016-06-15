__author__ = 'mweigert'

import sys

from PyQt4 import QtGui, QtCore

from spimagine.gui.mainwidget import MainWidget
from spimagine.models.data_model import DemoData, DataModel


def f():
    print "hallao"
def test_widget():
    app = QtGui.QApplication(sys.argv)


    win = MainWidget()

    win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    QtCore.QTimer.singleShot(1000,win.closeMe)

    app.exec_()



if __name__ == '__main__':
    test_widget()