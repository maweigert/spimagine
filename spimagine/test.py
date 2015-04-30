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



def genGetFunc(myVar):
    def get():
        return myVar
    return get


class bar(object):
    x = 10
    @staticmethod
    def foo():
        print "foo"
    @classmethod
    def baz(cls):
        print "baz"


class KeyableParameter(object):
    val_dict = {}
    @classmethod
    def register_value(cls,name, default = 0.):
        cls.val_dict[name] = default
    @classmethod
    def __getattr__(cls,name):
        return cls.val_dict[name]


KeyableParameter.register_value("name","bernd")

from PyQt4 import QtCore

class MetaClass(QtCore.pyqtWrapperType):
    val_dict = {}
    

    def register_value(cls,name, default = 0.):
        cls.val_dict[name] = default
    def __getattr__(cls,name):
        return cls.val_dict[name]
    def __setattr__(cls,name,val):
        if cls.val_dict.has_key(name):
            cls.val_dict[name] = val
        else:
            super(MetaClass,cls).__setattr__(name,val)

class TransformAttributes:
    __metaclass__ = MetaClass

TransformAttributes.register_value("gamma",1.)
TransformAttributes.register_value("alphaPow",1.)

if __name__ == '__main__':


    bar.foo()

    bar.baz()
