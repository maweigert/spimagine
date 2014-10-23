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


# class MainWindow(QtGui.QMainWindow):

#     def __init__(self, dataContainer = None):
#         super(MainWindow,self).__init__()

#         self.resize(800, 700)
#         self.setWindowTitle('SpImagine')

#         self.initActions()
#         self.isCloseFlag = False
#         # self.initMenus()

#         self.mainWidget = MainWidget(self)

#         hbox = QtGui.QHBoxLayout()
#         hbox.addWidget(self.mainWidget,stretch =1)


#         widget = QtGui.QWidget()
#         widget.setLayout(hbox)
#         self.setCentralWidget(widget)
#         self.setStyleSheet("background-color:black;")


#     def initActions(self):
#         QtGui.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.closeMe)

#     def keyPressEvent(self, event):
#         if type(event) == QtGui.QKeyEvent:
#             if event.modifiers()== QtCore.Qt.ControlModifier and  event.key() == QtCore.Qt.Key_Q:
#                 return

#     # def initActions(self):
#     #     self.exitAction = QtGui.QAction('Quit', self)
#     #     self.exitAction.setShortcut('Ctrl+Q')
#     #     self.exitAction.setStatusTip('Exit application')
#     #     self.exitAction.triggered.connect(self.close)


#     # def initMenus(self):
#     #     menuBar = self.menuBar()
#     #     fileMenu = menuBar.addMenu('&File')
#     #     fileMenu.addAction(self.exitAction)
#     #     # this has to be repeated in MAC OSX for some magic reason
#     #     fileMenu = menuBar.addMenu('&File')



#     def mouseDoubleClickEvent(self,event):
#         super(MainWindow,self).mouseDoubleClickEvent(event)
#         if self.isFullScreen:
#             self.showNormal()
#         else:
#             self.showFullScreen()

#         # there's a bug in Qt that disables drop after fullscreen, so reset it...
#         self.setAcceptDrops(True)

#         self.isFullScreen = not self.isFullScreen


#     def setModel(self,dataModel):
#         self.mainWidget.setModel(dataModel)



#     def closeMe(self):
#         #little workaround as on MAC ctrl-q cannot be overwritten

#         self.isCloseFlag = True
#         self.close()

#     def closeEvent(self,event):
#         if not event.spontaneous() and not self.isCloseFlag:
#             event.ignore()
#         else:
#             event.accept()


def main():
    

    app = QtGui.QApplication(sys.argv)

    win = MainWidget()

    win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()    
