from __future__ import absolute_import, print_function
import sys
from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtOpenGL
from OpenGL import GLU
from OpenGL import GLUT
from OpenGL.GL import *
from numpy import *
from transform_matrices import *

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        self.parent = parent
        super(GLWidget,self).__init__(parent)

    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(0, 0,  0))

        # glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        # glEnable(GL_DEPTH_TEST)
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



    def resizeGL(self, width, height):
        if height == 0: height = 1

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / float(height)

        GLU.gluPerspective(45.0, aspect, 1.0, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        Nx, Ny = 100,100
        self.output = linspace(0,1.,Nx*Ny)

        glBindTexture(GL_TEXTURE_2D,self.texture)
        # glTexImage2D(GL_TEXTURE_2D, 0, 1, Ny, Nx,
        #                  0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.output.astype(uint8))

        glTexImage2D(GL_TEXTURE_2D, 0, 1, Ny, Nx,
                         0, GL_RED, GL_FLOAT, self.output.astype(float32))

        w,h = 1,1
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

        # glOrtho(-2,2,-2,2,-10,10)

        # print glGetFloatv(GL_PROJECTION_MATRIX).T
        # print projMatOrtho(-2.,2.,-2.,2.,-10,10)
        # glMatrixMode(GL_MODELVIEW)
        # glLoadIdentity()



        # glLineWidth(1)
        # glColor(1.,1.,1.,1.)
        # GLUT.glutWireCube(2)


    def onTimer(self):
        self.updateGL()

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow,self).__init__()

        self.resize(300, 300)
        self.setWindowTitle('GL Cube Test')

        self.initActions()
        self.initMenus()


        glWidget = GLWidget(self)
        self.setCentralWidget(glWidget)

        timer = QtCore.QTimer(self)
        timer.setInterval(20)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'), glWidget.onTimer)
        timer.start()


    def initActions(self):
        self.exitAction = QtWidgets.QAction('Quit', self)
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
        QtWidgets.qApp.quit()


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
