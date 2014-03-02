
from time import time, sleep
import numpy as np

import threading
import Queue
import SpimUtils

counter = 0

dataQueue = Queue.Queue()

isRunning = True

class LoadThread(threading.Thread):
    def __init__(self,size=2):
        self.size = size
        self.queue = dataQueue
        threading.Thread.__init__(self);

    def run(self):
        while isRunning:
            if self.queue.qsize()<self.size:
                print "fetching data"
                self.queue.put(SpimUtils.fromSpimFolder("Example",pos=1,count=1))


if __name__ == '__main__':


    t = LoadThread(2)
    t.start()


    for i in range(4):
        sleep(.1)
        d = dataQueue.get()
        print d.shape
        print dataQueue.qsize()
        dataQueue.task_done()

    isRunning = False
