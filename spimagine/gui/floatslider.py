
from __future__ import absolute_import, print_function

import numpy as np

import os

from PyQt5 import Qt, QtCore, QtGui, QtWidgets

import logging

logger = logging.getLogger(__name__)




class FloatSlider(QtWidgets.QSlider):
    floatValueChanged = QtCore.pyqtSignal(float)
    def __init__(self,*args):
        super(FloatSlider,self).__init__(*args)
        self.setRange(0,1.,100)
        self.valueChanged.connect(self.onChanged)

        self.setStyleSheet("QToolTip { color:white;}")

    def setRange(self,minVal,maxVal,steps=100):
        assert(minVal <= maxVal)
        super(FloatSlider,self).setRange(0,steps)
        self.minVal = minVal
        self.maxVal = maxVal
        self.steps = steps

    def _from_float(self,x):
        ind = int(self.steps*(x-self.minVal)/(self.maxVal-self.minVal))
        ind = max(0,min(self.steps,ind))
        logger.debug("floatslider (id = %s):  index from float %s = %s"%(id(self), x,ind))
        return ind

    def _from_int(self,n):

        return self.minVal+1.*(self.maxVal-self.minVal)*n/self.steps


    def setValue(self,val):
        logger.debug("floatslider (id = %s): setValue to : %s"%(id(self),val))
        self.floatValue = val
        super(FloatSlider,self).setValue(self._from_float(val))

    def value(self):
        return self.floatValue
        # return self._from_int(super(FloatSlider,self).value())

    def onChanged(self,ind):
        self.floatValue = self._from_int(ind)

        self.floatValueChanged.emit(self.floatValue)

        # self.floatValueChanged.emit(self._from_int(ind))



class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.slide = FloatSlider(QtCore.Qt.Horizontal)
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


    def onSlide(self,val):
        print("int:\t",val)

    def onSlideFloat(self,val):
        print("float:\t",val)


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)

    win = MainWindow()

    win.show()
    win.raise_()

    app.exec_()
