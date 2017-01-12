from __future__ import absolute_import, print_function

import logging
logger = logging.getLogger(__name__)


import os
import numpy as np
import re
from PIL import Image


import warnings 

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from spimagine.lib.tifffile import TiffFile, imsave, imread
    from spimagine.lib.czifile import CziFile



def _read3dTiff_PIL(fName):
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
    return imread(fName)


def write3dTiff(data,fName):
    imsave(fName,data)

        
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


def readCziFile(fName):
    with CziFile(fName)  as f:
        return np.squeeze(f.asarray())
            


def parseIndexFile(fname):
    """
    returns (t,z,y,z) dimensions of a spim stack
    """
    try:
        lines = open(fname).readlines()
    except IOError:
        print("could not open and read ",fname)
        return None

    items = lines[0].replace("\t",",").split(",")
    try:
        stackSize = [int(i) for i in items[-4:-1]] +[len(lines)]
    except Exception as e:
        print(e)
        print("couldnt parse ", fname)
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

            return (.162,.162, (1.*z2-z1)/(zN-1.))
        except Exception as e:
            print(e)
            print("coulndt parse ", fName)
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

            t = time()
            ds.append(func(fName))
            print("%s\ntime: %.2f ms"%(func.__name__, 1000.*(time()-t)))

        assert np.allclose(*ds)



def createSpimFolder(fName,data = None,
                     stackSize= [10,10,32,32],
                     stackUnits = (.162,.162,.162)):
    if not os.path.exists(fName):
        os.makedirs(fName)
    if not os.path.exists(os.path.join(fName,"data")):
        os.makedirs(os.path.join(fName,"data"))



    if not data is None:
        stackSize = data.shape
        datafName = os.path.join(fName,"data/data.bin")
        with open(datafName,"wa") as f:
                data.astype(np.uint16).tofile(f)

    Nt,Nz,Ny,Nx = stackSize

    indexfName = os.path.join(fName,"data/index.txt")
    with open(indexfName,"w") as f:
        for i in range(Nt):
            f.write("%i\t0.0000\t1,%i,%i,%i\t0\n"%(i,Nx,Ny,Nz))

    metafName = os.path.join(fName,"metadata.txt")
    with open(metafName,"w") as f:
        f.write("timelapse.NumberOfPlanes\t=\t%i\t0\n"%Nz)
        f.write("timelapse.StartZ\t=\t0\t0\n")
        f.write("timelapse.StopZ\t=\t%.2f\t0\n"%(stackUnits[2]*(Nz-1.)))


        
def test_czi():
    d = readCziFile("test_data/retina.czi")
    return d
    
if __name__ == '__main__':

    # test_tiff()

    d = test_czi()
