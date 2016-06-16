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


from PyQt4 import QtGui, QtCore

import argparse

import logging
logger = logging.getLogger(__name__)

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception as e:
        logger.debug("did not find MEIPASS: %s "%e)


        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


    
def main():

    parser = argparse.ArgumentParser(description='spimagine rendering application ')
    parser.add_argument('fname',
                        type=str,
                        nargs='*',
                        help='the files/folder to open (e.g. tif, folder of tif) ',
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

        
    if args.D:
        logger = logging.getLogger("spimagine")
        logger.setLevel(logging.DEBUG)

    app = QtGui.QApplication(sys.argv)


    #splash screen
    # print 'FIIIIIIIIIIII'
    # print absPath('../gui/images/splash.png')
    # print os.listdir(absPath("."))
    # print sys._MEIPASS

    pixmap = QtGui.QPixmap(absPath('../gui/images/splash.png'))
    splash = QtGui.QSplashScreen(pixmap, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(pixmap.mask())
    splash.show()
    app.processEvents()


    from spimagine.gui.mainwidget import MainWidget
    from spimagine.models.data_model import DemoData, DataModel
        


    
    app.setWindowIcon(QtGui.QIcon(absPath('../gui/images/spimagine.png')))

    if sys.platform.startswith("win"):
    	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("CleanLooks"))


    win = MainWidget()
    if args.fname:
        if len(args.fname)==1:
            win.setModel(DataModel.fromPath(args.fname[0]))
        else:
            win.setModel(DataModel.fromPath(args.fname))
    else:
        win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    splash.finish(win)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    
