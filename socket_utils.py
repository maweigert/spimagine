

# import socket
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind(("localhost",8089))
# s.listen(5)


# while True:
#     c,a = s.accept()
#     # buf = c.recv(64)
#     # if len(buf)>0:
#     #     print buf
#     #     break



import socket
import time
import select
import numpy as np


import SocketServer
import threading


def empty_socket(sock):
    """remove the data present on the socket"""
    input = [sock]
    while 1:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready)==0: break
        for s in inputready: s.recv(4096)


def getEggData(s):

    while s.recv(1) != "[":
        pass
    tmp = "["

    while tmp.find(']') == -1:
        tmp += s.recv(1)

    empty_socket(s)

    try:
        q = eval("np.array(%s)"%tmp)
    except:
        q = np.array([1,0,0,0,0,0,0,0,0,0])
    return q



class EchoRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        while True:
            # Echo the back to the client
            data = self.request.recv(1024)
            if data == '':
                break
            self.request.send(data)



class StoppableTCPServer(SocketServer.TCPServer):

    allow_reuse_address = True

    def __init__(self, address, handler):

        SocketServer.TCPServer.__init__(self,("localhost",4000), handler)
        self.stopped = False

    def serve_forever(self):
        while not self.stopped:
            self.handle_request()


    def stop(self):
        self.stopped = True
        self.server_close()



class TCPServerThread(threading.Thread):

    def __init__(self, address):
        self.server = None;
        self.address = address
        self.stopped = False
        threading.Thread.__init__(self);

    def run(self):
        if self.server == None:
            self.server = StoppableTCPServer(self.address, EchoRequestHandler);
            self.server.serve_forever()




def startServer(address):
    tServe = TCPServerThread(address)
    # tServe.setDaemon(True)
    tServe.start()



class SendThread(threading.Thread):
    stopped = False
    def __init__(self, address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(address)

        threading.Thread.__init__(self);

    def run(self):
        while not self.stopped:
            self.socket.send("[0,0,0,0]")
            print "sending..."
            time.sleep(1)


def sendThread(address):
    t = SendThread(address)
    t.start()



def sendLoop(address):
    s = socket.socket()         # Create a socket object
    s.bind(address)        # Bind to the port

    s.listen(5)                 # Now wait for client connection.
    while True:
        c, addr = s.accept()     # Establish connection with client.
        print 'Got connection from', addr
        c.send('Thank you for connecting')
        c.close()                # Close the connection



class SendThread(threading.Thread):
    stopped = False
    def __init__(self, address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(address)

        threading.Thread.__init__(self);

    def run(self):
        while not self.stopped:
            self.socket.send("[0,0,0,0]")
            print "sending..."
            time.sleep(1)

if __name__ == '__main__':
    # import time

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect(("myers-mac-5.local",4444))


    while True:
        d = getEggData(s)
        print d
        # time.sleep(.001)

    # tServe = ServeThread(("localhost",4000))
    # tServe.setDaemon(True)
    # tServe.start()

    # time.sleep(1)


    # address = ("localhost",40003)

    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # s.connect(address)


    # # Send the data
    # # message = 'Hello, world'
    # # print 'Sending : "%s"' % message
    # # len_sent = s.send(message)
    # # Receive a response
    # # print 'Sending : "%s"' % message
    # # response = s.recv(2)
    # # print 'Received: "%s"' % response
