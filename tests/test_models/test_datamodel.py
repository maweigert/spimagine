"""
mweigert@mpi-cbg.de
"""
import numpy as np
from spimagine import DataModel, SpimData, TiffData, NumpyData


#
# def test_spimdata():
#     d = SpimData("/Users/mweigert/Data/HisBTub_short")
#
#     m = DataModel(d)
#     print m
#     for pos in range(m.sizeT()):
#         print pos
#         print np.mean(m[pos])
#     return m
#
#
#
# def test_numpydata():
#     d = NumpyData(np.ones((10, 100, 100, 100)))
#
#     m = DataModel(d)
#
#     print m
#     for pos in range(m.sizeT()):
#         print pos
#         print np.mean(m[pos])
#
#


def test_speed():
    import time

    fName = "/Users/mweigert/Data/Drosophila_07"

    t = []
    d = DataModel.fromPath(fName, 1)

    for i in range(100):
        print i

        if i%10==0:
            a = d[i/10]

        time.sleep(.01)
        t.append(time.time())



def test_frompaths():
    from glob import glob
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


    # test_spimdata()
    #test_tiffdata()
    # test_numpydata()
    #test_speed()


    test_frompaths()
