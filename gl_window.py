import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from OpenGL import GLU
from OpenGL.GL import *

from PyOCL import *
from volume_render import *
import SpimUtils

from numpy import *
import time
import Queue
import socket
from scipy.misc import imsave


modelView = scaleMat()
quatRot = array([1,0,0,0])
zoomVal = 1.
isAppRunning = True
isSocket = False


def getEggData(s):
    while s.recv(1) != "[":
        pass
    tmp = "["
    while tmp.find(']') == -1:
        tmp += s.recv(1)


    # empty_socket(s)
    try:
        q = eval("array(%s)"%tmp)
    except Exception as e:
        print e
        q = np.array([1,0,0,0,0,0,0,0,0,0])

    return q

class ModelViewThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        global isSocket
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # soc.connect(("myers-mac-5.local",4444))
            soc.connect(("localhost",4444))
            isSocket = True
            print "connected"
        except Exception as e:
            print e
            print "not connected"
            soc = None

        # soc = 1
        global modelView
        global zoomVal
        global quatRot

        t = 0
        while isSocket and isAppRunning:
            try:
                eggData = getEggData(soc)
                a,b,c,d = eggData[:4]
                q = array([a,b,d,-c])

                quatRot =  .93*quatRot + .07 * q

                buttonPressVal = eggData[8]/255.
                acceleratVal = sum(abs(eggData[4:7]))
                if buttonPressVal>.5:
                    zoomVal = min(2.,zoomVal*(1+.01*buttonPressVal))

                if acceleratVal>1.:
                    zoomVal = max(1.,zoomVal*(1-.01*acceleratVal))


                modelView = quaternionToRotMat(quatRot)
            except Exception as e:
                print e
                print "couldnt create modelview from quaternion"




class DataLoadThread(QtCore.QThread):
    def __init__(self, dataQueue, size = 6):
        self.size = size
        self.queue = dataQueue
        # self.fName = "../Data/Drosophila_05"
        self.fName = ""
        QtCore.QThread.__init__(self)

    def run(self):
        self.pos, self.nT  = 0, 1
        dpos = 1
        while isAppRunning:
            if self.queue.qsize()<self.size:
                print "fetching data at pos %i"%(self.pos)
                try:
                    d = SpimUtils.fromSpimFolder(self.fName,pos=self.pos,
                                                 count=1)[0,:,:,:]
                    self.queue.put(d)
                except:
                    print "couldnt open ", self.fName
                self.pos += dpos
                if self.pos>self.nT-1:
                    self.pos = self.nT-1
                    dpos = -1
                if self.pos<0:
                    self.pos = 0
                    dpos = 1


    def dataFolderChanged(self,fName):
        self.fName = str(fName)

        self.queue.queue.clear()
        stackSize = SpimUtils.parseIndexFile(
            os.path.join(self.fName,"data/index.txt"))
        self.pos, self.nT = 0, stackSize[0]
        print "changed: ",stackSize, fName


# class CLLoadThread(QtCore.QThread):
#     def __init__(self, myqueue, dev, size = 6):
#         self.size = size
#         self.dev = dev
#         self.queue = myqueue
#         self.fName = "../Data/Drosophila_Single"
#         QtCore.QThread.__init__(self)

#     def run(self):
#         self.pos, self.nT  = 0, 1
#         dpos = 1

#         while isAppRunning:
#             if self.queue.qsize()<self.size :
#                 print "fetching data at pos %i"%(self.pos)
#                 try:
#                     d = SpimUtils.fromSpimFolder(self.fName,pos=self.pos,
#                                                  count=1)[0,:,:,:]
#                     dataImg = self.dev.createImage(d.shape[::-1],
#                                                    mem_flags = cl.mem_flags.READ_ONLY)
#                     self.dev.writeImage(dataImg,d.astype(uint16))
#                     self.queue.put(dataImg)
#                 except:
#                     print "couldnt open ", self.fName
#                 self.pos += dpos
#                 if self.pos>self.nT-1:
#                     self.pos = self.nT-1
#                     dpos = -1
#                 if self.pos<0:
#                     self.pos = 0
#                     dpos = 1


    # def dataFolderChanged(self,fName):
    #     self.fName = str(fName)

    #     self.queue.queue.clear()
    #     stackSize = SpimUtils.parseIndexFile(
    #         os.path.join(self.fName,"data/index.txt"))
    #     self.pos, self.nT = 0, stackSize[0]
    #     print "changed: ",stackSize, fName


class GLWidget(QtOpenGL.QGLWidget):
    dataFolderChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        self.parent = parent
        super(GLWidget,self).__init__(parent)

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer((800,800),useDevice=1)
        self.output = zeros([self.renderer.height,self.renderer.width],dtype=uint8)
        self.modelViewThread = ModelViewThread()
        self.modelViewThread.start()

        self.dataQueue = Queue.Queue()
        self.dataLoadThread = DataLoadThread(self.dataQueue,size = 4)
        self.dataLoadThread.start(priority=QtCore.QThread.HighPriority)

        self.dataFolderChanged.connect(self.dataLoadThread.dataFolderChanged)

        self.count = 0
        self.scale = 1.
        self.t = time.time()
        self.set_dataFromFolder("../Data/Drosophila_05")


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile().toLocal8Bit().data()
            print path
            self.set_dataFromFolder(path)


    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(0, 0,  0))
        glEnable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT,1)
        glTexParameterf (GL_TEXTURE_2D,
                            GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameterf (GL_TEXTURE_2D,
                            GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)

        self.width , self.height = 200, 200

    def set_data(self,data):
        self.renderer.set_data(data)


    def set_dataFromFolder(self,fName,count = 100):
        try:
            self.renderer.set_dataFromFolder(fName)
            self.dataFolderChanged.emit(fName)
        except:
            print "couldnt open %s" % fName


    def resizeGL(self, width, height):
        if height == 0: height = 1

        self.width , self.height = width, height
        glViewport(0, 0, width, height)


    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        Ny, Nx = self.output.shape
        w = 1.*min(self.width,self.height)/self.width
        h = 1.*min(self.width,self.height)/self.height

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glBindTexture(GL_TEXTURE_2D,self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, 1, Nx, Ny,
                      0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.output.astype(uint8))
        glBegin (GL_QUADS);
        glTexCoord2f (0, 0);
        glVertex2f (-w, -h);
        glTexCoord2f (1, 0);
        glVertex2f (w, -h);
        glTexCoord2f (1, 1);
        glVertex2f (w,h);
        glTexCoord2f (0, 1);
        glVertex2f (-w, h);
        glEnd();


    def render(self):

        global modelView
        global isSocket

        if isSocket:
            loc_modelView = dot(transMat(0,0,-18*log(zoomVal)),modelView)
        else:
            loc_modelView = dot(transMat(0,0,-8+4*cos(.02*self.count)),rotMatX(.01*self.count));


        self.renderer.set_modelView(loc_modelView)

        out = self.renderer.render(render_func="max_proj")

        self.scale = .9*self.scale + .1*(1e-8+amax(out))
        out = (out-amin(out))/self.scale

        self.output = minimum(255,255*out)


        if self.count%20==0:
            print self.count
            t2  = time.time()
            fps = 20./(t2-self.t)
            self.t = t2
            self.parent.setWindowTitle('SpimRender (%.1f fps)'%fps)
        self.count += 1


    def onRenderTimer(self):
        self.render()
        self.updateGL()


    def onUpdateDataTimer(self):

        if self.dataQueue.qsize():
            self.renderer.update_data(self.dataQueue.get())
            self.dataQueue.task_done()

        self.render()
        self.updateGL()

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(600, 600)
        self.setWindowTitle('SpimRender')

        self.initActions()
        self.initMenus()

        self.glWidget = GLWidget(self)
        self.setCentralWidget(self.glWidget)

        renderTimer = QtCore.QTimer(self)
        renderTimer.setInterval(50)
        QtCore.QObject.connect(renderTimer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.onRenderTimer)
        renderTimer.start()

        updateDataTimer = QtCore.QTimer(self)
        updateDataTimer.setInterval(100)
        QtCore.QObject.connect(updateDataTimer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.onUpdateDataTimer)
        updateDataTimer.start()


    def initActions(self):
        self.exitAction = QtGui.QAction('Quit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.connect(self.exitAction, QtCore.SIGNAL('triggered()'), self.close)

    def initMenus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(self.exitAction)
        # this has to be repeated in MAC OSX for some magic reason
        fileMenu = menuBar.addMenu('&File')

    def close(self):
        isAppRunning = False
        QtGui.qApp.quit()




if __name__ == '__main__':



    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
