
from __future__ import absolute_import, print_function

import numpy as np
import sys
import os

from PyQt5 import Qt, QtCore, QtGui, QtWidgets

from spimagine.gui.floatslider import FloatSlider


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.slide = FloatSlider(QtCore.Qt.Vertical)
        self.slide.setRange(-12.,10.,400)
        self.slide.valueChanged.connect(self.onSlide)
        self.slide.floatValueChanged.connect(self.onSlideFloat)


        self.slide.setValue(7.)
        self.setWindowTitle("Key Frame View")


        self.edit = QtWidgets.QLineEdit("")
        self.edit.setValidator(QtGui.QDoubleValidator())
        self.edit.returnPressed.connect(lambda: self.slide.setValue(float(self.edit.text())))


        self.slide.floatValueChanged.connect(lambda x: self.edit.setText(str(x)))



        self.resize(500,200)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.slide)
        hbox.addWidget(self.edit)

        self.setLayout(hbox)

        # self.setStyleSheet("""
        #    background-color:black;
        #    color:black;""")

    def onSlide(self,val):
        print("int:\t",val)

    def onSlideFloat(self,val):
        print("float:\t",val)



if __name__ == '__main__':


    app = QtWidgets.QApplication(sys.argv)

    win = MainWindow()

    win.show()
    win.raise_()

    app.exec_()
