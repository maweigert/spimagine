

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
import select
import numpy as np

def readlines(sock, recv_buffer=4096, delim='\n'):
	buffer = ''
	data = True
	while data:
		data = sock.recv(recv_buffer)
		buffer += data
		while buffer.find(delim) != -1:
			line, buffer = buffer.split('\n', 1)
			yield line
	return




def empty_socket(sock):
    """remove the data present on the socket"""
    input = [sock]
    while 1:
        inputready, o, e = select.select(input,[],[], 0.0)
        if len(inputready)==0: break
        for s in inputready: s.recv(4096)


def getQuatFromSocket(s):

    
    while s.recv(1) != "[":
        pass

    # print "after"
    tmp = "["

    while tmp.find(']') == -1:
        tmp += s.recv(1)

    # empty_socket(s)

    return eval("np.array(%s)"%tmp)


if __name__ == '__main__':
    import time

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect(("myers-mac-5-wifi.mpi-cbg.de",4444))


    while True:
        d = getQuatFromSocket(s)
        if d[0]%100 == 0:
            print d[0]
