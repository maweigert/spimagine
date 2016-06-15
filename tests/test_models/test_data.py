"""


mweigert@mpi-cbg.de

"""
import numpy as np
from spimagine import DataModel
from glob import glob

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
    test_frompaths()