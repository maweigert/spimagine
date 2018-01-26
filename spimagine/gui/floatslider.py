
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

        # this surpressed anoying feedback
        old = self.blockSignals(True)
        super(FloatSlider,self).setValue(self._from_float(val))
        self.blockSignals(old)

    def value(self):
        return self.floatValue
        # return self._from_int(super(FloatSlider,self).value())

    def onChanged(self,ind):
        self.floatValue = self._from_int(ind)
        self.floatValueChanged.emit(self.floatValue)
        # self.floatValueChanged.emit(self._from_int(ind))



