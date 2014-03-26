import os
import numpy as np
from PyQt4 import QtCore
import time
import Queue
# import h5py
import SpimUtils
import re
from PIL import Image
from collections import defaultdict

# isAppRunning = True

# class DataLoadThread2(QtCore.QThread):
#     def __init__(self, dataQueue, fName = "", size = 6):
#         self.size = size
#         self.queue = dataQueue
#         QtCore.QThread.__init__(self)
#         self.getFunc = self.getfromH5

#     def run(self):
#         self.pos, self.nT  = 0, 10
#         dpos = 1
#         while isAppRunning:
#             if self.queue.qsize()<self.size and self.fName !="":

#                 print "fetching data at pos %i"%(self.pos)

#                 try:
#                     self.queue.put(self.getFunc(self.fName,self.pos))
#                 except Exception as e:
#                     print e
#                     print "couldnt open ", self.fName

#                 self.pos += dpos
#                 if self.pos>self.nT-1:
#                     self.pos = self.nT-1
#                     dpos = -1
#                 if self.pos<0:
#                     self.pos = 0
#                     dpos = 1

#     def getfromSpimFolder(self,fName,pos):
#         try:
#             d = SpimUtils.fromSpimFolder(fName,pos=pos,
#                                          count=1)[0,:,:,:]
#             return d
#         except Exception as e:
#             print e
#             print "couldnt open ", fName

#     def getfromH5(self,fName,pos):
#         try:
#             return self.f[str(self.pos)][...]
#         except Exception as e:
#             print e
#             print "couldnt open ", fName


#     def dataSourceChanged(self,fName):
#         self.fName = str(fName)
#         self.queue.queue.clear()
#         print "changed: ",fName
#         if re.match(".*\.h5",fName):
#             if hasattr(self,"f"):
#                 self.f.close()
#             self.getFunc = self.getfromH5
#             self.f = h5py.File(fName, "r")
#         else:
#             self.getFunc = self.getfromSpimFolder


def getTiffSize(fName):
    img = Image.open(fName, 'r')
    depth = 0
    while True:
        try:
            img.seek(depth)
        except EOFError:
            break
        depth += 1

    return (depth,)+img.size[::-1]


def read3dTiff(fName, depth = -1, dtype = np.uint16):

    if not depth>0:
        depth = getTiffSize(fName)[0]

    img = Image.open(fName, 'r')
    stackSize = (depth,) + img.size[::-1]

    data = np.empty(stackSize,dtype=dtype)

    for i in range(stackSize[0]):
        img.seek(i)
        data[i,...] = np.asarray(img, dtype= dtype)

    return data




class GenericData():
    dataFileError = Exception("not a valid file")
    def __init__(self):
        self.stackSize = None
        self.stackUnits = None

    def sizeT(self):
        return None

    def __getitem__(self,int):
        return None


class SpimData(GenericData):
    def __init__(self,fName = ""):
        GenericData.__init__(self)
        self.load(fName)

    def load(self,fName):
        if fName:
            try:
                self.stackSize = SpimUtils.parseIndexFile(os.path.join(fName,"data/index.txt"))
                self.stackUnits = SpimUtils.parseMetaFile(os.path.join(fName,"metadata.txt"))
                self.fName = fName
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as SpimData"%fName)

    def sizeT(self):
        if self.fName:
            return self.stackSize[0]
        else:
            return 0

    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            if pos<0 or pos>=self.stackSize[0]:
                raise IndexError("0 <= pos <= %i, but pos = %i"%(self.stackSize[0]-1,pos))


            pos = max(0,min(pos,self.stackSize[0]-1))
            voxels = np.prod(self.stackSize[1:])
            offset = 2*pos*voxels

            with open(os.path.join(self.fName,"data/data.bin"),"rb") as f:
                f.seek(offset)
                return np.fromfile(f,dtype="<u2",
                count=voxels).reshape(self.stackSize[1:])
        else:
            return None


class TiffData(GenericData):
    def __init__(self,fName = ""):
        GenericData.__init__(self)
        self.load(fName)

    def load(self,fName, stackUnits = None):
        if fName:
            try:
                self.stackSize = (1,)+ getTiffSize(fName)
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as TiffData"%fName)
                return

            if stackUnits:
                self.stackUnits = stackUnits
            self.fName = fName

    def sizeT(self):
        if self.fName:
            return 1
        else:
            return 0

    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            return read3dTiff(self.fName,depth = self.stackSize[1])
        else:
            return None



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


class DataLoader():
    _rwLock = QtCore.QReadWriteLock()

    def __init__(self, fName = "", prefetchSize = 0):
        self.dataLoadThread = DataLoadThread(self._rwLock)
        if fName:
            self.load(fName, prefetchSize)

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


    def chooseContainer(self,fName):
        if re.match(".*\.tif",fName):
            return TiffData(fName)
        else:
            return SpimData(fName)


    def stop(self):
        self.dataLoadThread.stopped = True

    def __getitem__(self,pos):
        # self._rwLock.lockForRead()
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




def test_spimLoader():
    loader = DataLoader("/Users/mweigert/python/Data/Drosophila_Full",0)


    dt = 0

    for i in range(20):
        print i
        time.sleep(.00001)
        t = time.time()
        d = loader[i]
        dt += (time.time()-t)

    print "%.4s per fetch "%(dt/20.)

    loader.stop()


if __name__ == '__main__':


    fName = "../../Data/DrosophilaDeadPan/example/SPC0_TM0606_CM0_CM1_CHN00_CHN01.fusedStack.tif"

    # data = read3dTiff(fName)

    data = TiffData()


    data.load(fName)

    d = data[0]
