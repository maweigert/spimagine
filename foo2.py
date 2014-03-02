from Queue import Queue
from threading import Thread

q = Queue()
def consumer():
    while True:
        print sum(q.get())

def producer(data_source):
    for line in data_source:
        q.put( map(int, line.split()) )

Thread(target=producer, args=[["1 0 0 0 0 0","0 0 0 8 8 8 8 "]]).start()
for i in range(10):
    Thread(target=consumer).start()
