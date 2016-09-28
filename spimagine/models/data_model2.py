"""
the (Qt) data models for usage in the gui frame

generic containers are defined for BScope Spim Data (SpimData)
and Tiff files (TiffData).
Extend it if you want to and change the DataLoadModel.chooseContainer to
accept it via drag/drop

at the end every data model is assumed to be 5d (Time,Channel,Z,Y,X)

author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import os
import numpy as np
import re
import glob
from PyQt4 import QtCore
from collections import defaultdict

import logging
logger = logging.getLogger(__name__)

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
The next classes define simple 5d Data Structures that implement the interface
given by GenericData
"""


class GenericData(object):
    """abstract base class for 5d data

    if you wanna subclass it, just overwrite self.size() and self.__getitem__()

    """
    dataFileError = Exception("not a valid file")

    def __init__(self, name=""):
        self.stackSize = None
        self.stackUnits = None
        self.name = name

    # def setStackSize(self, stackSize):
    #     self.stackSize  = list(stackSize)

    def sizeT(self):
        return self.size()[0]

    def sizeC(self):
        return self.size()[1]

    def size(self):
        return self.stackSize

    def __getitem__(self, pos):
        raise NotImplementedError("should be overwritten")

    # #this should be override by every derived class
    # def _get_single_item(self,i):
    #     return None
    #
    # def __getslice__(self, i, j):
    #     return self.__getitem__(slice(i, j))
    #
    # def __getitem__(self,i):
    #     if isinstance(key, slice):
    #         return [self.list[i] for i in xrange(key.start, key.stop, key.step)]
    #     else:
    #         self._get_single_item(i)


class SpimData(GenericData):
    """data class for spim data saved in folder fName
    fname/
    |-- metadata.txt
    |-- data/
       |--data.bin
       |--index.txt
    """

    def __init__(self, fName=""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self, fName):
        if fName:
            try:
                # no multichannel for now...
                stackSize_4d = imgutils.parseIndexFile(os.path.join(fName, "data/index.txt"))
                self.stackSize = tuple(stackSize_4d[:1]+[1,]+stackSize_4d[1:])
                self.stackUnits = imgutils.parseMetaFile(os.path.join(fName, "metadata.txt"))
                self.fName = fName
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as SpimData"%fName)

            try:
                # try to figure out the dimension of the dark frame stack
                darkSizeZ = os.path.getsize(os.path.join(self.fName, "data/darkstack.bin"))/2/self.stackSize[-2]/ \
                            self.stackSize[-1]
                with open(os.path.join(self.fName, "data/darkstack.bin"), "rb") as f:
                    self.darkStack = np.fromfile(f, dtype="<u2").reshape(
                        [darkSizeZ, self.stackSize[-2], self.stackSize[-1]])

            except Exception as e:
                logger.warning("couldn't find darkstack (%s)", e)

    def __getitem__(self, pos):
        if self.stackSize and self.fName:
            if pos<0 or pos>=self.stackSize[0]:
                raise IndexError("0 <= pos <= %i, but pos = %i"%(self.stackSize[0]-1, pos))

            pos = max(0, min(pos, self.stackSize[0]-1))
            voxels = np.prod(self.stackSize[1:])
            # use int64 for bigger files
            offset = np.int64(2)*pos*voxels

            with open(os.path.join(self.fName, "data/data.bin"), "rb") as f:
                f.seek(offset)
                return np.fromfile(f, dtype="<u2",
                                   count=voxels).reshape(self.stackSize[1:])
        else:
            return None


class Img2dData(GenericData):
    """2d image data"""

    def __init__(self, fName=""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self, fName, stackUnits=[1., 1., 1.]):
        if fName:
            try:
                self.img = np.array([imgutils.openImageFile(fName)])
                self.stackSize = (1,)+self.img.shape
            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as Img2dData"%fName)
                return

            self.stackUnits = stackUnits
            self.fName = fName

    def __getitem__(self, pos):
        if self.stackSize and self.fName:
            return self.img
        else:
            return None


class TiffData(GenericData):
    """3d tiff data"""

    def __init__(self, fName=""):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self, fName, stackUnits=[1., 1., 1.]):
        if fName:
            try:
                data = np.squeeze(imgutils.read3dTiff(fName))

                if not data.ndim in [3, 4, 5]:
                    raise ValueError("in file %s: dada.ndim = %s (not 3 ,4 or 5)"%(fName, data.ndim))

                self.stackSize = (1,)*(5-data.ndim) + data.shape


                self.data = data.reshape(self.stackSize)

            except Exception as e:
                print e
                self.fName = ""
                raise Exception("couldnt open %s as TiffData"%fName)
                return

            self.stackUnits = stackUnits
            self.fName = fName

    def __getitem__(self, pos):
        if self.stackSize and self.fName:
            return self.data[pos]
        else:
            return None



class TiffMultipleFiles(GenericData):
    """multiple tiff files"""

    def __init__(self, fNames=[]):
        GenericData.__init__(self, fNames)
        self.fNames = fNames
        self.load(fNames)

    def load(self, fNames, stackUnits=[1., 1., 1.]):
        if fNames:
            if len(self.fNames)==0:
                raise Exception("filelist %s seems to be empty"%fName)

            try:
                _tmp = imgutils.read3dTiff(self.fNames[0])
                if not _tmp.ndim in [3, 4]:
                    raise ValueError("files in %s: dada.ndim = %s (not 3 or 4)"%(fName, _tmp.ndim))

                self.stackSize = (len(self.fnames),)*(5-_tmp.ndim) + _tmp.shape

            except Exception as e:
                print e
                raise Exception("couldnt open %s as TiffData"%self.fNames[0])
                return

            self.stackUnits = stackUnits

    def __getitem__(self, pos):
        if len(self.fNames)>0 and pos<len(self.fNames):
            return imgutils.read3dTiff(self.fNames[pos]).reshape(self.stackSize[1:])


class TiffFolderData(TiffMultipleFiles):
    """3d tiff data inside a folder"""

    def __init__(self, fName = ""):
        if fname:
            fnames = glob.glob(os.path.join(fName, "*.tif"))
        else:
            fnames = []
        TiffMultipleFiles.__init__(self, fNames)



class NumpyData(GenericData):
    def __init__(self, data, stackUnits=[1., 1., 1.]):
        GenericData.__init__(self, "NumpyData %s"%(data.shape,))

        if not data.ndim in [3,4,5]:
            raise TypeError("data should be 3, 4 or 5 dimensional! shape = %s" %str(data.shape))

        self.stackSize  = (1,)*(5-data.ndim) + data.shape
        self.data = data.copy().reshape(self.stackSize)

        self.stackUnits = stackUnits

    def __getitem__(self, pos):
        return self.data[pos]


class DemoData(GenericData):
    def __init__(self, N=None):
        GenericData.__init__(self, "DemoData")
        self.load(N)

    def load(self, N=None):
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

    def __getitem__(self, pos):
        return (self.data*np.exp(-.3*pos)).astype(np.float32)


class EmptyData(GenericData):
    def __init__(self):
        GenericData.__init__(self, "EmptyData")
        self.stackSize = (1, )*5
        self.fName = ""
        self.stackUnits = (1, 1, 1)
        self.data = np.zeros((1,)*5).astype(np.uint16)


    def __getitem__(self, pos):
        return self.data


# class HDF5Data(GenericData):
#     """loads hdf5 data files
#     """

#     def __init__(self,fName = None, key = None ):
#         GenericData.__init__(self, fName)
#         self.load(fName, key)

#     def load(self,fName, key = None, stackUnits = [1.,1.,1.]):
#         if fName:
#             with h5py.File(fName,"r") as f:
#                 if len(f.keys())==0 :
#                     raise KeyError("no valid key found in file %s"%fName)
#                 if key is None:
#                     key = f.keys()[0]
#                 self.data = np.asarray(f[key][:]).copy()
#                 self.stackSize = (1,)+ self.data.shape
#                 self.stackUnits = stackUnits
#                 self.fName = fName

#     def __getitem__(self,pos):
#         return self.data

class CZIData(GenericData):
    """loads czi data files
    """

    def __init__(self, fName=None):
        GenericData.__init__(self, fName)
        self.load(fName)

    def load(self, fName, stackUnits=[1., 1., 1.]):

        if fName:
            try:
                data = np.squeeze(imgutils.readCziFile(fName))

                if not data.ndim in [3, 4]:
                    raise ValueError("in file %s: dada.ndim = %s (not 3 or 4)"%(fName, data.ndim))

                if data.ndim==3:
                    self.stackSize = (1,)+data.shape
                else:
                    self.stackSize = data.shape
                self.data = data
                self.stackUnits = stackUnits
                self.fName = fName
            except Exception as e:
                print e

    def __getitem__(self, pos):
        if self.data.ndim==3:
            return self.data
        else:
            return self.data[pos]


############################################################################
"""
this defines the qt enabled data models based on the GenericData structure

each dataModel starts a prefetching thread, that loads next timepoints in
the background
"""


class DataLoadThread(QtCore.QThread):
    """the prefetching thread for each data model"""

    def __init__(self, _rwLock, nset=set(), data=None, dataContainer=None):
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
                del (self.data[k])

            self._rwLock.unlock()

            if dnset:
                logger.debug("preloading %s", list(dnset))
                for k in dnset:
                    newdata = self.dataContainer[k]
                    self._rwLock.lockForWrite()
                    self.data[k] = newdata
                    self._rwLock.unlock()
                    logger.debug("preload: %s", k)
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

    def __init__(self, dataContainer=None, prefetchSize=0):
        assert prefetchSize>=0

        super(DataModel, self).__init__()
        self.dataLoadThread = DataLoadThread(self._rwLock)
        self._dataSourceChanged.connect(self.dataSourceChanged)
        self._dataPosChanged.connect(self.dataPosChanged)
        if dataContainer:
            self.setContainer(dataContainer, prefetchSize)

    @classmethod
    def fromPath(self, fName, prefetchSize=0):
        d = DataModel()
        d.loadFromPath(fName, prefetchSize)
        return d

    def setContainer(self, dataContainer=None, prefetchSize=0):
        self.dataContainer = dataContainer
        self.prefetchSize = prefetchSize
        self.nset = [0]
        self.data = defaultdict(lambda: None)

        if self.dataContainer:
            self.stopDataLoadThread()
            self.dataLoadThread.load(self.nset, self.data, self.dataContainer)
            self.dataLoadThread.start(priority=QtCore.QThread.LowPriority)
            self._dataSourceChanged.emit()
            self.setPos(0)

    def __repr__(self):
        return "DataModel: %s \t %s"%(self.dataContainer.name, self.size())

    def dataSourceChanged(self):
        logger.debug("data source changed:\n%s", self)

    def dataPosChanged(self, pos):
        logger.debug("data position changed to %i", pos)

    def stopDataLoadThread(self):
        self.dataLoadThread.stopped = True

    def prefetch(self, pos):
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

    def setPos(self, pos):
        if pos<0 or pos>=self.sizeT():
            raise IndexError("setPos(pos): %i outside of [0,%i]!"%(pos, self.sizeT()-1))
            return

        if not hasattr(self, "pos") or self.pos!=pos:
            self.pos = pos
            self._dataPosChanged.emit(pos)
            self.prefetch(self.pos)

    def __getitem__(self, pos):
        # self._rwLock.lockForRead()
        if not hasattr(self, "data"):
            print "something is wrong in datamodel as its lacking a 'data' atttribute!"
            return None

        # switching of the prefetched version for now...
        # as for some instances there seems to be a race condition still

        self._rwLock.lockForWrite()

        if not self.data.has_key(pos):
            newdata = self.dataContainer[pos]
            self.data[pos] = newdata
        else:
            newdata = self.data[pos]

        self._rwLock.unlock()

        self.prefetch(pos)
        return newdata

    def neighborhood(self, pos):
        # FIXME mod stackSize!
        return np.arange(pos, pos+self.prefetchSize+1)%self.sizeT()

    def loadFromPath(self, fName, prefetchSize=0):

        if isinstance(fName, (tuple, list)):
            self.setContainer(TiffMultipleFiles(fName), prefetchSize)

        elif re.match(".*\.tif", fName):
            self.setContainer(TiffData(fName), prefetchSize=0)
        elif re.match(".*\.(png|jpg|bmp)", fName):
            self.setContainer(Img2dData(fName), prefetchSize=0)
        # elif re.match(".*\.h5",fName):
        #     self.setContainer(HDF5Data(fName),prefetchSize = 0)
        elif re.match(".*\.czi", fName):
            self.setContainer(CZIData(fName), prefetchSize=0)
        elif os.path.isdir(fName):
            if os.path.exists(os.path.join(fName, "metadata.txt")):
                self.setContainer(SpimData(fName), prefetchSize)
            else:
                self.setContainer(TiffFolderData(fName), prefetchSize=prefetchSize)



if __name__=='__main__':

    # test_data_sets()
    # test_spimdata()

    # test_tiffdata()
    # test_numpydata()

    # test_speed()

    # test_frompath()


    d = DataModel(TiffFolderData("/home/martin/Data_new/Tomancak_Droso/volumes"), prefetchSize=0)

    for i in np.random.randint(0, d.sizeT(), 100):
        print i
        a = d[i]
