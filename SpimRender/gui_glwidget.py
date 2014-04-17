import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from OpenGL import GLU
from OpenGL import GLUT

from OpenGL.GL import *
from OpenGL.GL import shaders

from volume_render import *

from numpy import *

# on windows numpy.linalg.inv crashes without notice, so we have to import scipy.linalg
if os.name == "nt":
    from scipy import linalg


import time
from quaternion import Quaternion

vertShaderStrBasic ="""#version 120
void main() {
gl_FrontColor = gl_Color;
gl_TexCoord[0] = gl_MultiTexCoord0;
gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

fragShaderStrBasic = """#version 120
void main() {
gl_FragColor = gl_Color;
}
"""

fragShaderStrTex = """#version 120
uniform sampler2D tex;
void main() {
gl_FragColor  = texture2D(tex, gl_TexCoord[0].st);
gl_FragColor.w = 1.*length(gl_FragColor.xyz);

}
"""



class TransformModel(QtCore.QObject):
    _maxChanged = QtCore.pyqtSignal(int)
    _gammaChanged = QtCore.pyqtSignal(float)

    def __init__(self):
        super(TransformModel,self).__init__()
        self.reset()

    def reset(self,maxVal = 256.):
        self.quatRot = Quaternion()
        self.translate = [0,0,0]
        self.zoom = 1.
        self.setScale(0,maxVal)
        self.setGamma(1.)


    def setGamma(self, gamma):
        self.gamma = gamma
        print "gamma: ", self.gamma
        print "maxVal: ", self.maxVal

        self._gammaChanged.emit(self.gamma)


    def setScale(self,minVal,maxVal):
        self.minVal, self.maxVal = minVal, maxVal
        print "maxVal: ", maxVal
        self._maxChanged.emit(self.maxVal)


class GLWidget(QtOpenGL.QGLWidget):

    def __init__(self, parent=None, N_PREFETCH = 1,**kwargs):

        super(GLWidget,self).__init__(parent,**kwargs)

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer2((800,800),useDevice=0)
        self.output = zeros([self.renderer.height,self.renderer.width],dtype=uint8)

        self.count = 0


        self.transform = TransformModel()

        self.t = time.time()

        self.renderTimer = QtCore.QTimer(self)
        self.renderTimer.setInterval(50)
        self.renderTimer.timeout.connect(self.onRenderTimer)
        self.renderTimer.start()

        self.N_PREFETCH = N_PREFETCH

        self.setModel(None)
        self.transform._maxChanged.connect(lambda x:self.refresh())
        self.transform._gammaChanged.connect(lambda x:self.refresh())

        self.refresh()


    def setModel(self,dataModel):
        self.dataModel = dataModel
        if self.dataModel:
            self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
            self.dataModel._dataPosChanged.connect(self.dataPosChanged)
            self.dataSourceChanged()
            self.transform.reset(amax(self.dataModel[0]))


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile().toLocal8Bit().data()
            self.dataModel.load(path, prefetchSize = self.N_PREFETCH)


    def initializeGL(self):
        glClearColor(0,0,0,1.)
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

        self.width , self.height = 200, 200

        # set up shaders...
        self.shaderBasic = QtOpenGL.QGLShaderProgram()
        self.shaderBasic.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderStrBasic)
        self.shaderBasic.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderStrBasic)
        print self.shaderBasic.log()
        self.shaderBasic.link()

        self.shaderTex = QtOpenGL.QGLShaderProgram()
        self.shaderTex.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderStrBasic)
        self.shaderTex.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderStrTex)
        print self.shaderTex.log()
        self.shaderTex.link()

    def dataSourceChanged(self):
        self.renderer.set_data(self.dataModel[0])
        if self.dataModel.dataContainer.stackUnits != None:
            self.renderer.set_units(self.dataModel.dataContainer.stackUnits)
        else:
            self.renderer.set_units([.16,.16,.8])
        self.transform.reset(amax(self.dataModel[0]))

        self.refresh()



    def dataPosChanged(self,pos):
        self.renderer.update_data(self.dataModel[pos])
        self.refresh()


    def refresh(self):
        if self.parentWidget() and self.dataModel:
            self.parentWidget().setWindowTitle("SpImagine %s"%self.dataModel.fName)
        self.renderUpdate = True

    def resizeGL(self, width, height):
        if height == 0: height = 1

        self.width , self.height = width, height
        glViewport(0, 0, width, height)


    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        Ny, Nx = self.output.shape
        w = 1.*min(self.width,self.height)/self.width
        h = 1.*min(self.width,self.height)/self.height

        self.shaderBasic.bind()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        GLU.gluPerspective(360*arctan(.5)/pi,1.*self.width/self.height,2,10.)
        # glOrtho(-1.*self.width/self.height,1.*self.width/self.height,-1,1,1,-1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        modelView = self.getModelView()


        # mScale =  scaleMat(1.,1.*dx*Nx/dy/Ny,1.*dx*Nx/dz/Nz)
        mScale =  self.renderer._stack_scale_mat()

        # glTranslatef(0,0,3)
        glTranslatef(0,0,-7*(1-log(self.transform.zoom)/log(2.)))


        glMultMatrixf(linalg.inv(self.transform.quatRot.toRotation4()))
        glMultMatrixf(mScale)


        glLineWidth(1)
        glColor(1.,1.,1.,.4)

        GLUT.glutWireCube(2.)

        self.shaderTex.bind()


        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glBindTexture(GL_TEXTURE_2D,self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, 1, Ny, Nx,
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


        glDisable(GL_TEXTURE_2D)

        self.shaderBasic.bind()

        rSphere = .05

        glEnable(GL_DEPTH_TEST)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.*self.width/self.height,1.*self.width/self.height,-1,1,-10,10)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(1.+2*rSphere,-1.+2*rSphere,0)
        glMultMatrixf(linalg.inv(self.transform.quatRot.toRotation4()))



        quadric = GLU.gluNewQuadric()

        glColor(101./255, 134./255, 167./255,.8)

        for i,rots in enumerate([-90,90,90]):
            vec = (arange(3)==i).astype(int)
            glPushMatrix()
            glRotatef(rots,*vec)
            glTranslatef(0,0,rSphere)
            GLU.gluCylinder(quadric,.2*rSphere,0,rSphere,30,30)
            glPopMatrix()

        glColor(14./255, 66./255, 108./255,.7)

        GLU.gluSphere(quadric,rSphere,40,40)



    def getModelView(self):
        modelView = dot(transMatReal(0,0,-7*(1-log(self.transform.zoom)/log(2.))),
                                dot(self.transform.quatRot.toRotation4(),transMatReal(*self.transform.translate)))

        return modelView


    def render(self):

        self.renderer.set_modelView(self.getModelView())

        out = self.renderer.render(isPerspective = True)

        self.output = clip(255.*(1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal)**self.transform.gamma),0,255)


        # if self.count%20==0:
        #     t2  = time.time()
        #     fps = 20./(t2-self.t)
        #     self.t = t2
        #     if self.parentWidget():
        #         self.parentWidget().setWindowTitle('%s   (%.1f fps)'%(self.dataModel.fName,fps))

        self.count += 1


    def onRenderTimer(self):
        if self.renderUpdate:
            self.render()
            self.renderUpdate = False
            self.updateGL()



    def wheelEvent(self, event):
        """ self.transform.zoom should be within [1,2]"""
        self.transform.zoom *= 1.2**(event.delta()/1400.)
        self.transform.zoom = clip(self.transform.zoom,1,2)
        self.refresh()


    def posToVec3(self,x,y, r0 = .8, isRot = True ):
        x, y = 2.*x/self.width-1.,1.-2.*y/self.width
        r = sqrt(x*x+y*y)
        if r>r0-1.e-7:
            x,y = 1.*x*r0/r, 1.*y*r0/r
        z = sqrt(max(0,r0**2-x*x-y*y))
        if isRot:
            M = linalg.inv(self.transform.quatRot.toRotation3())
            x,y,z = dot(M,[x,y,z])

        return x,y,z

    def posToVec2(self,x,y):
        x, y = 2.*x/self.width-1.,1.-2.*y/self.width
        return x,y


    def mousePressEvent(self, event):
        super(GLWidget, self).mousePressEvent(event)

        if event.buttons() == QtCore.Qt.LeftButton:
            self._x0, self._y0, self._z0 = self.posToVec3(event.x(),event.y())

        if event.buttons() == QtCore.Qt.RightButton:
            self._x0, self._y0, self._z0 = self.posToVec3(event.x(),event.y())


    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:

            x1,y1,z1 = self.posToVec3(event.x(),event.y())
            n = cross(array([self._x0,self._y0,self._z0]),array([x1,y1,z1]))
            nnorm = linalg.norm(n)
            if abs(nnorm)>=1.:
                nnorm *= 1./abs(nnorm)
            w = arcsin(nnorm)
            n *= 1./(nnorm+1.e-10)
            q = Quaternion(cos(.5*w),*(sin(.5*w)*n))
            self.transform.quatRot = self.transform.quatRot*q

        if event.buttons() == QtCore.Qt.RightButton:
            x, y = self.posToVec2(event.x(),event.y())
            self.transform.translate[0] += (x-self._x0)
            self.transform.translate[1] += (y-self._y0)
            self._x0,self._y0 = x,y

        self.refresh()

if __name__ == '__main__':
    from data_model import DataLoadModel, DemoData

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(600,600))
    win.setModel(DataLoadModel(dataContainer=DemoData(50),prefetchSize = 10))

    win.show()
    win.raise_()

    sys.exit(app.exec_())
