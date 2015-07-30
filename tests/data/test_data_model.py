#!/usr/bin/env python


import logging
logger = logging.getLogger(__name__)


from spimagine.data_model import DataModel, SpimData


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

def test_spimdata():
    d = SpimData("data/Drosophila_Single")

    m = DataModel(d)
    print m
    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])

    return d

def test_tiffdata():
    d = TiffData("/Users/mweigert/Data/droso_test.tif")

    m = DataModel(d)
    print m
    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])

    return d

def test_numpydata():
    d = NumpyData(np.ones((10,100,100,100)))


    m = DataModel(d)

    print m
    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])

def test_frompath():
    m = DataModel.fromPath("/Users/mweigert/Data/HisGFP")
    m = DataModel.fromPath("/Users/mweigert/Data/droso_test.tif")


def test_speed():
    import time

    fName  = "/Users/mweigert/Data/Drosophila_full"

    t = []
    d = DataModel.fromPath(fName,1)

    for i in range(100):
        print i

        if i%10==0:
            a = d[i/10]


        time.sleep(.1)
        t.append(time.time())


def test_data_sets():
    fNames = ["test_data/Drosophila_Single",
              "test_data/HisStack_uint16_0000.tif",
              "test_data/HisStack_uint8_0000.tif",
              # "test_data/meep.h5",
              "test_data/retina.czi"
          ]

    
    for fName in fNames:
        d = DataModel.fromPath(fName)
        print fName, d[0].shape

    
        

if __name__ == '__main__':

    # test_data_sets()
    test_spimdata()

    # d = test_tiffdata()


    # test_numpydata()

    # test_speed()

    # test_frompath()


    # d = Img2dData("/Users/mweigert/Data/test_images/actin.jpg")

