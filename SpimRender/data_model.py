import os
import numpy as np
from PyQt4 import QtCore
import time
import re
from collections import defaultdict
from dataloader import SpimData, TiffData



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
                    self._rwLock.lockForWrite()
                    self.data[k] = self.dataContainer[k]
                    self._rwLock.unlock()
                    time.sleep(.0001)
            time.sleep(.0001)


class DataLoadModel(QtCore.QObject):
    _dataSourceChanged = QtCore.pyqtSignal()
    _rwLock = QtCore.QReadWriteLock()

    def __init__(self, fName = "", prefetchSize = 0):
        super(DataLoadModel,self).__init__()

        self.dataLoadThread = DataLoadThread(self._rwLock)
        self._dataSourceChanged.connect(self.dataSourceChanged)

        if fName:
            self.load(fName, prefetchSize)


    def dataSourceChanged(self):
        print "data source changed"

    def load(self,fName, prefetchSize = 0):
        try:
            self.dataContainer = self.chooseContainer(fName)
        except Exception as e:
            print "couldnt load abstract data container ", fName
            print e
            return

        self.fName = fName
        self.prefetchSize = prefetchSize
        self.nset = []
        self.data = defaultdict(lambda: None)

        if prefetchSize > 0:
            self.dataLoadThread.stopped = True
            self.dataLoadThread.load(self.nset,self.data, self.dataContainer)
            self.dataLoadThread.start(priority=QtCore.QThread.HighPriority)

        self._dataSourceChanged.emit()

    def chooseContainer(self,fName):
        if re.match(".*\.tif",fName):
            return TiffData(fName)
        else:
            return SpimData(fName)


    def stop(self):
        self.dataLoadThread.stopped = True

    def __getitem__(self,pos):
        # self._rwLock.lockForRead()
        if not hasattr(self,"data"):
            return None

        if not self.data.has_key(pos):
            self._rwLock.lockForWrite()
            self.data[pos] = self.dataContainer[pos]
            self._rwLock.unlock()


        if self.prefetchSize > 0:
            self._rwLock.lockForWrite()
            self.nset[:] = self.neighborhood(pos)
            self._rwLock.unlock()

        return self.data[pos]


    def neighborhood(self,pos):
        # FIXME mod stackSize!
        return range(pos,pos+self.prefetchSize+1)


class MyData(DataLoadModel):
    def dataSourceChanged(self):
        print "a new one!!"



if __name__ == '__main__':

    fName = "/Users/mweigert/python/Data/DrosophilaDeadPan/example/SPC0_TM0606_CM0_CM1_CHN00_CHN01.fusedStack.tif"

    # fName = "/Users/mweigert/python/Data/Drosophila_Full"

    loader = DataLoadModel(fName,3)



    dt = 0

    for i in range(10):
        print i
        time.sleep(.1)
        t = time.time()
        # time.sleep(.1)

        d = loader[i]
        dt += (time.time()-t)

    print "%.3fs per fetch "%(dt/10.)

    loader.stop()
