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

from quaternion import Quaternion
from gui_glwidget import GLWidget
from keyframe_view import *
from gui_settings import SettingsPanel
from data_model import DataLoadModel, DemoData, SpimData


# the default number of data timeslices to prefetch
N_PREFETCH = 10



def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(800, 700)
        self.isFullScreen = False
        self.setWindowTitle('SpImagine')

        self.initActions()
        self.initMenus()

        self.glWidget = GLWidget(self,N_PREFETCH = N_PREFETCH)

        self.startButton = QtGui.QPushButton("",self)
        self.startButton.setStyleSheet("background-color: black")
        self.startButton.setIcon(QtGui.QIcon(absPath("images/icon_start.png")))
        self.startButton.setIconSize(QtCore.QSize(24,24))
        self.startButton.clicked.connect(self.startPlay)
        self.startButton.setMaximumWidth(24)
        self.startButton.setMaximumHeight(24)




        buttonStyleStr = """
        QPushButton {
        background: black;
        : none;
        background-position: top center;
        background-origin: content;
        padding: 3px;
        border-style: solid;
        border-width: 3px;
        border-color: red (120,0,0);
        border-radius: 40px;
        }

        QPushButton:pressed {
        background-color: rgb(255,0,0);
        background-image: url(:/Images/alarmButtonReflection.png) ;
        background-repeat: none;
        background-position: top center;
        background-origin: content;
        }       """


        self.screenshotButton = QtGui.QPushButton("",self)
        self.screenshotButton.setStyleSheet("background-color: black")
        self.screenshotButton.setIcon(QtGui.QIcon(absPath("images/icon_camera.png")))
        self.screenshotButton.setIconSize(QtCore.QSize(24,24))
        self.screenshotButton.clicked.connect(self.screenShot)
        self.screenshotButton.setMaximumWidth(24)
        self.screenshotButton.setMaximumHeight(24)

        checkBoxStyleStr = """
        QCheckBox::indicator:checked {
        background:black;
        background-image: url(:%s);


        }
        QCheckBox::indicator:unchecked {
        background:black;
        border-image: url(:%s);}
        """

        # self.checkProj  = QtGui.QCheckBox()
        # self.checkProj.setStyleSheet(
        #     checkBoxStyleStr%(absPath("images/rays_persp.png"),absPath("images/rays_ortho.png")))

        # self.checkBox = QtGui.QCheckBox()
        # self.checkBox.setStyleSheet(
        #     checkBoxStyleStr%(absPath("images/wire_cube.png"),absPath("images/wire_cube_inactive.png")))

        self.checkSettings = QtGui.QCheckBox()
        self.checkSettings.setStyleSheet(
            checkBoxStyleStr%(absPath("images/settings.png"),absPath("images/settings_inactive.png")))


        self.checkKey = QtGui.QCheckBox()
        self.checkKey.setStyleSheet(
            checkBoxStyleStr%(absPath("images/video.png"),absPath("images/video_inactive.png")))


        self.sliderTime = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sliderTime.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.sliderTime.setTickInterval(1)
        self.sliderTime.setTracking(False)


        self.spinTime = QtGui.QSpinBox()
        self.spinTime.setStyleSheet("color:white;")
        self.spinTime.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.spinTime.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.spinTime.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)


        self.sliderTime.valueChanged.connect(self.spinTime.setValue)
        self.spinTime.valueChanged.connect(self.sliderTime.setValue)


        self.scaleSlider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.scaleSlider.setRange(1, 250)

        self.gammaSlider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.gammaSlider.setRange(0, 200)
        # self.gammaSlider.setValue(50)

        self.scaleSlider.valueChanged.connect(
            lambda x: self.glWidget.transform.setScale(0,x**2))
        self.glWidget.transform._maxChanged.connect(
            lambda x: self.scaleSlider.setValue(int(np.sqrt(x))))

        self.gammaSlider.valueChanged.connect(
            lambda x: self.glWidget.transform.setGamma(1+(x-100.)/200.))
        self.glWidget.transform._gammaChanged.connect(
            lambda x: self.gammaSlider.setValue(200*(x-1.)+100))


        self.keyframes = KeyFrameList()
        self.keyPanel = KeyFramePanel()
        self.keyPanel.hide()




        self.settingsView = SettingsPanel()
        self.settingsView.hide()

        self.setStyleSheet("background-color:black;")

        hbox0 = QtGui.QHBoxLayout()
        hbox0.addWidget(self.glWidget,stretch =1)
        hbox0.addWidget(self.scaleSlider)
        hbox0.addWidget(self.gammaSlider)
        hbox0.addWidget(self.settingsView)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.startButton)
        hbox.addWidget(self.sliderTime)
        hbox.addWidget(self.spinTime)
        # hbox.addWidget(self.checkProj)
        # hbox.addWidget(self.checkBox)
        hbox.addWidget(self.checkKey)
        hbox.addWidget(self.screenshotButton)


        hbox.addWidget(self.checkSettings)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox0)

        vbox.addLayout(hbox)
        vbox.addWidget(self.keyPanel)

        widget = QtGui.QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)



        self.playTimer = QtCore.QTimer(self)
        self.playTimer.setInterval(100)
        self.playTimer.timeout.connect(self.onPlayTimer)
        self.playDir = 1

        self.settingsView.checkBox.stateChanged.connect(self.glWidget.transform.setBox)
        self.glWidget.transform._boxChanged.connect(self.settingsView.checkBox.setChecked)


        self.settingsView.checkProj.stateChanged.connect(self.glWidget.transform.setPerspective)
        self.glWidget.transform._perspectiveChanged.connect(self.settingsView.checkProj.setChecked)

        self.checkKey.stateChanged.connect(self.keyPanel.setVisible)
        self.checkSettings.stateChanged.connect(self.settingsView.setVisible)


        self.dataModel = DataLoadModel()



        self.settingsView._stackUnitsChanged.connect(self.glWidget.transform.setStackUnits)
        self.glWidget.transform._stackUnitsChanged.connect(self.settingsView.setStackUnits)


        self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
        self.dataModel._dataPosChanged.connect(self.sliderTime.setValue)

        self.sliderTime.valueChanged.connect(self.dataModel.setPos)

        self.dataModel.load(dataContainer=DemoData(100),
                                       prefetchSize = N_PREFETCH)
        self.glWidget.setModel(self.dataModel)


        self.keyPanel.keyView.setDataTransformModel(self.dataModel,self.glWidget.transform)
        self.keyPanel.keyView.setModel(self.keyframes)


    def initUI(self):
        pass

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


    def dataSourceChanged(self):
        self.sliderTime.setRange(0,self.dataModel.sizeT()-1)
        self.spinTime.setRange(0,self.dataModel.sizeT()-1)
        print "XXXX",self.dataModel.stackSize()
        self.settingsView.dimensionLabel.setText("Dim: %ix%ix%i"%self.dataModel.stackSize()[:0:-1])


    def startPlay(self,event):
        if self.playTimer.isActive():
            self.playTimer.stop()
            self.startButton.setIcon(QtGui.QIcon(absPath("images/icon_start.png")))

        else:
            self.playTimer.start()
            self.startButton.setIcon(QtGui.QIcon(absPath("images/icon_pause.png")))


    def screenShot(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save screenshot as',
                                                     '.', selectedFilter='*.png')

        if fileName:
            self.glWidget.saveFrame(fileName)


    def onPlayTimer(self):

        if self.dataModel.pos == self.dataModel.sizeT()-1:
            self.playDir = -1
        if self.dataModel.pos == 0:
            self.playDir = 1

        print self.dataModel.pos, self.playDir
        newpos = (self.dataModel.pos+self.playDir)%self.dataModel.sizeT()
        self.dataModel.setPos(newpos)
        # self.glWidget.transform.quatRot *= Quaternion(np.cos(.01),0,np.sin(0.01),0)

    def close(self):
        isAppRunning = False
        QtGui.qApp.quit()

    def mouseDoubleClickEvent(self,event):
        super(MainWindow,self).mouseDoubleClickEvent(event)
        if self.isFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

        # there's a bug in Qt that disables drop after fullscreen, so reset it...
        self.setAcceptDrops(True)

        self.isFullScreen = not self.isFullScreen


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
