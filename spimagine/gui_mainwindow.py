import sys
import os
import numpy as np


from PyQt4 import QtCore
from PyQt4 import QtGui

from quaternion import Quaternion
from gui_glwidget import GLWidget
from data_model import DataLoadModel, DemoData


N_PREFETCH = 20


def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, myPath)


class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(800, 700)
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

        self.setStyleSheet("background-color:black;")

        hbox0 = QtGui.QHBoxLayout()
        hbox0.addWidget(self.glWidget)
        hbox0.addWidget(self.scaleSlider)
        hbox0.addWidget(self.gammaSlider)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.startButton)
        hbox.addWidget(self.sliderTime)
        hbox.addWidget(self.spinTime)


        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox0)

        vbox.addLayout(hbox)

        widget = QtGui.QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)



        self.playTimer = QtCore.QTimer(self)
        self.playTimer.setInterval(100)
        self.playTimer.timeout.connect(self.onPlayTimer)
        self.playDir = 1


        self.dataModel = DataLoadModel()

        self.dataModel._dataSourceChanged.connect(self.glWidget.dataSourceChanged)
        self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)

        self.dataModel._dataPosChanged.connect(self.glWidget.dataPosChanged)
        self.dataModel._dataPosChanged.connect(self.sliderTime.setValue)

        self.dataModel.load(dataContainer=DemoData(50),prefetchSize = N_PREFETCH)
        self.glWidget.setModel(self.dataModel)

        self.sliderTime.valueChanged.connect(self.dataModel.setPos)

        # self.dataModel.load("/Users/mweigert/python/Data/DrosophilaDeadPan/example/SPC0_TM0606_CM0_CM1_CHN00_CHN01.fusedStack.tif")

        # self.dataModel.load("/Users/mweigert/python/Data/Drosophila_05")\



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


    def startPlay(self,event):
        if self.playTimer.isActive():
            self.playTimer.stop()
            self.startButton.setIcon(QtGui.QIcon(absPath("images/icon_start.png")))

        else:
            self.playTimer.start()
            self.startButton.setIcon(QtGui.QIcon(absPath("images/icon_pause.png")))


    def onPlayTimer(self):

        if self.dataModel.pos == self.dataModel.sizeT()-1:
            self.playDir = -1
        if self.dataModel.pos == 0:
            self.playDir = 1

        print self.dataModel.pos, self.playDir
        newpos = (self.dataModel.pos+self.playDir)%self.dataModel.sizeT()
        self.dataModel.setPos(newpos)
        self.glWidget.transform.quatRot *= Quaternion(np.cos(.01),0,np.sin(0.01),0)

    def close(self):
        isAppRunning = False
        QtGui.qApp.quit()



if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
