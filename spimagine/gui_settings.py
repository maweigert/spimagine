import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
import numpy as np

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


class SettingsPanel(QtGui.QWidget):
    _stackUnitsChanged = QtCore.pyqtSignal(float,float,float)
    _playIntervalChanged = QtCore.pyqtSignal(int)
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

        # the perspective/box checkboxes
        checkBoxStyleStr = """
        QCheckBox::indicator:checked {
        background:black;
        border-image: url(%s);}
        QCheckBox::indicator:unchecked {
        background:black;
        border-image: url(%s);}
        """

        self.checkProj  = QtGui.QCheckBox()
        self.checkProj.setStyleSheet(
            checkBoxStyleStr%(absPath("images/rays_persp.png"),absPath("images/rays_ortho.png")))

        self.checkBox = QtGui.QCheckBox()
        self.checkBox.setStyleSheet(
            checkBoxStyleStr%(absPath("images/wire_cube.png"),absPath("images/wire_cube_inactive.png")))


        self.checkLoopBounce = QtGui.QCheckBox()


        gridBox = QtGui.QGridLayout()

        gridBox.addWidget(QtGui.QLabel("projection:\t"),1,0)
        gridBox.addWidget(self.checkProj,1,1)

        gridBox.addWidget(QtGui.QLabel("bounding box:\t"),2,0)
        gridBox.addWidget(self.checkBox,2,1)


        gridBox.addWidget(QtGui.QLabel("loop bounce:\t"),3,0)
        gridBox.addWidget(self.checkLoopBounce,3,1)


        gridBox.addWidget(QtGui.QLabel("play interval (ms):\t"))

        self.playInterval = QtGui.QLineEdit("50")
        self.playInterval.setValidator(QtGui.QIntValidator(bottom=10))
        self.playInterval.returnPressed.connect(self.playIntervalChanged)
        gridBox.addWidget(self.playInterval)

        vbox.addLayout(gridBox)


        vbox.addStretch()
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



        self.setLayout(vbox)

    def setStackUnits(self,px,py,pz):
        for e,p in zip(self.stackEdits,[px,py,pz]):
            e.setText(str(p))


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
