
from __future__ import absolute_import
from __future__ import print_function
import logging
from six.moves import zip
logger = logging.getLogger(__name__)


import sys
import os
from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtOpenGL

import numpy as np

from spimagine.gui.floatslider import FloatSlider

from spimagine.gui.gui_utils import createImageCheckbox,createStandardButton

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

# def createImgCheckBox(parentfName_active,fName_inactive):
#     checkBox = QtWidgets.QCheckBox()
#     checkBox.setStyleSheet(
#             checkBoxStyleStr%(absPath(fName_active),absPath(fName_inactive)))
#     return checkBox

# def createImgPushButton(parent,fName, tooltip = ""):
#     but = QtWidgets.QPushButton("",parent)
#     but.setStyleSheet("background-color: black;color:black")
#     but.setIcon(QtGui.QIcon(absPath(fname)))
#     but.setIconSize(QtCore.QSize(24,24))
#     but.clicked.connect(self.folderSelect)


class MainSettingsPanel(QtWidgets.QWidget):
    _playIntervalChanged = QtCore.pyqtSignal(int)
    _substepsChanged = QtCore.pyqtSignal(int)

    _dirNameChanged =  QtCore.pyqtSignal(str)
    _frameNumberChanged = QtCore.pyqtSignal(int)
    
    def __init__(self):
        super(QtWidgets.QWidget,self).__init__()

        self.resize(50, 300)
        self.initUI()


    def initUI(self):


        vbox = QtWidgets.QVBoxLayout()


        vbox.addWidget(QtWidgets.QLabel("Render",alignment = QtCore.Qt.AlignCenter))

        gridBox = QtWidgets.QGridLayout()

        gridBox.addWidget(QtWidgets.QLabel("loop bounce:\t"),0,0)
        self.checkLoopBounce = QtWidgets.QCheckBox()
        gridBox.addWidget(self.checkLoopBounce,0,1)


        gridBox.addWidget(QtWidgets.QLabel("play interval (ms):\t"))
        self.playInterval = QtWidgets.QLineEdit("50")
        self.playInterval.setValidator(QtGui.QIntValidator(bottom=10))
        self.playInterval.returnPressed.connect(self.playIntervalChanged)
        gridBox.addWidget(self.playInterval)

        gridBox.addWidget(QtWidgets.QLabel("subrender steps:\t"))
        self.editSubsteps = QtWidgets.QLineEdit("1")
        self.editSubsteps.setValidator(QtGui.QIntValidator(bottom=1))
        self.editSubsteps.returnPressed.connect(self.substepsChanged)
        gridBox.addWidget(self.editSubsteps)

        gridBox.addWidget(QtWidgets.QLabel("Egg3D:\t"))
        self.checkEgg = createImageCheckbox(self, absPath("images/egg.png"),
                                            absPath("images/egg_inactive.png"),
                                            tooltip="toggle egg control")

        gridBox.addWidget(self.checkEgg)

        vbox.addLayout(gridBox)

        line =  QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)

        vbox.addWidget(line)

        vbox.addWidget(QtWidgets.QLabel("General",
                                    alignment = QtCore.Qt.AlignCenter))

        renderFolder = QtWidgets.QLineEdit("./")
        hbox = QtWidgets.QHBoxLayout()

        hbox.addWidget(QtWidgets.QLabel("output folder: ",
                                    alignment = QtCore.Qt.AlignCenter))

        hbox.addWidget(renderFolder)

        folderButton = createStandardButton(self,
                        absPath("images/icon_folder.png"),
                        tooltip = "folder to render to")
        
        folderButton.clicked.connect(self.folderSelect)

        hbox.addWidget(folderButton)

        renderFolder.returnPressed.connect(lambda: self.setDirName(renderFolder.text()))
        self._dirNameChanged.connect(renderFolder.setText)

        self.setDirName("./")

        vbox.addLayout(hbox)

        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("number frames:\t"))
        frameEdit = QtWidgets.QLineEdit("100")
        frameEdit.setValidator(QtGui.QIntValidator(bottom=1))
        frameEdit.returnPressed.connect(lambda: self._frameNumberChanged.emit(int(frameEdit.text())))
        hbox.addWidget(frameEdit)

        vbox.addLayout(hbox)

        self.setStyleSheet("""
        QFrame,QLabel,QLineEdit {
        color: white;
        }
        """)
        vbox.addStretch()

        self.setLayout(vbox)



    def setDirName(self,dirName):
        logger.debug("setDirName: %s"%dirName)
        self.dirName = dirName
        self._dirNameChanged.emit(dirName)


    def folderSelect(self,event):
        dirName= QtWidgets.QFileDialog.getExistingDirectory(self, 'select output folder',
                self.dirName)
        if dirName:
            self.setDirName(dirName)

    def onButtonColor(self):
        col = QtWidgets.QColorDialog.getColor()

        if col.isValid():
            color = 1./255*np.array(col.getRgb()[:3])
            self._rgbColorChanged.emit(*color)

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
            print("couldnt parse text")
            print(e)

    def playIntervalChanged(self):
        self._playIntervalChanged.emit(int(self.playInterval.text()))

    def substepsChanged(self):
        print("changed substeps to ", int(self.editSubsteps.text()))
        self._substepsChanged.emit(int(self.editSubsteps.text()))
        
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, ):
        super(QtWidgets.QMainWindow,self).__init__()

        self.resize(500, 300)
        self.setWindowTitle('Test')

        self.settings = MainSettingsPanel()
        self.setCentralWidget(self.settings)
        self.setStyleSheet("background-color:black;")

    def close(self):
        QtWidgets.qApp.quit()


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
