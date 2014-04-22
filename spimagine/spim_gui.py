#!/usr/bin/python

import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from OpenGL import GLU
from OpenGL.GL import *

from volume_render import *
from dataloader import DataLoader
import SpimUtils

from numpy import *
import time
from scipy.misc import imsave
from quaternion import Quaternion



class GLWidget(QtOpenGL.QGLWidget):
    dataFolderChanged = QtCore.pyqtSignal(str)
    posChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        self.parent = parent
        super(GLWidget,self).__init__(parent)

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer2((800,800),useDevice=1)
        self.output = zeros([self.renderer.height,self.renderer.width],dtype=uint8)
        self.modelViewThread = ModelViewThread()
        self.modelViewThread.start()



        self.dataQueue = Queue.Queue()

        self.dataLoader = DataLoader()

        self.count = 0
        self.quatRot = Quaternion(1,0,0,0)

        self.scale = 1.
        self.t = time.time()
        self.load("../../Data/Drosophila_05")
        # self.load("/Users/mweigert/python/Data/DrosophilaDeadPan/example/SPC0_TM0606_CM0_CM1_CHN00_CHN01.fusedStack.tif")


        # self.set_dataFromFolder("../Data/Drosophila_05")


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile().toLocal8Bit().data()
            print path
            self.load(path)

            # self.set_dataFromFolder(path)


    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(0, 0,  0))
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable( GL_LINE_SMOOTH )
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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

    def load(self, fName):
        self.dataLoader.load(fName)
        self.renderer.set_data(self.dataLoader[0])
        if self.dataLoader.dataContainer.stackUnits != None:
            self.renderer.set_units(self.dataLoader.dataContainer.stackUnits)
        else:
            self.renderer.set_units([.16,.16,.8])

        print self.renderer.stackUnits

    def set_dataFromFolder(self,fName):
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

        glEnable(GL_TEXTURE_2D)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glBindTexture(GL_TEXTURE_2D,self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, 1, Ny, Nx,
                      0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.output.astype(uint8))
        glColor4f(1.,1.,1.,1.);

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

        glDisable(GL_TEXTURE_2D)

        rSphere = .05

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.*self.width/self.height,1.*self.width/self.height,-1,1,-10,10)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(1.-2*rSphere,-1.+2*rSphere,0)

        glMultMatrixf(linalg.inv(self.quatRot.toRotation4()))


        quadric = GLU.gluNewQuadric()

        glLineWidth(2)
        glColor(101./255, 134./255, 167./255,.8)
        # glColor(.8,.8,.8,.7)

        for i,rots in enumerate([-90,90,90]):
            vec = (arange(3)==i).astype(int)
            glPushMatrix()
            glRotatef(rots,*vec)
            glTranslatef(0,0,rSphere)
            GLU.gluCylinder(quadric,.2*rSphere,0,rSphere,30,30)
            glPopMatrix()

        glColor(14./255, 66./255, 108./255,.7)
        # glColor(.4,.4,.4,.7)

        GLU.gluSphere(quadric,rSphere,40,40)



    def render(self):

        global modelView
        global isSocket

        if isSocket:
            loc_modelView = dot(transMat(0,0,12*(-1./3+log(2)-log(zoomVal))),modelView)
        else:

            # loc_modelView = dot(transMat(0,0,12*(-1./3+log(2)-log(zoomVal))),
            #                     self.quatRot.toRotation4())

            modelView = dot(transMatReal(0,0,-10*(1-log(zoomVal)/log(2.))),
                                self.quatRot.toRotation4())

        self.renderer.set_modelView(modelView)

        out = self.renderer.render(isPerspective = True)

        self.scale = .9*self.scale + .1*(1e-8+partition(out.flatten(),out.size-100)[out.size-100])

        out = (out-amin(out))/self.scale

        self.output = minimum(255,255*out)


        if self.count%20==0:
            t2  = time.time()
            fps = 20./(t2-self.t)
            self.t = t2
            self.parent.setWindowTitle('SpimRender (%.1f fps)'%fps)
        self.count += 1


    def onRenderTimer(self):
        self.render()
        self.updateGL()


    def onUpdateDataTimer(self):
        # print "updating"
        if self.dataQueue.qsize():
            self.renderer.update_data(self.dataQueue.get(timeout=2))
            self.dataQueue.task_done()

        self.render()
        self.updateGL()


    def wheelEvent(self, event):
        global zoomVal
        lam = 2*zoomVal-3
        lam += sign(event.delta())*(1.01-abs(lam))/30.
        lam = sign(lam)*min(1,abs(lam))
        zoomVal = (3+lam)/2.

    def posToVec(self,x,y, r0 = .3,isRot = True ):
        x, y = 2.*x/self.width-1.,1.-2.*y/self.width
        r = sqrt(x*x+y*y)
        if r>r0-1.e-7:
            x,y = 1.*x*r0/r, 1.*y*r0/r
        z = sqrt(max(0,r0**2-x*x-y*y))
        print x,y,z
        if isRot:
            # global modelView

            M = linalg.inv(self.quatRot.toRotation3())
            x,y,z = dot(M,[x,y,z])

            # x,y,z,w = dot(modelView,[x,y,z,1])
            # print x,y,z

        return x,y,z


    def mousePressEvent(self, event):
        super(GLWidget, self).mousePressEvent(event)

        if event.buttons() == QtCore.Qt.LeftButton:
            print "huhu"
            self._x0, self._y0, self._z0 = self.posToVec(event.x(),event.y())

        # print "pressed ", self._x0,self._y0,self._z0

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:

            x1,y1,z1 = self.posToVec(event.x(),event.y())
            n = cross(array([self._x0,self._y0,self._z0]),array([x1,y1,z1]))
            nnorm = linalg.norm(n)
            if abs(nnorm)>=1.:
                nnorm *= 1./abs(nnorm)
            w = arcsin(nnorm)
            n *= 1./(nnorm+1.e-10)
            q = Quaternion(cos(.5*w),*(sin(.5*w)*n))
            self.quatRot = self.quatRot*q



class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(600, 600)
        self.setWindowTitle('SpimRender')

        self.initActions()
        self.initMenus()

        self.glWidget = GLWidget(self)

        self.startButton = QtGui.QPushButton("",self)
        self.startButton.setStyleSheet("background-color: black")
        self.startButton.setIcon(QtGui.QIcon("icon_start.png"))
        self.startButton.setIconSize(QtCore.QSize(24,24))
        self.startButton.clicked.connect(self.startTimeLapsed)
        self.startButton.setMaximumWidth(24)
        self.startButton.setMaximumHeight(24)

        self.sliderTime = QtGui.QSlider(QtCore.Qt.Horizontal)
        # self.sliderTime.setStyleSheet("QSlider::handle:horizontal {border-radius: 1px;}")

        self.sliderTime.setRange(1, 400)
        self.sliderTime.setValue(1)
        self.sliderTime.setTracking(True)
        self.sliderTime.setTickPosition(QtGui.QSlider.TicksBothSides)

        self.connect(self.sliderTime, QtCore.SIGNAL('valueChanged(int)'),
                     self.on_sliderTime)

        self.setStyleSheet("background-color:black")


        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.glWidget)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.startButton)
        hbox.addWidget(self.sliderTime)

        vbox.addLayout(hbox)

        widget = QtGui.QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)

        renderTimer = QtCore.QTimer(self)
        renderTimer.setInterval(50)
        QtCore.QObject.connect(renderTimer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.onRenderTimer)
        renderTimer.start()

        self.updateDataTimer = QtCore.QTimer(self)
        self.updateDataTimer.setInterval(50)
        QtCore.QObject.connect(self.updateDataTimer, QtCore.SIGNAL('timeout()'),
                               self.glWidget.onUpdateDataTimer)
        QtCore.QObject.connect(self.updateDataTimer, QtCore.SIGNAL('timeout()'),
                               self.onUpdateDataTimer)



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


    def startTimeLapsed(self,event):
        if self.updateDataTimer.isActive():
            self.updateDataTimer.stop()
            self.startButton.setIcon(QtGui.QIcon("icon_start.png"))

        else:
            self.updateDataTimer.start()
            self.startButton.setIcon(QtGui.QIcon("icon_pause.png"))

    def on_sliderTime(self,event):
        pos =  self.sliderTime.value()
        self.glWidget.posChanged.emit(pos)
        # time.sleep(.4)
        self.glWidget.onUpdateDataTimer()


    def onUpdateDataTimer(self):
        pos =  self.sliderTime.value()
        self.sliderTime.setValue(pos+1)

    def close(self):
        isAppRunning = False
        QtGui.qApp.quit()




if __name__ == '__main__':



    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
