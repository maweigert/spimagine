"""

receive input data of Loics Egg3d controller and emit qt signals

"""

from PyQt4 import QtCore,QtGui

import socket

import select
import numpy as np


import time



def empty_socket(sock):
    """remove the data present on the socket"""
    input = [sock]
    while 1:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready)==0: break
        for s in inputready: s.recv(4096)


def getEggData(s):


    while s.recv(1) != "[":
        pass
    tmp = "["

    while tmp.find(']') == -1:
        tmp += s.recv(1)

    empty_socket(s)

    try:
        q = eval("np.array(%s)"%tmp)
    except:
        q = np.array([1,0,0,0,0,0,0,0,0,0])
    return q[0],q[1],q[2],q[3]




class Egg3dListener(QtCore.QThread):
    _quaternionChanged =  QtCore.pyqtSignal(float,float,float,float)
    foo = QtCore.pyqtSignal()

    def __init__(self, socket):
        super(Egg3dListener,self).__init__()
        self.socket = socket
        self.signal = QtCore.SIGNAL("SIGNAL")


    def run(self):
        print "Egg3dlistener started"
        while True:
            time.sleep(0.01)
            self._quaternionChanged.emit(*getEggData(self.socket))



class Egg3dController(QtCore.QObject):

    def __init__(self,):
        super(Egg3dController,self).__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener = Egg3dListener(self.socket)
        self.listener.foo.connect(self.foo)

    def connect(self, port=4444):
        try:
            self.socket.connect(("localhost",port))
            print "connection with Egg3d established!"
        except Exception as e:
            print "Couldnt connect with port %i:  %s"%(port,e)
            raise Exception("Connection refused at port %s"%port)


    def start(self):
        self.listener.start()

    def foo(self):
        print "FOOOO"

    # def onChanged(self,a,b,c,d):

    #     print "changed!", a,b,c,d





if __name__ == '__main__':


    egg = Egg3dController()

    egg.connect()

    egg.start()


    print "s"

    time.sleep(5)

    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # s.connect(("localhost",4444))


    # while True:
    #     d = getEggData(s)
    #     print d
