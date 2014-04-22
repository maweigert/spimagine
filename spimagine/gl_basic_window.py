import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from OpenGL import GLU
from OpenGL.GL import *
from numpy import array

class GLWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        self.parent = parent
        super(GLWidget,self).__init__(parent)

    def initializeGL(self):
        self.qglClearColor(QtGui.QColor(0, 0,  0))

        glEnable(GL_DEPTH_TEST)

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

        glLoadIdentity()
        glTranslate(0.0, 0.0, -50.0)
        glScale(20.0, 20.0, 20.0)
        glTranslate(-0.5, -0.5, -0.5)


    def onTimer(self):
        self.updateGL()

class MainWindow(QtGui.QMainWindow):

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
        QtGui.qApp.quit()


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
