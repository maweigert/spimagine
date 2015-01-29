
import numpy as np

import os

from PyQt4 import Qt, QtCore, QtGui

class FloatSlider(QtGui.QSlider):
    floatValueChanged = QtCore.pyqtSignal(float)
    def __init__(self,*args):
        super(FloatSlider,self).__init__(*args)
        self.setRange(0,1.,100)
        self.valueChanged.connect(self.onChanged)

    def setRange(self,minVal,maxVal,steps=100):
        assert(minVal < maxVal)
        super(FloatSlider,self).setRange(0,steps)
        self.minVal = minVal
        self.maxVal = maxVal
        self.steps = steps

    def _from_float(self,x):
        ind = int(self.steps*(x-self.minVal)/(self.maxVal-self.minVal))
        ind = max(0,min(self.steps,ind))
        return ind

    def _from_int(self,n):
        return self.minVal+1.*(self.maxVal-self.minVal)*n/self.steps

    def setValue(self,val):
        super(FloatSlider,self).setValue(self._from_float(val))

    def value(self):
        return self._from_int(super(FloatSlider,self).value())

    def onChanged(self,ind):
        self.floatValueChanged.emit(self._from_int(ind))



class MainWindow(QtGui.QWidget):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.slide = FloatSlider(QtCore.Qt.Horizontal)
        self.slide.setRange(1.,6.)
        self.slide.valueChanged.connect(self.onSlide)
        self.slide.floatValueChanged.connect(self.onSlideFloat)


        self.slide.setValue(.3)
        self.setWindowTitle("Key Frame View")


        self.resize(500,200)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.slide)

        self.setLayout(hbox)


    def onSlide(self,val):
        print "int:\t",val

    def onSlideFloat(self,val):
        print "float:\t",val


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()

    win.show()
    win.raise_()

    app.exec_()
