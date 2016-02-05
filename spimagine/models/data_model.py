#!/usr/bin/env python

"""
the (Qt) data models for usage in the gui frame

generic containers are defined for BScope Spim Data (SpimData)
and Tiff files (TiffData).
Extend it if you want to and change the DataLoadModel.chooseContainer to
accept it via dropg

at the end every data nodel is assumed to be 5d (Time,Channel,ZYZ)

author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import logging
logger = logging.getLogger(__name__)


import os
import numpy as np
import time

from PyQt4 import QtCore



import re
import glob


# import h5py


from collections import defaultdict

import spimagine.utils.imgutils as imgutils

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


############################################################################
"""
The next classes define simple 5d (time+channel+3d) Data Structures that implement the interface
given by GenericData
"""

class GenericData():
    """abstract base class for 5d data

    if you wanna sublass it, just overwrite self.size() and self.__getitem__()

    """
    dataFileError = Exception("not a valid file")
    _DIM_WITHOUT_TIME = 4

    def __init__(self, name = ""):
        self.stackSize = None
        self.stackUnits = None
        self.name = name


    def sizeT(self):
        return self.size()[0]

    def sizeC(self):
        return self.size()[1]

    def size(self):
        return self.stackSize

    def __getitem__(self,i):
        return None

    @classmethod
    def _basic_shape_to_dim(cls, shape, ndim):
        """reshapes shape such that its dim = _DIM_WITHOUT_TIME"""
        if len(shape)>ndim:
            raise ValueError("invalid data dimension! (len(shape)=%s > %s)"%
                             (len(shape),ndim))

        return (1,)*(ndim-len(shape))+shape

    @classmethod
    def shape_to_dim(cls, shape, include_time = False):
        """reshapes shape such that its dim = _DIM_WITHOUT_TIME"""
        if include_time:
            return cls._basic_shape_to_dim(shape,cls._DIM_WITHOUT_TIME+1)
        else:
            return cls._basic_shape_to_dim(shape,cls._DIM_WITHOUT_TIME)

    @classmethod
    def reshape_to_dim(cls, data, include_time = False):
        """reshapes data such that its dim = _DIM_WITHOUT_TIME"""
        return data.reshape(cls.shape_to_dim(data.shape, include_time))



class SpimData(GenericData):
    """data class for spim data saved in folder fName
    fname/
    |-- metadata.txt
    |-- data/
       |--data.bin
       |--index.txt
    """
    def __init__(self,fName = ""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self,fName):
        if fName:
            try:
                self.stackSize = imgutils.parseIndexFile(os.path.join(fName,"data/index.txt"))
                # no multichannel for now...
                self.stackSize = self.stackSize[:1]+[1,]+self.stackSize[1:]
                self.stackUnits = imgutils.parseMetaFile(os.path.join(fName,"metadata.txt"))
                self.fName = fName
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as SpimData"%fName)

            try:
                # try to figure out the dimension of the dark frame stack
                darkSizeZ = os.path.getsize(os.path.join(self.fName,"data/darkstack.bin"))/2/self.stackSize[2]/self.stackSize[3]
                with open(os.path.join(self.fName,"data/darkstack.bin"),"rb") as f:
                    self.darkStack = np.fromfile(f,dtype="<u2").reshape([darkSizeZ,self.stackSize[2],self.stackSize[3]])

            except Exception as e:
                logger.warning("couldn't find darkstack (%s)",e)


    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            if pos<0 or pos>=self.stackSize[0]:
                raise IndexError("0 <= pos <= %i, but pos = %i"%(self.stackSize[0]-1,pos))


            pos = max(0,min(pos,self.stackSize[0]-1))
            voxels = np.prod(self.stackSize[1:])
            # use int64 for bigger files
            offset = np.int64(2)*pos*voxels

            with open(os.path.join(self.fName,"data/data.bin"),"rb") as f:
                f.seek(offset)
                return np.fromfile(f,dtype="<u2",
                count=voxels).reshape(self.stackSize[1:])
        else:
            return None




class Img2dData(GenericData):
    """2d image data"""
    def __init__(self,fName = ""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self,fName, stackUnits = [1.,1.,1.]):
        if fName:
            try:
                self.img  = self.reshape_to_dim(np.array([imgutils.openImageFile(fName)]),
                                                include_time=True)
                self.stackSize = self.shape_to_dim(self.img.shape,
                                                   include_time=True)
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as Img2dData"%fName)
                return

            self.stackUnits = stackUnits
            self.fName = fName


    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            return self.img[pos]
        else:
            return None


class TiffData(GenericData):
    """a single 3d/4d/5d tiff data"""
    def __init__(self,fName = ""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self, fName, stackUnits = [1.,1.,1.]):
        if fName:
            try:
                data = np.squeeze(imgutils.read3dTiff(fName))

                if not data.ndim in [3,4,5]:
                    raise ValueError("in file %s: dada.ndim = %s (not 3 or 4)"%(fName,data.ndim))

                self.data = self.reshape_to_dim(data,include_time=True)
                #reshape it to e.g. (1,1,100,100,100)
                self.stackSize = self.data.shape

            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as TiffData"%fName)
                return

            self.stackUnits = stackUnits
            self.fName = fName


    def __getitem__(self,pos):
        if self.stackSize and self.fName:
            return self.data[pos]
        else:
            return None



class TiffFolderData(GenericData):
    """3d/4d tiff data inside a folder"""
    def __init__(self,fName = ""):
        GenericData.__init__(self, fName)
        self.fNames = []
        self.fName = ""
        self.load(fName)

    def load(self,fName, stackUnits = [1.,1.,1.]):
        if fName:
            self.fNames = glob.glob(os.path.join(fName,"*.tif"))
            if len(self.fNames) == 0:
                raise Exception("folder %s seems to be empty"%fName)
            else:
                self.fNames.sort()
            
            try:
                _tmp = imgutils.read3dTiff(self.fNames[0])
                self.stackSize = (len(self.fNames),)+self.shape_to_dim(_tmp.shape,
                                                   include_time=False)
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as TiffData"%self.fNames[0])
                return

            self.stackUnits = stackUnits
            self.fName = fName


    def __getitem__(self,pos):
        if len(self.fNames)>0 and pos<len(self.fNames):
            return self.reshape_to_dim(imgutils.read3dTiff(self.fNames[pos]),
                                           include_time = False)



# class TiffMultipleFiles(GenericData):
#     """3d/4d tiff data inside a folder"""
#     def __init__(self,fName = []):
#         GenericData.__init__(self, fName)
#         self.fNames = fName
#         self.load(fName)
#
#     def load(self,fNames, stackUnits = [1.,1.,1.]):
#         if fNames:
#             if len(self.fNames) == 0:
#                 raise Exception("filelist %s seems to be empty"%fName)
#
#             try:
#                 _tmp = imgutils.read3dTiff(self.fNames[0])
#                 self.stackSize = (len(self.fNames),)+ _tmp.shape
#             except Exception as e:
#                 print e
#                 raise Exception("couldnt open %s as TiffData"%self.fNames[0])
#                 return
#
#             self.stackUnits = stackUnits
#
#
#     def __getitem__(self,pos):
#         if len(self.fNames)>0 and pos<len(self.fNames):
#             return imgutils.read3dTiff(self.fNames[pos])

class NumpyData(GenericData):

    def __init__(self, data, stackUnits = [1.,1.,1.]):
        GenericData.__init__(self,"NumpyData")

        if not data.ndim in [3,4,5]:
            raise TypeError("data should be 3, 4 or 5 dimensional! shape = %s" %str(data.shape))

        self.data = self.reshape_to_dim(data.copy(), include_time=True)
        self.stackSize  = self.data.shape
        self.stackUnits = stackUnits

    def __getitem__(self,pos):
        return self.data[pos]


class DemoData(GenericData):
    def __init__(self, N = None):
        GenericData.__init__(self,"DemoData")
        self.load(N)

    def load(self,N = None):
        if N==None:
            logger.debug("loading precomputed demodata")
            self.data = imgutils.read3dTiff(absPath("../data/mpi_logo_80.tif")).astype(np.float32)
            N = 80
            self.stackSize = (10,1,N,N,N)
            self.fName = ""
            self.nT = 10
            self.stackUnits = (1,1,1)

        else:
            self.stackSize = (1,1,N,N,N)
            self.fName = ""
            self.nT = N
            self.stackUnits = (1,1,1)
            x = np.linspace(-1,1,N)
            Z,Y,X = np.meshgrid(x,x,x , indexing = "ij")
            R = np.sqrt(X**2+Y**2+Z**2)
            R2 = np.sqrt((X-.4)**2+(Y+.2)**2+Z**2)
            phi = np.arctan2(Z,Y)
            theta = np.arctan2(X,np.sqrt(Y**2+Z**2))
            u = np.exp(-500*(R-1.)**2)*np.sum(np.exp(-150*(-theta-t+.1*(t-np.pi/2.)*
                np.exp(-np.sin(2*(phi+np.pi/2.))))**2)
                for t in np.linspace(-np.pi/2.,np.pi/2.,10))*(1+Z)

            u2 = np.exp(-7*R2**2)
            self.data = (10000*(u + 2*u2)).astype(np.float32)
        self.data = self.data.reshape((1,)+self.data.shape)


    def sizeT(self):
        return self.nT

    def __getitem__(self,pos):
        return (self.data*np.exp(-.3*pos)).astype(np.float32)


class EmptyData(GenericData):
    def __init__(self):
        GenericData.__init__(self,"EmptyData")
        self.stackSize = (1,)*(self._DIM_WITHOUT_TIME+1)
        self.fName = ""
        self.nT = 1
        self.stackUnits = (1,1,1)
        self.data = np.zeros(self.stackSize).astype(np.uint16)


    def __getitem__(self,pos):
        return self.data



class CZIData(GenericData):
    """loads czi data files
    """

    def __init__(self,fName = None):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self,fName, stackUnits = [1.,1.,1.]):

        if fName:
            try:
                data = np.squeeze(imgutils.readCziFile(fName))

                if not data.ndim in [3,4,5]:
                    raise ValueError("in file %s: dada.ndim = %s (not 3 or 4)"%(fName,data.ndim))

                self.data = self.reshape_to_dim(data,include_time=True)
                self.stackSize = self.data.shape
                self.stackUnits = stackUnits
                self.fName = fName
            except Exception as e:
                print e
        
    def __getitem__(self,pos):
        return self.data[pos]



############################################################################
"""
this defines the qt enabled data models based on the GenericData structure

each dataModel starts a prefetching thread, that loads next timepoints in
the background
"""


class DataLoadThread(QtCore.QThread):
    """the prefetching thread for each data model"""
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
        import time

        self.stopped = False

        while not self.stopped:
            self._rwLock.lockForWrite()

            kset = set(self.data.keys())
            dkset = kset.difference(set(self.nset))
            dnset = set(self.nset).difference(kset)

            for k in dkset:
                del(self.data[k])

            self._rwLock.unlock()
            
            if dnset:
                logger.debug("preloading %s", list(dnset))
                for k in dnset:
                    newdata = self.dataContainer[k]
                    self._rwLock.lockForWrite()
                    self.data[k] = newdata
                    self._rwLock.unlock()
                    logger.debug("preload: %s",k)
                    try:
                        time.sleep(.0001)
                    except Exception as e:
                        print e

            # print "load thead dict length: ", len(self.data.keys())
            
            try:
                time.sleep(.0001)
            except Exception as e:
                print e


class DataModel(QtCore.QObject):
    """the data model
    emits signals when source/time position has changed
    """
    _dataSourceChanged = QtCore.pyqtSignal()
    _dataPosChanged = QtCore.pyqtSignal(int)

    _rwLock = QtCore.QReadWriteLock()

    def __init__(self, dataContainer = None, prefetchSize = 0):
        assert prefetchSize>=0
        
        super(DataModel,self).__init__()
        self.dataLoadThread = DataLoadThread(self._rwLock)
        self._dataSourceChanged.connect(self.dataSourceChanged)
        self._dataPosChanged.connect(self.dataPosChanged)
        if dataContainer:
            self.setContainer(dataContainer, prefetchSize)

    @classmethod
    def fromPath(self,fName, prefetchSize = 0):
        d = DataModel()
        d.loadFromPath(fName,prefetchSize)
        return d

    def setContainer(self,dataContainer = None, prefetchSize = 0):
        self.dataContainer = dataContainer
        self.prefetchSize = prefetchSize
        self.nset = [0]
        self.data = defaultdict(lambda: None)

        if self.dataContainer:
            self.stopDataLoadThread()
            self.dataLoadThread.load(self.nset,self.data, self.dataContainer)
            self.dataLoadThread.start(priority=QtCore.QThread.LowPriority)
            self._dataSourceChanged.emit()
            self.setPos(0)


    def __repr__(self):
        return "DataModel: %s \t %s"%(self.dataContainer.name,self.size())

    def dataSourceChanged(self):
        logger.debug("data source changed:\n%s",self)

    def dataPosChanged(self, pos):
        logger.debug("data position changed to %i",pos)



    def stopDataLoadThread(self):
        self.dataLoadThread.stopped = True

    def prefetch(self,pos):
        self._rwLock.lockForWrite()
        self.nset[:] = self.neighborhood(pos)
        self._rwLock.unlock()

    def sizeT(self):
        if self.dataContainer:
            return self.dataContainer.sizeT()

    def sizeC(self):
        if self.dataContainer:
            return self.dataContainer.sizeC()

    def size(self):
        if self.dataContainer:
            return self.dataContainer.size()

    def name(self):
        if self.dataContainer:
            return self.dataContainer.name

    def stackUnits(self):
        if self.dataContainer:
            return self.dataContainer.stackUnits

    def setPos(self,pos):
        if pos<0 or pos>=self.sizeT():
            raise IndexError("setPos(pos): %i outside of [0,%i]!"%(pos,self.sizeT()-1))
            return

        if not hasattr(self,"pos") or self.pos != pos:
            self.pos = pos
            self._dataPosChanged.emit(pos)
            self.prefetch(self.pos)


    def __getitem__(self,pos):
        # self._rwLock.lockForRead()
        if not hasattr(self,"data"):
            print "something is wrong in datamodel as its lacking a 'data' atttribute!"
            return None


        # switching of the prefetched version for now...
        # as for some instances there seems to be a race condition still
        
        if not self.data.has_key(pos):
            newdata = self.dataContainer[pos]
            self._rwLock.lockForWrite()
            self.data[pos] = newdata
            self._rwLock.unlock()

        self.prefetch(pos)

        #block until data was fetched....
        while not self.data.has_key(pos):
            time.sleep(1.e-4)

        return self.data[pos]

        # return self.dataContainer[pos]



    def neighborhood(self,pos):
        # FIXME mod stackSize!
        return np.arange(pos,pos+self.prefetchSize+1)%self.sizeT()

    def loadFromPath(self,fName, prefetchSize = 0):

        if  isinstance(fName,(tuple,list)):
            self.setContainer(TiffMultipleFiles(fName),prefetchSize)

        elif re.match(".*\.tif",fName):
            self.setContainer(TiffData(fName),prefetchSize = 0)
        elif re.match(".*\.(png|jpg|bmp)",fName):
            self.setContainer(Img2dData(fName),prefetchSize = 0)
        # elif re.match(".*\.h5",fName):
        #     self.setContainer(HDF5Data(fName),prefetchSize = 0)
        elif re.match(".*\.czi",fName):
            self.setContainer(CZIData(fName),prefetchSize = 0)
        elif os.path.isdir(fName):
            if os.path.exists(os.path.join(fName,"metadata.txt")):
                self.setContainer(SpimData(fName),prefetchSize)
            else:
                self.setContainer(TiffFolderData(fName),prefetchSize = prefetchSize)            



    
        

if __name__ == '__main__':


    d = DataModel(TiffFolderData("/home/martin/Data_new/Tomancak_Droso/volumes"), prefetchSize= 0)

    for i in np.random.randint(0,d.sizeT(),100):
        print i
        a = d[i]
