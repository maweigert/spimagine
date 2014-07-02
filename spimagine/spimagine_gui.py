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
from PyQt4 import QtGui

from spimagine.gui_mainwindow import MainWindow






def main():

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
        
    win.raise_()

    sys.exit(app.exec_())



if __name__== '__main__':
    main()
