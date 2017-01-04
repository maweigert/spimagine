"""
mweigert@mpi-cbg.de
"""
from __future__ import absolute_import, print_function
import os
import numpy as np
from spimagine import DataModel, SpimData, TiffData, NumpyData
from six.moves import range


def rel_path(name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__),name))


def test_spimdata():
    d = SpimData(rel_path("../data/spimdata"))

    m = DataModel(d)
    print(m)
    for pos in range(m.sizeT()):
        print(pos)
        print(np.mean(m[pos]))
    return m



def test_numpydata():
    d = NumpyData(np.ones((10, 100, 100, 100)))

    m = DataModel(d)

    print(m)
    for pos in range(m.sizeT()):
        print(pos)
        print(np.mean(m[pos]))




def test_speed():
    import time

    fName = rel_path("../data/spimdata")

    t = []
    d = DataModel.fromPath(fName, 1)

    for i in range(100):
        print(i)

        if i%10==0:
            a = d[i//10]

        time.sleep(.01)
        t.append(time.time())



def test_frompaths():
    from glob import glob
    fnames = glob(rel_path("../data/*"))
    if len(fnames)==0:
        raise ValueError("could not find any test data!")

    print(fnames)
    for f in fnames:
        print(f)
        d = DataModel.fromPath(f)
        print(d)
        for i in np.random.randint(0,d.sizeT(),10):
            print(i)
            a =  d[i]


def test_folder():
    d = DataModel.fromPath(rel_path("../data/tiffstacks"))
    print(d)



def test_tiffdata():
    d = TiffData(rel_path("../data/flybrain.tif"))

    m = DataModel(d)
    print(m)
    for pos in range(m.sizeT()):
        print(pos)
        print((np.mean(m[pos])))




if __name__ == '__main__':



    # test_tiffdata()
    # test_numpydata()
    #
    # test_spimdata()
    test_speed()

    # test_frompaths()
    # test_folder()
