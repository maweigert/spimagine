
from __future__ import absolute_import, print_function

import logging
from six.moves import range, zip
logger = logging.getLogger(__name__)


import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets


import numpy as np


from spimagine.gui.gui_utils import createImageCheckbox,createStandardCheckbox, createStandardButton
from spimagine.gui.floatslider import FloatSlider

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



class MyWidget(QtWidgets.QWidget):

    def __init__(self):
        super(QtWidgets.QWidget ,self).__init__()

        self.resize(50, 300)
        self.initUI()


    def initUI(self):



        vbox = QtWidgets.QVBoxLayout()


        self.colorCombo = QtWidgets.QComboBox()

        self.colormaps = list(spimagine.config.__COLORMAPDICT__.keys())

        self.colorCombo.setIconSize(QtCore.QSize(70 ,20))
        for s in self.colormaps:
            print(s)
            self.colorCombo.addItem(QtGui.QIcon(absPath( "../../spimagine/colormaps/cmap_%s.png" %s)) ,s)


        vbox.addWidget(self.colorCombo)

        self.setLayout(vbox)




if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    win = MyWidget()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
