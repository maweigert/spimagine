from __future__ import absolute_import
from jack_input import JackSource
from PyQt5 import QtCore
import numpy as np

class JackPlugin(QtCore.QObject):
    NHist = 100
    def __init__(self, transform, n_bank = 0):
        super(JackPlugin,self).__init__()
        self.n_bank = n_bank
        self.transform = transform
        self.s = JackSource()
        self.history = [1.]*self.NHist

    def start(self):
        self.s.start()
        
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.onTimer)
        self.timer.start()

    def onTimer(self):
        val = self.s.data[self.n_bank]
        
        avg = val/np.mean(self.history)

        self.transform.setZoom(1+.03*avg)

        # p = 2.*np.pi*np.random.uniform(0,1.)
        # t = np.arccos(2.*np.random.uniform(0,1.)-1.)
        # x,y,z = np.cos(p)*np.sin(t),np.sin(p)*np.sin(t),np.cos(t)
        # self.transform.addRotation(.01*(1.e-5+avg),x,y,z)
        
        self.history.pop(0)
        self.history.append(val)
        
if __name__ == '__main__':


    p = JackPlugin(None)

    p.start()
    
    while(1):
        pass
