from numpy import *

from PyQt4.QtCore import QObject, pyqtProperty



def generic_getter(varName):
    def get(self):
        return self.__dict__[varName]
    return get

def generic_setter(varName, signal_to_emit = None):
    def set(self, val):
        self.__dict__[varName] = val
        if signal_to_emit is not None:
            signal_to_emit.emit(val)
            
    return set


def getX(self):
    return self._x

def setX(self, val):
    self._x = val

class Foo(QObject):

    def __init__(self):
        QObject.__init__(self)

        self._total = 0
        self._vec = array([1,1])
        self._x = [99,67]


    @pyqtProperty(int)
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        self._total = value

    @pyqtProperty(int,int)
    def vec(self):
        return self._vec

    @vec.setter
    def vec(self,x):
        self._vec = array(x)


    x = pyqtProperty(tuple,getter("_x"),setter("_x"))

def genGetFunc(myVar):
    def get():
        return myVar
    return get


if __name__ == '__main__':


    f = Foo()
    g = Foo()
