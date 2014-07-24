#!/usr/bin/env python

"""
the main frame used for in spimagine_gui

the data model is member of the frame

author: Martin Weigert
email: mweigert@mpi-cbg.de
"""


import logging
logger = logging.getLogger(__name__)


import os
import numpy as np
import sys

from PyQt4 import QtCore
from PyQt4 import QtGui

from quaternion import Quaternion
from gui_glwidget import GLWidget
from keyframe_view import KeyFramePanel
from gui_settings import SettingsPanel
from data_model import DataModel, DemoData, SpimData


# the default number of data timeslices to prefetch
N_PREFETCH = 10



def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


class MainWidget(QtGui.QWidget):

    def __init__(self, parent = None,dataContainer = None, N_PREFTECH = 0):
        super(QtGui.QWidget,self).__init__(parent)

        self.myparent = parent

        self.resize(800, 700)
        self.isFullScreen = False
        self.setWindowTitle('SpImagine')

        self.initActions()
        # self.initMenus()

        self.glWidget = GLWidget(self,N_PREFETCH = N_PREFETCH)

        self.fwdButton = QtGui.QPushButton("",self)
        self.fwdButton.setStyleSheet("background-color: black")


        self.fwdButton.setIcon(QtGui.QIcon(absPath("images/icon_forward.png")))
        self.fwdButton.setIconSize(QtCore.QSize(18,18))
        self.fwdButton.clicked.connect(self.forward)
        self.fwdButton.setMaximumWidth(18)
        self.fwdButton.setMaximumHeight(18)

        self.bwdButton = QtGui.QPushButton("",self)
        self.bwdButton.setStyleSheet("background-color: black")
        self.bwdButton.setIcon(QtGui.QIcon(absPath("images/icon_backward.png")))
        self.bwdButton.setIconSize(QtCore.QSize(18,18))
        self.bwdButton.clicked.connect(self.backward)
        self.bwdButton.setMaximumWidth(18)
        self.bwdButton.setMaximumHeight(18)

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
        border-image: url(%s);


        }
        QCheckBox::indicator:unchecked {
        background:black;
        border-image: url(%s);}
        """

        self.checkSettings = QtGui.QCheckBox()
        self.checkSettings.setStyleSheet(
            checkBoxStyleStr%(absPath("images/settings.png"),absPath("images/settings_inactive.png")))


        self.checkKey = QtGui.QCheckBox()
        self.checkKey.setStyleSheet(
            checkBoxStyleStr%(absPath("images/video.png"),absPath("images/video_inactive.png")))


        self.sliderTime = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sliderTime.setTickPosition(QtGui.QSlider.TicksBothSides)
        self.sliderTime.setTickInterval(1)
        self.sliderTime.setFocusPolicy(QtCore.Qt.ClickFocus)

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
        self.scaleSlider.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.gammaSlider = QtGui.QSlider(QtCore.Qt.Vertical)
        self.gammaSlider.setRange(0, 200)
        self.gammaSlider.setFocusPolicy(QtCore.Qt.ClickFocus)

        # self.gammaSlider.setValue(50)

        self.scaleSlider.valueChanged.connect(
            lambda x: self.glWidget.transform.setScale(0,x**2))
        self.glWidget.transform._maxChanged.connect(
            lambda x: self.scaleSlider.setValue(int(np.sqrt(x))))

        self.gammaSlider.valueChanged.connect(
            lambda x: self.glWidget.transform.setGamma(1+(x-100.)/200.))
        self.glWidget.transform._gammaChanged.connect(
            lambda x: self.gammaSlider.setValue(200*(x-1.)+100))


        # self.keyframes = KeyFrameList()
        self.keyPanel = KeyFramePanel(self.glWidget)
        self.keyPanel.hide()

        self.settingsView = SettingsPanel()
        self.settingsView.hide()

        self.setStyleSheet("background-color:black;")

        hbox0 = QtGui.QHBoxLayout()
        hbox0.addWidget(self.scaleSlider)
        hbox0.addWidget(self.gammaSlider)

        hbox0.addWidget(self.glWidget,stretch =1)


        hbox0.addWidget(self.settingsView)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.bwdButton)
        hbox.addWidget(self.startButton)
        hbox.addWidget(self.fwdButton)
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


        for box in [hbox,vbox,hbox0]:
            box.setContentsMargins(0,0,0,0)

        vbox.setSpacing(1)
        hbox.setSpacing(11)
        hbox0.setSpacing(5)

        # widget = QtGui.QWidget()
        self.setLayout(vbox)



        self.playTimer = QtCore.QTimer(self)
        self.playTimer.setInterval(100)
        self.playTimer.timeout.connect(self.onPlayTimer)
        self.settingsView._playIntervalChanged.connect(self.playIntervalChanged)
        self.setLoopBounce(True)

        self.settingsView.checkBox.stateChanged.connect(self.glWidget.transform.setBox)
        self.glWidget.transform._boxChanged.connect(self.settingsView.checkBox.setChecked)


        self.settingsView.checkProj.stateChanged.connect(self.glWidget.transform.setPerspective)
        self.glWidget.transform._perspectiveChanged.connect(self.settingsView.checkProj.setChecked)

        self.checkKey.stateChanged.connect(self.keyPanel.setVisible)
        self.checkSettings.stateChanged.connect(self.settingsView.setVisible)

        if not dataContainer:
            dataContainer = DemoData(70)

        dataModel = DataModel(dataContainer,prefetchSize = N_PREFETCH)

        self.settingsView.checkLoopBounce.stateChanged.connect(self.setLoopBounce)

        self.settingsView._stackUnitsChanged.connect(self.glWidget.transform.setStackUnits)
        self.glWidget.transform._stackUnitsChanged.connect(self.settingsView.setStackUnits)

        self.settingsView._frameNumberChanged.connect(self.keyPanel.setFrameNumber)

        self.settingsView._dirNameChanged.connect(self.keyPanel.setDirName)
        # dataModel._dataSourceChanged.connect(self.dataSourceChanged)
        # dataModel._dataPosChanged.connect(self.sliderTime.setValue)

        self.glWidget._dataModelChanged.connect(self.dataModelChanged)

        self.setModel(dataModel)

        self.hiddableControls = [self.checkSettings,
                                 self.startButton,self.sliderTime,self.spinTime,
                                 self.checkKey,self.screenshotButton ]

        # self.keyPanel.keyView.setModel(self.keyframes)



    def initUI(self):
        pass

    def initActions(self):
        self.exitAction = QtGui.QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.close)


    # def initMenus(self):
    #     menuBar = self.menuBar()
    #     fileMenu = menuBar.addMenu('&File')
    #     fileMenu.addAction(self.exitAction)
    #     # this has to be repeated in MAC OSX for some magic reason
    #     fileMenu = menuBar.addMenu('&File')

    def setModel(self,dataModel):
        self.glWidget.setModel(dataModel)

    def dataModelChanged(self):
        logger.info("data Model changed")
        dataModel = self.glWidget.dataModel
        dataModel._dataSourceChanged.connect(self.dataSourceChanged)

        # self.sliderTime.valueChanged.connect(dataModel.setPos)

        dataModel._dataPosChanged.connect(self.sliderTime.setValue)
        self.sliderTime.valueChanged.connect(self.glWidget.transform.setPos)


        self.keyPanel.setTransformModel(self.glWidget.transform)

        self.dataSourceChanged()

    def dataSourceChanged(self):
        self.sliderTime.setRange(0,self.glWidget.dataModel.sizeT()-1)
        self.sliderTime.setValue(0)
        self.spinTime.setRange(0,self.glWidget.dataModel.sizeT()-1)
        self.settingsView.dimensionLabel.setText("Dim: %s"%str(tuple(self.glWidget.dataModel.size()[::-1])))

        if self.myparent:
            self.myparent.setWindowTitle(self.glWidget.dataModel.name())
        else:
            self.setWindowTitle(self.glWidget.dataModel.name())


        d = self.glWidget.dataModel[self.glWidget.dataModel.pos]
        minMaxMean = (np.amin(d),np.amax(d),np.mean(d))
        self.settingsView.statsLabel.setText("Min:\t%.2f\nMax:\t%.2f \nMean:\t%.2f"%minMaxMean)



    def forward(self,event):
        newpos = (self.glWidget.dataModel.pos+1)%self.glWidget.dataModel.sizeT()
        self.glWidget.transform.setPos(newpos)

    def backward(self,event):
        newpos = (self.glWidget.dataModel.pos-1)%self.glWidget.dataModel.sizeT()
        self.glWidget.transform.setPos(newpos)


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


    def setLoopBounce(self,loopBounce):
        #if loopBounce = True, then while playing it should loop back and forth
        self.loopBounce = loopBounce
        self.settingsView.checkLoopBounce.setChecked(loopBounce)
        self.playD = 1


    def playIntervalChanged(self,val):
        if self.playTimer.isActive():
            self.playTimer.stop()
        self.playTimer.setInterval(val)

        print val



    def onPlayTimer(self):

        if self.glWidget.dataModel.pos == self.glWidget.dataModel.sizeT()-1:
            self.playDir = 1-2*self.loopBounce
        if self.glWidget.dataModel.pos == 0:
            self.playDir = 1

        newpos = (self.glWidget.dataModel.pos+self.playDir)%self.glWidget.dataModel.sizeT()
        self.glWidget.transform.setPos(newpos)
        # self.glWidget.dataModel.setPos(newpos)


    def contextMenuEvent(self,event):
         # create context menu
        popMenu = QtGui.QMenu(self)
        action = QtGui.QAction('toggle controls', self)
        action.triggered.connect(self.toggleControls)
        popMenu.addAction(action)
        popMenu.setStyleSheet("background-color: white")
        # popMenu.exec_(QtGui.QCursor.pos())


    def toggleControls(self):
        for c in self.hiddableControls:
            c.setVisible(not c.isVisible())


    def closeEvent(self,event):
        self.close()
        event.accept()

    def close(self):
        if self.playTimer.isActive():
            self.playTimer.stop()
        super(MainWidget,self).close()


    def mouseDoubleClickEvent(self,event):
        super(MainWidget,self).mouseDoubleClickEvent(event)
        if self.isFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

        # there's a bug in Qt that disables drop after fullscreen, so reset it...
        self.setAcceptDrops(True)

        self.isFullScreen = not self.isFullScreen



if __name__ == '__main__':
    import argparse

    app = QtGui.QApplication(sys.argv)

    win = MainWidget()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
