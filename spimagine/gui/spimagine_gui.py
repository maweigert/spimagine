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

import logging

    
def main():

    parser = argparse.ArgumentParser(description='spimagine rendering application ')
    parser.add_argument('fname',
                        type=str,
                        nargs='?',
                        help='the file/folder to open (e.g. tif, folder of tif) ',
                        default = None)
    
    parser.add_argument('-p',
                        dest='prefetch',
                        type = int,
                        default=0,
                        help='prefetch size (should not be negative, e.g. -p 2)')

    parser.add_argument('-D',
                        action='store_true',
                        help = "output DEBUG messages")

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)


    from spimagine.gui.gui_mainwidget import MainWidget
    from spimagine.models.data_model import DemoData, DataModel
        
        
    if args.D:
        logger = logging.getLogger("spimagine")
        logger.setLevel(logging.DEBUG)

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
