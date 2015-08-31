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


def getTiffSize(fName):
    img = Image.open(fName, 'r')
    depth = 0
    while True:
        try:
            img.seek(depth)
        except Exception as e:
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

            try:
                # try to figure out the dimension of the dark frame stack
                darkSizeZ = os.path.getsize(os.path.join(self.fName,"data/darkstack.bin"))/2/self.stackSize[2]/self.stackSize[3]
                print darkSizeZ
                with open(os.path.join(self.fName,"data/darkstack.bin"),"rb") as f:
                    self.darkStack = np.fromfile(f,dtype="<u2").reshape([darkSizeZ,self.stackSize[2],self.stackSize[3]])

            except Exception as e:
                print e
                print "couldn't find darkstack"
                

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
            # use int64 for bigger files
            offset = np.int64(2)*pos*voxels

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


def test_spimLoader():
    fName = "/Users/mweigert/Data/SIM/SIM_Hela3_18/"

    data = SpimData(fName)


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


    fName = "/Users/mweigert/Data/SIM/DarkTest"

    data = SpimData(fName)
