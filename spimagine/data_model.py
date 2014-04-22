import os
import numpy as np
from PyQt4 import QtCore
import time
import re
from collections import defaultdict
from dataloader import GenericData, SpimData, TiffData


class DemoData(GenericData):
    def __init__(self, N = 200):
        GenericData.__init__(self)
        self.load(N)

    def load(self,N=200):
        self.stackSize = (N,N,N/2)
        self.fName = ""
        self.nT = N
        self.stackUnits = (1,1,1)
        x = np.linspace(-1,1,N)
        X,self.Y,Z = np.meshgrid(x[::2],x,x,indexing="ij")
        self.R  = np.sqrt(X**2+self.Y**2+Z**2)
        self.W = np.arctan2(Z,X)


    def sizeT(self):
        return self.nT

    def __getitem__(self,pos):
        return (700+400*np.exp(-100*(self.R-.8)**2)*(1+np.sin(20*self.Y))*(1+np.sin(10*self.W+.4*pos))).astype(np.uint16)





class DataLoadThread(QtCore.QThread):
    def __init__(self, _rwLock, nset = set(), data = None,dataContainer = None):
        QtCore.QThread.__init__(self)
        self._rwLock = _rwLock
        if nset and data and dataContainer:
            self.load(nset, data, dataContainer)


    def load(self, nset, data, dataContainer):
        self.nset = nset
        self.data = data
        self.dataContainer = dataContainer


    def run(self):
        self.stopped = False
        while not self.stopped:
            kset = set(self.data.keys())
            dkset = kset.difference(set(self.nset))
            dnset = set(self.nset).difference(kset)

            for k in dkset:
                del(self.data[k])

            if dnset:
                print "preloading ", list(dnset)
                for k in dnset:
                    newdata = self.dataContainer[k]
                    self._rwLock.lockForWrite()
                    self.data[k] = newdata
                    self._rwLock.unlock()
                    time.sleep(.0001)

            time.sleep(.0001)


class DataLoadModel(QtCore.QObject):
    _dataSourceChanged = QtCore.pyqtSignal()
    _dataPosChanged = QtCore.pyqtSignal(int)

    _rwLock = QtCore.QReadWriteLock()

    def __init__(self, fName = "", dataContainer = None, prefetchSize = 0):
        print "prefetch: ", prefetchSize
        super(DataLoadModel,self).__init__()

        self.dataLoadThread = DataLoadThread(self._rwLock)
        self._dataSourceChanged.connect(self.dataSourceChanged)
        self._dataPosChanged.connect(self.dataPosChanged)

        self.load(fName, dataContainer, prefetchSize = prefetchSize)


    def dataSourceChanged(self):
        print "data source changed"

    def dataPosChanged(self, pos):
        print "data position changed to %i"%pos



    def load(self,fName = "", dataContainer = None, prefetchSize = 0):
        if not fName and not dataContainer:
            return

        if not dataContainer:
            try:
                dataContainer = self.chooseContainer(fName)
            except Exception as e:
                print "couldnt load abstract data container ", fName
                print e
                return

        self.dataContainer = dataContainer


        self.fName = fName
        self.prefetchSize = prefetchSize
        self.nset = []
        self.data = defaultdict(lambda: None)

        if prefetchSize > 0:
            self.dataLoadThread.stopped = True
            self.dataLoadThread.load(self.nset,self.data, self.dataContainer)
            self.dataLoadThread.start(priority=QtCore.QThread.HighPriority)

        self._dataSourceChanged.emit()
        self.setPos(0)


    def chooseContainer(self,fName):
        if re.match(".*\.tif",fName):
            return TiffData(fName)
        else:
            return SpimData(fName)


    def stop(self):
        self.dataLoadThread.stopped = True

    def prefetch(self,pos):
        self._rwLock.lockForWrite()
        self.nset[:] = self.neighborhood(pos)
        self._rwLock.unlock()

    def sizeT(self):
        if self.dataContainer:
            return self.dataContainer.sizeT()


    def setPos(self,pos):
        if pos<0 or pos>=self.sizeT():
            raise IndexError("setPos(pos): %i outside of [0,%i]!"%(pos,self.sizeT()-1))
            return

        print "setPos: ",pos
        self.pos = pos
        self._dataPosChanged.emit(pos)
        self.prefetch(self.pos)


    def __getitem__(self,pos):
        # self._rwLock.lockForRead()
        if not hasattr(self,"data"):
            return None

        if not self.data.has_key(pos):
            newdata = self.dataContainer[pos]
            self._rwLock.lockForWrite()
            self.data[pos] = newdata
            self._rwLock.unlock()



        if self.prefetchSize > 0:
            self.prefetch(pos)

        return self.data[pos]


    def neighborhood(self,pos):
        # FIXME mod stackSize!
        return np.arange(pos,pos+self.prefetchSize+1)%self.sizeT()


class MyData(DataLoadModel):
    def dataSourceChanged(self):
        print "a new one!!"



if __name__ == '__main__':

    fName = "/Users/mweigert/python/Data/DrosophilaDeadPan/example/SPC0_TM0606_CM0_CM1_CHN00_CHN01.fusedStack.tif"

    # fName = "/Users/mweigert/python/Data/Drosophila_Full"

    loader = DataLoadModel(fName,prefetchSize = 10)


    d = loader[0]

    time.sleep(2)


    dt = 0

    for i in range(10):
        print i
        # time.sleep(.1)
        t = time.time()
        # time.sleep(.1)

        d = loader[i]
        dt += (time.time()-t)

    print "%.3fs per fetch "%(dt/10.)

    loader.stop()
