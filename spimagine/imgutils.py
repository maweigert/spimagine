import os
import numpy as np
from PIL import Image
import re

def read3dTiff_old(fName):
    img = Image.open(fName)
    i = 0
    data = []
    while True:
        try:
            img.seek(i)
        except EOFError:
            break
        data.append(np.asarray(img))
        i += 1

    return np.array(data)

def read3dTiff(fName):
    from libtiff import TIFFfile

    """ still has problems with matlab created tif"""
    tif = TIFFfile(fName)
    data = tif.get_samples()[0][0]
    return data

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


def absPath(s):
    return os.path.join(os.path.dirname(__file__),s)


def parseIndexFile(fname):
    """
    returns (t,z,y,z) dimensions of a spim stack
    """
    try:
        lines = open(fname).readlines()
    except IOError:
        print "could not open and read ",fname
        return None

    items = lines[0].replace("\t",",").split(",")
    try:
        stackSize = [int(i) for i in items[-4:-1]] +[len(lines)]
    except Exception as e:
        print e
        print "couldnt parse ", fname
        return None
    stackSize.reverse()
    return stackSize


def parseMetaFile(fName):
    """
    returns pixelSizes (dx,dy,dz)
    """

    with open(fName) as f:
        s = f.read()
        try:
            z1 = np.float(re.findall("StartZ.*",s)[0].split("\t")[2])
            z2 = np.float(re.findall("StopZ.*",s)[0].split("\t")[2])
            zN = np.float(re.findall("NumberOfPlanes.*",s)[0].split("\t")[2])

            return (.162,.162, (1.*z2-z1)/zN)
        except Exception as e:
            print e
            print "coulndt parse ", fName
            return (1.,1.,1.)



def fromSpimFolder(fName,dataFileName="data/data.bin",indexFileName="data/index.txt",pos=0,count=1):
    stackSize = parseIndexFile(os.path.join(fName,indexFileName))

    if stackSize:
        # clamp to pos to stackSize
        pos = min(pos,stackSize[0]-1)
        pos = max(pos,0)

        if count>0:
            stackSize[0] = min(count,stackSize[0]-pos)
        else:
            stackSize[0] = max(0,stackSize[0]-pos)

        with open(os.path.join(fName,dataFileName),"rb") as f:
            f.seek(2*pos*np.prod(stackSize[1:]))
            return np.fromfile(f,dtype="<u2",
                               count=np.prod(stackSize)).reshape(stackSize)


def fromSpimFile(fName,stackSize):
    return np.fromfile(fName,dtype="<u2").reshape(stackSize)




if __name__ == '__main__':
    from time import time
    t = time()
    d = getTiffSize_old("/Users/mweigert/Data/Wing_cropped.tif")

    print d
    print time()-t

    t = time()
    d = getTiffSize("/Users/mweigert/Data/Wing_cropped.tif")
    print d
    print time()-t



