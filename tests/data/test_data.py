"""


mweigert@mpi-cbg.de

"""
from spimagine import DataModel, TiffData, SpimData

if __name__ == '__main__':


    d = TiffData("/Users/mweigert/Data/droso_test.tif")

    d2 = SpimData("/Users/mweigert/Data/HisBTub")

    print d.size(), d.sizeC(), d[0].shape
    print d2.size(), d2.sizeC(), d2[0].shape



