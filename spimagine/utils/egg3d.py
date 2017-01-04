"""

receive input data of Loics Egg3d controller and emit qt signals

"""

from __future__ import absolute_import
from __future__ import print_function
from PyQt5 import QtCore,QtGui, QtWidgets

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
        val = eval("np.array(%s)"%tmp)
    except:
        val = np.array([1,0,0,0,0,0,0,0,0,0])

    return val




class Egg3dListener(QtCore.QThread):
    _quaternionChanged =  QtCore.pyqtSignal(float,float,float,float)
    _zoomChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super(Egg3dListener,self).__init__()

    def set_socket(self,s):
        self.socket = s

    def run(self):
        print("Egg3dlistener started")
        self.isActive = True
        self.vals = []
        while self.isActive:
            try:
                val = getEggData(self.socket)

                #acceleration
                if sum(abs(val[4:7]))>.5:
                    # button pressed?
                    self._zoomChanged.emit(2.*(val[-1]>125)-1)

                #rotation
                quat = val[:4]
                self._quaternionChanged.emit(*val[:4])
                    
            except  Exception as e:
                print("could not read", e)
            time.sleep(0.005)




class Egg3dController(QtCore.QObject):

    def __init__(self,):
        super(Egg3dController,self).__init__()
        self.listener = Egg3dListener()

    def _reset(self, port=4444):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener.set_socket(self.socket)
            self.socket.connect(("localhost",port))
            # self.listener._zoomChanged.connect(self.foo)
            print("connection with Egg3d established!")
        except Exception as e:
            print("Couldnt connect with port %i:  %s"%(port,e))
            raise Exception("Connection refused at port %s"%port)


    def start(self):
        print("starting Egg3dController...")

        self._reset()
        self.listener.start()

    def stop(self):
        print("stopping Egg3dController...")
        self.listener.isActive = False
        # self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()


    def foo(self,zoom):
        print(zoom)




if __name__ == '__main__':


    egg = Egg3dController()




    egg.start()

    time.sleep(20)


    egg.stop()

    # time.sleep(1)

    # egg.start()



    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # s.connect(("localhost",4444))


    # while True:
    #     d = getEggData(s)
    #     print d
