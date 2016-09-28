"""
mweigert@mpi-cbg.de
"""
import numpy as np
from spimagine import DataModel, SpimData, TiffData

from spimagine.models.data_model2 import DataModel, SpimData, TiffData, NumpyData


def test_spimdata():
    d = SpimData("/Users/mweigert/Data/HisBTub_short")

    m = DataModel(d)
    print m
    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])
    return m

def test_tiffdata():
    d = TiffData("/Users/mweigert/Data/droso_test.tif")

    m = DataModel(d)
    print m
    for pos in range(m.sizeT()):
        print pos
        print np.mean(m[pos])

    return m


def test_numpydata():
    d = NumpyData(np.ones((10, 4,100, 100, 100)))

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

    fName = "/Users/mweigert/Data/Drosophila_full"

    t = []
    d = DataModel.fromPath(fName, 1)

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
              "test_data/meep.h5",
              "test_data/retina.czi"
              ]

    for fName in fNames:
        try:
            d = DataModel.fromPath(fName)
            print fName, d[0].shape
        except Exception as e:
            print e
            print "ERROR    could not open %s"%fName



def test_frompaths():
    fnames = glob("/Users/mweigert/python/spimagine/tests/data/*")
    if len(fnames)==0:
        raise ValueError("could not find any test data!")

    print fnames
    for f in fnames:
        print f
        d = DataModel.fromPath(f)
        print d
        for i in np.random.randint(0,d.sizeT(),10):
            print i
            a =  d[i]


if __name__ == '__main__':


    #m = test_spimdata()
    m = test_tiffdata()

    test_numpydata()
