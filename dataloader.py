from PyQt4 import QtCore
import time
import Queue
import h5py
import SpimUtils
import re
from collections import OrderedDict
isAppRunning = True

class DataLoadThread2(QtCore.QThread):
    def __init__(self, dataQueue, fName = "", size = 6):
        self.size = size
        self.queue = dataQueue
        QtCore.QThread.__init__(self)
        self.getFunc = self.getfromH5

    def run(self):
        self.pos, self.nT  = 0, 10
        dpos = 1
        while isAppRunning:
            if self.queue.qsize()<self.size and self.fName !="":

                print "fetching data at pos %i"%(self.pos)

                try:
                    self.queue.put(self.getFunc(self.fName,self.pos))
                except Exception as e:
                    print e
                    print "couldnt open ", self.fName

                self.pos += dpos
                if self.pos>self.nT-1:
                    self.pos = self.nT-1
                    dpos = -1
                if self.pos<0:
                    self.pos = 0
                    dpos = 1

    def getfromSpimFolder(self,fName,pos):
        try:
            d = SpimUtils.fromSpimFolder(fName,pos=pos,
                                         count=1)[0,:,:,:]
            return d
        except Exception as e:
            print e
            print "couldnt open ", fName

    def getfromH5(self,fName,pos):
        try:
            return self.f[str(self.pos)][...]
        except Exception as e:
            print e
            print "couldnt open ", fName


    def dataSourceChanged(self,fName):
        self.fName = str(fName)
        self.queue.queue.clear()
        print "changed: ",fName
        if re.match(".*\.h5",fName):
            if hasattr(self,"f"):
                self.f.close()
            self.getFunc = self.getfromH5
            self.f = h5py.File(fName, "r")
        else:
            self.getFunc = self.getfromSpimFolder






class DataLoadThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        self.stopped = False
        while not self.stopped:
            print "thread"
            time.sleep(1)


class DataLoader():
    _rwLock = QtCore.QReadWriteLock()

    def __init__(self, prefetch_size = 4):
        self.data = OrderedDict()
        self.dataLoadThread = DataLoadThread()
        self.dataLoadThread.start()


    def foo(self):
        self.dataLoadThread.stopped = True

    def __getitem__(self,pos):
        try:
            return self.data[pos]
        except KeyError:
            #load the data




if __name__ == '__main__':
    # dataQueue = Queue.Queue()

    # thread = DataLoadThread(dataQueue,size = 4)

    # thread.dataSourceChanged("/Users/mweigert/Desktop/Phd/worms/test.h5")
    # thread.dataSourceChanged("/Users/mweigert/Desktop/Phd/worms/test_lzf.h5")

    # thread.dataSourceChanged("/Users/mweigert/python/Data/Drosophila_Full")
    # thread.getFunc = thread.getfromSpimFolder


    # thread.start(priority=QtCore.QThread.LowPriority)

    # N = 10
    # t = time.time()

    # for i in range(N):
    #     print i
    #     d = dataQueue.get(timeout=2)

    # print "",(1.*time.time()-t)/N

    # isAppRunning = False


    loader = DataLoader()


    time.sleep(4)
    loader.foo()
