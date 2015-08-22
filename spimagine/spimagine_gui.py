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

import argparse


from spimagine.gui_mainwidget import MainWidget
from spimagine.data_model import DemoData, DataModel


def main():

    parser = argparse.ArgumentParser(description='spimagine rendering application ')
    parser.add_argument('fname', metavar='fname', type=str, nargs='?',
                        help='the file/folder to open (e.g. tif, folder of tif) ', default = None)
    parser.add_argument('-p', dest='prefetch', type = int,
                    default=0,
                        help='prefetch size (should not be negative, e.g. -p 2)')

    args = parser.parse_args()
    print args.fname, args.prefetch
    
    app = QtGui.QApplication(sys.argv)

    if sys.platform.startswith("win"):
    	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("CleanLooks"))

    
    win = MainWidget()

    if args.fname:
        win.setModel(DataModel.fromPath(args.fname))
    else:
        win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    
