"""


mweigert@mpi-cbg.de

"""
from PyQt4 import QtGui, QtCore
import sys
from spimagine import DataModel, DemoData
from spimagine.gui.glwidget import GLWidget


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800,800))

    d = DataModel(DemoData())

    win.setModel(d)

    win.show()

    win.raise_()

    sys.exit(app.exec_())
