"""


mweigert@mpi-cbg.de

"""
from PyQt4 import QtGui, QtCore
import sys
from spimagine import DataModel, DemoData, NumpyData
from spimagine.gui.glwidget import GLWidget
import numpy as np

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800,800))


    x = np.linspace(-1,1,128)
    Z,Y,X = np.meshgrid(x,x,x,indexing="ij")
    u = np.array([X*(X+Y>0),Z*(Z>0)])
    # u = X
    d = DataModel(NumpyData(u))




    win.setModel(d)

    win.show()

    win.raise_()

    sys.exit(app.exec_())
