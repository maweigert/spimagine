
import logging
logger = logging.getLogger(__name__)


import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL

from spimagine.floatslider import FloatSlider

import numpy as np

from gui_utils import *

import spimagine


def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


checkBoxStyleStr = """
    QCheckBox::indicator:checked {
    background:black;
    border-image: url(%s);}
    QCheckBox::indicator:unchecked {
    background:black;
    border-image: url(%s);}
    """

def createImgCheckBox(fName_active,fName_inactive):
    checkBox = QtGui.QCheckBox()
    checkBox.setStyleSheet(
            checkBoxStyleStr%(absPath(fName_active),absPath(fName_inactive)))
    return checkBox



class SettingsPanel(QtGui.QWidget):
    _stackUnitsChanged = QtCore.pyqtSignal(float,float,float)
    _playIntervalChanged = QtCore.pyqtSignal(int)
    _dirNameChanged =  QtCore.pyqtSignal(str)
    _frameNumberChanged = QtCore.pyqtSignal(int)
    _boundsChanged =  QtCore.pyqtSignal(float,float,float,float,float,float)
    _alphaPowChanged = QtCore.pyqtSignal(float)

    def __init__(self):
        super(QtGui.QWidget,self).__init__()

        self.resize(50, 300)
        self.initUI()


    def initUI(self):


        # The stack units line edits
        stackLabels = ["x","y","z"]

        vbox = QtGui.QVBoxLayout()



        vbox.addWidget(QtGui.QLabel("Stack units",alignment = QtCore.Qt.AlignCenter))


        self.stackEdits = []
        for lab in stackLabels:
            hbox = QtGui.QHBoxLayout()
            edit = QtGui.QLineEdit("1.0")
            edit.setValidator(QtGui.QDoubleValidator(bottom=1e-10))
            edit.returnPressed.connect(self.stackUnitsChanged)
            hbox.addWidget(QtGui.QLabel(lab))
            hbox.addWidget(edit)
            vbox.addLayout(hbox)
            self.stackEdits.append(edit)

        line =  QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)

        vbox.addWidget(line)
        vbox.addWidget(QtGui.QLabel("Display",alignment = QtCore.Qt.AlignCenter))

        # the perspective/box checkboxes


        self.checkProj = createStandardCheckbox(self,absPath("images/rays_persp.png"),
                                                    absPath("images/rays_ortho.png"), tooltip="projection")

        self.checkBox = createStandardCheckbox(self,absPath("images/wire_cube.png"),
                                                    absPath("images/wire_cube_incative.png"),
                                                    tooltip="toggle box")

        self.checkLoopBounce = QtGui.QCheckBox()



        self.checkEgg = createStandardCheckbox(self,absPath("images/egg.png"),
                                                    absPath("images/egg_inactive.png"),
                                                    tooltip="toggle egg control")

        gridBox = QtGui.QGridLayout()

        gridBox.addWidget(QtGui.QLabel("projection:\t"),1,0)
        gridBox.addWidget(self.checkProj,1,1)

        gridBox.addWidget(QtGui.QLabel("bounding box:\t"),2,0)
        gridBox.addWidget(self.checkBox,2,1)

        gridBox.addWidget(QtGui.QLabel("colormap:\t"),3,0)

        self.colorCombo = QtGui.QComboBox()

        self.colormaps = list(spimagine.__COLORMAPDICT__.keys())

        self.colorCombo.setIconSize(QtCore.QSize(100,20))

        for s in self.colormaps:
            self.colorCombo.addItem(QtGui.QIcon(absPath("colormaps/cmap_%s.png"%s)),"")



        gridBox.addWidget(self.colorCombo,3,1)


        gridBox.addWidget(QtGui.QLabel("loop bounce:\t"),4,0)
        gridBox.addWidget(self.checkLoopBounce,4,1)


        gridBox.addWidget(QtGui.QLabel("play interval (ms):\t"))

        self.playInterval = QtGui.QLineEdit("50")
        self.playInterval.setValidator(QtGui.QIntValidator(bottom=10))
        self.playInterval.returnPressed.connect(self.playIntervalChanged)
        gridBox.addWidget(self.playInterval)

        gridBox.addWidget(QtGui.QLabel("Egg3D:\t"),6,0)
        gridBox.addWidget(self.checkEgg,6,1)


        self.sliderAlphaPow = FloatSlider(QtCore.Qt.Horizontal)
        self.sliderAlphaPow.setRange(0,1.)
        self.sliderAlphaPow.setTickInterval(1)
        self.sliderAlphaPow.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.sliderAlphaPow.setTracking(True)
        self.sliderAlphaPow.setValue(1.)

        gridBox.addWidget(QtGui.QLabel("opacity transfer:\t"),7,0)
        gridBox.addWidget(self.sliderAlphaPow,7,1)

        vbox.addLayout(gridBox)


        vbox.addStretch()
        line =  QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)

        vbox.addWidget(line)

        #################

        gridBox = QtGui.QGridLayout()
        self.sliderBounds = [QtGui.QSlider(QtCore.Qt.Horizontal) for _ in range(6)]
        for i,s in enumerate(self.sliderBounds):
            s.setTickPosition(QtGui.QSlider.TicksBothSides)
            s.setRange(-100,100)
            s.setTickInterval(1)
            s.setFocusPolicy(QtCore.Qt.ClickFocus)
            s.setTracking(True)
            s.setValue(-100+200*(i%2))
            s.valueChanged.connect(self.boundsChanged)
            s.setStyleSheet("height: 12px; border = 0px;")

            gridBox.addWidget(s,i,1)


        vbox.addLayout(gridBox)

        vbox.addWidget(QtGui.QLabel("Render",alignment = QtCore.Qt.AlignCenter))

        renderFolder = QtGui.QLineEdit("./")
        hbox = QtGui.QHBoxLayout()

        hbox.addWidget(QtGui.QLabel("output folder: ",alignment = QtCore.Qt.AlignCenter))

        hbox.addWidget(renderFolder)
        folderButton = QtGui.QPushButton("",self)
        folderButton.setStyleSheet("background-color: black")
        folderButton.setIcon(QtGui.QIcon(absPath("images/icon_folder.png")))
        folderButton.setIconSize(QtCore.QSize(24,24))
        folderButton.clicked.connect(self.folderSelect)
        # self.screenshotButton.setMaximumWidth(24)
        # self.screenshotButton.setMaximumHeight(24)

        hbox.addWidget(folderButton)

        renderFolder.returnPressed.connect(lambda: self.setDirName(renderFolder.text()))
        self._dirNameChanged.connect(renderFolder.setText)

        self.setDirName("./")

        vbox.addLayout(hbox)


        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("number frames:\t"))
        frameEdit = QtGui.QLineEdit("100")
        frameEdit.setValidator(QtGui.QIntValidator(bottom=1))
        frameEdit.returnPressed.connect(lambda: self._frameNumberChanged.emit(int(frameEdit.text())))
        hbox.addWidget(frameEdit)

        vbox.addLayout(hbox)

        line =  QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        vbox.addWidget(line)

        self.dimensionLabel = QtGui.QLabel("Dimensions:",alignment = QtCore.Qt.AlignLeft)
        vbox.addWidget(self.dimensionLabel)

        self.statsLabel = QtGui.QLabel("Max: Min: Mean:",alignment = QtCore.Qt.AlignLeft)
        vbox.addWidget(self.statsLabel)

        self.setStyleSheet("""
        QFrame,QLabel,QLineEdit {
        color: white;
        }
        """)
        self.colorCombo.setStyleSheet("background-color:none;")

        self.setLayout(vbox)



    def setDirName(self,dirName):
        logger.debug("setDirName: %s"%dirName)
        self.dirName = dirName
        self._dirNameChanged.emit(dirName)


    def folderSelect(self,event):
        dirName= QtGui.QFileDialog.getExistingDirectory(self, 'select output folder',
                self.dirName)
        if dirName:
            self.setDirName(dirName)


    def setStackUnits(self,px,py,pz):
        for e,p in zip(self.stackEdits,[px,py,pz]):
            e.setText(str(p))

    def setBounds(self,x1,x2,y1,y2,z1,z2):
        for x,s in zip([x1,x2,y1,y2,z1,z2],self.sliderBounds):
            flag = s.blockSignals(True)
            s.setValue(x*100)
            s.blockSignals(flag)


    def boundsChanged(self):
        bounds = [s.value()/100. for s in self.sliderBounds]
        self._boundsChanged.emit(*bounds)


    def alphaPowChanged(self):
        alphaPow = 100.*(self.sliderAlphaPow.value()/100.)**3
        self._alphaPowChanged.emit(alphaPow)

    def stackUnitsChanged(self):
        try:
            stackUnits = [float(e.text()) for e in self.stackEdits]
            self._stackUnitsChanged.emit(*stackUnits)
        except Exception as e:
            print "couldnt parse text"
            print e

    def playIntervalChanged(self):
        self._playIntervalChanged.emit(int(self.playInterval.text()))

class MainWindow(QtGui.QMainWindow):

    def __init__(self, ):
        super(QtGui.QMainWindow,self).__init__()

        self.resize(500, 300)
        self.setWindowTitle('Test')

        self.settings = SettingsPanel()
        self.setCentralWidget(self.settings)
        self.setStyleSheet("background-color:black;")

    def close(self):
        QtGui.qApp.quit()


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
