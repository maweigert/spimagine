"""


mweigert@mpi-cbg.de

"""
from PyQt4 import QtGui, QtCore
import sys
from spimagine import DataModel, DemoData, NumpyData
from spimagine.gui.glwidget import GLWidget
from spimagine.gui.mainwidget import MainWidget

import numpy as np

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWidget(size=QtCore.QSize(800,800))


    x = np.linspace(-1,1,100)
    Z,Y,X = np.meshgrid(x,x,x,indexing="ij")
    u1 = np.exp(-10*((Z-.3)**2+Y**2+(X-.3)**2))
    u2 = np.exp(-10*((Z+.3)**2+Y**2+(X+.3)**2))
    u3 = np.exp(-10*((Z+.0)**2+Y**2+(X+.0)**2))

    u = np.array([u1,u2,u3])
    # u = X
    d = DataModel(NumpyData(u))

    win.setModel(d)

    #win.glWidget.transfers[0].set_cmap((1.,0,0))
    # win.transfers[1].set_cmap((0,1,0))
    # win.transfers[2].set_cmap((0,0,1))
    win.show()

    win.raise_()

    sys.exit(app.exec_())
