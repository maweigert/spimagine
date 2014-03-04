
import SpimUtils
from PyOCL import *
from numpy import *

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL

import Queue
from volume_render import VolumeRenderer

isAppRunning = True
dataQueue = Queue.Queue()


class DataLoadThread(QtCore.QThread):
    def __init__(self, dataQueue, size = 6):
        self.size = size
        self.queue = dataQueue
        self.fName = "../Data/Drosophila_07"
        QtCore.QThread.__init__(self)

    def run(self):
        self.pos, self.nT  = 0, 100
        dpos = 1
        while isAppRunning:
            if self.queue.qsize()<self.size:
                # print "fetching data at pos %i"%(self.pos)
                try:
                    d = SpimUtils.fromSpimFolder(self.fName,pos=self.pos,
                                                 count=1)[0,:,:,:]
                    self.queue.put(d)
                except Exception as e:
                    print "couldnt open: ", self.fName
                    print e
                self.pos += dpos
                if self.pos>self.nT-1:
                    self.pos = self.nT-1
                    dpos = -1
                if self.pos<0:
                    self.pos = 0
                    dpos = 1




if __name__ == '__main__':
    from time import time

    dev = OCLDevice()

    fName = "../Data/Drosophila_07"
    d = SpimUtils.fromSpimFolder(fName,count=1)[0,:,:,:].astype(uint16)
    img = dev.createImage(d.shape[::-1])

    dataLoadThread = DataLoadThread(dataQueue,size = 4)
    dataLoadThread.start(priority=QtCore.QThread.HighPriority)

    rend = VolumeRenderer((600,600))
    rend.set_dataFromFolder("../Data/Drosophila_07")

    t = time()
    for i in range(100):
        # a = d.astype(uint16)
        d = dataQueue.get()
        dev.writeImage(img,d)
        # rend.dev.writeImage(rend.dataImg,d)
        # rend.update_data(d)

        # rend.render(render_func="max_proj")

        # print i


    print (time()-t)
    # N = 100



    # fName = "../Data/Drosophila_07"
    # d = fromSpimFolder(fName,count=1)[0,:,:,:].astype(uint16)
    # img = dev.createImage(d.shape[::-1])


    # stackSize = parseIndexFile(os.path.join(fName,"data/index.txt"))

    # t = time()
    # for i in range(N):

    #     d = fromSpimFolder(fName,pos=0,count=1)[0,:,:,:].astype(uint16)

    #     # dev.writeImage(img,d)

    # print (1.*time()-t)/N

    # # print time()-t
    # print N*d.nbytes/((1.*time()-t))/1e6," MB/s"
