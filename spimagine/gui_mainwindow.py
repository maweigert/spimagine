#!/usr/bin/env python

"""
the main frame used for in spimagine_gui

the data model is member of the frame

author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import sys
import os
import numpy as np


from PyQt4 import QtCore
from PyQt4 import QtGui

from gui_mainwidget import MainWidget

class MainWindow(QtGui.QMainWindow):

    def __init__(self, dataContainer = None):
        super(MainWindow,self).__init__()

        self.resize(800, 700)
        self.setWindowTitle('SpImagine')

        self.initActions()
        self.initMenus()

        self.mainWidget = MainWidget(self)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.mainWidget,stretch =1)


        widget = QtGui.QWidget()
        widget.setLayout(hbox)
        self.setCentralWidget(widget)
        self.setStyleSheet("background-color:black;")

    def initActions(self):
        self.exitAction = QtGui.QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)


    def initMenus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.exitAction)
        # this has to be repeated in MAC OSX for some magic reason
        fileMenu = menuBar.addMenu('&File')



    def mouseDoubleClickEvent(self,event):
        super(MainWindow,self).mouseDoubleClickEvent(event)
        if self.isFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

        # there's a bug in Qt that disables drop after fullscreen, so reset it...
        self.setAcceptDrops(True)

        self.isFullScreen = not self.isFullScreen


    def close(self):
        self.mainWidget.close()
        super(MainWindow,self).close()


    def setModel(self,dataModel):
        self.mainWidget.setModel(dataModel)



        
if __name__ == '__main__':
    import argparse
    from data_model import DataModel, NumpyData

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()

    win.setModel(DataModel(NumpyData(np.linspace(0,5000.,50**4).reshape((50,)*4))))

    win.show()
    win.raise_()

    sys.exit(app.exec_())
