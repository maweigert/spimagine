#!/usr/bin/env python

"""
main gui program that creates the frame with the rendering controls.

Drag and Drop into rendering canvas is supported for
- Tiff files
- BScope Spim Data Folders (Myers Lab)

and might be extended by writing a corressponding DataModel (defined in data_model.py)
for it


author: Martin Weigert
email: mweigert@mpi-cbg.de
"""


import sys
import os


from PyQt4 import QtGui

from spimagine.gui_mainwidget import MainWidget
from spimagine.data_model import DemoData, DataModel


from numpy import *
from scipy.integrate import *


def main():
    

    app = QtGui.QApplication(sys.argv)

    if sys.platform.startswith("win"):
    	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("CleanLooks"))

    
    win = MainWidget()

    if len(sys.argv)>1:
        win.setModel(DataModel.fromPath(sys.argv[1]))
    else:
        win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    
