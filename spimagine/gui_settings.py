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

    def __init__(self):
        super(QtGui.QWidget,self).__init__()

        self.resize(50, 300)
        self.initUI()


    def initUI(self):


        # The stack units line edits
        stackLabels = ["x","y","z"]

        vbox = QtGui.QVBoxLayout()

        self.dimensionLabel = QtGui.QLabel("Dimensions:",alignment = QtCore.Qt.AlignLeft)
        vbox.addWidget(self.dimensionLabel)


        vbox.addWidget(QtGui.QLabel("Stack units",alignment = QtCore.Qt.AlignCenter))

        # hbox = QtGui.QHBoxLayout()
        # for lab in stackLabels:
        #     hbox.addWidget(QtGui.QLabel(lab,alignment = QtCore.Qt.AlignCenter))
        # vbox.addLayout(hbox)
        # hbox = QtGui.QHBoxLayout()

        # for lab in stackLabels:
        #     edit = QtGui.QLineEdit("1.0",alignment = QtCore.Qt.AlignCenter)
        #     edit.setFixedWidth(50)
        #     edit.setValidator(QtGui.QDoubleValidator(bottom=1e-10))
        #     hbox.addWidget(edit)
        # vbox.addLayout(hbox)


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

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("projection:"))
        hbox.addWidget(self.checkProj)
        vbox.addLayout(hbox)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("bounding box:"))
        hbox.addWidget(self.checkBox)
        vbox.addLayout(hbox)

        vbox.addStretch()





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
