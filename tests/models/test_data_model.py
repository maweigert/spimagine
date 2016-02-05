from spimagine.models.data_model import DataModel, DemoData,SpimData, TiffData, NumpyData

import numpy as np

def test_demodata():
    m = DataModel(DemoData())
    print m
    for pos in (0,m.sizeT()-1):
        print pos, np.mean(m[pos])

    return m


def test_spimdata():
    d = SpimData("/Users/mweigert/Data/HisBTub_short")

    m = DataModel(d)
    print m
    for pos in (0,m.sizeT()-1):
        print pos, np.mean(m[pos])

    return m

def test_tiffdata():
    d = TiffData("/Users/mweigert/Data/flybrain.tif")

    m = DataModel(d)
    print m

    for pos in (0,m.sizeT()-1):
        print pos, np.mean(m[pos])

    return  m

def test_numpydata(shape = (10,100,100,100) ):
    d = NumpyData(np.ones(shape))


    m = DataModel(d)

    print m
    for pos in (0,m.sizeT()-1):
        print pos, np.mean(m[pos])

    return m

def test_frompath():
    m = DataModel.fromPath("/Users/mweigert/Data/HisBTub_short")
    print m
    m = DataModel.fromPath("/Users/mweigert/Data/flybrain.tif")
    print m

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
            

if __name__ == '__main__':
    
    # test_data_sets()
    m = test_demodata()
    m = test_spimdata()
    m = test_tiffdata()
    m = test_numpydata((11,12,13))
    m = test_numpydata((10,11,12,13))
    m = test_numpydata((9,10,11,12,13))

    # test_speed()

    test_frompath()

    
            
