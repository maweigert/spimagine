#!/usr/bin/env python

"""

The rendering widget

It renderes a projection via the OpenCL (defined in volume_render.py)
into a texture which is drawn by simple OpenGL calls onto the canvas.

It should handle all user interaction via a transformation model.


author: Martin Weigert
email: mweigert@mpi-cbg.de
"""



import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from OpenGL import GLU
from OpenGL import GLUT

from OpenGL.GL import *
from OpenGL.GL import shaders

from volume_render import VolumeRenderer

from transform_matrices import *

from numpy import *

from keyframe_model import TransformData


# from scipy.misc import imsave

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
    _boxChanged = QtCore.pyqtSignal(int)
    _perspectiveChanged = QtCore.pyqtSignal(int)
    # _rotationChanged = QtCore.pyqtSignal(float,float,float,float)

    _transformChanged = QtCore.pyqtSignal()
    _stackUnitsChanged = QtCore.pyqtSignal(float,float,float)

    def __init__(self):
        super(TransformModel,self).__init__()
        self.reset()

    def reset(self,maxVal = 256.,stackUnits=None):
        self.quatRot = Quaternion()
        self.translate = [0,0,0]
        self.cameraZ = 5
        self.scaleAll = 1.
        self.zoom = 1.
        self.isPerspective = True
        self.setPerspective()
        self.setScale(0,maxVal)
        self.setGamma(1.)
        self.setBox(True)
        if not stackUnits:
            stackUnits = [.1,.1,.1]
        self.setStackUnits(*stackUnits)
        self.update()


    def setGamma(self, gamma):
        self.gamma = gamma
        print "gamma: ", self.gamma
        print "maxVal: ", self.maxVal

        self._gammaChanged.emit(self.gamma)
        self._transformChanged.emit()

    def setScale(self,minVal,maxVal):
        self.minVal, self.maxVal = minVal, maxVal
        print "maxVal: ", maxVal
        self._maxChanged.emit(self.maxVal)
        self._transformChanged.emit()


    def setStackUnits(self,px,py,pz):
        print px,py,pz
        self.stackUnits = px,py,pz
        self._stackUnitsChanged.emit(px,py,pz)
        self._transformChanged.emit()

    def setBox(self,isBox = True):
        self.isBox = isBox
        self._boxChanged.emit(isBox)
        self._transformChanged.emit()

    def setZoom(self,zoom = 1.):
        self.zoom = clip(zoom,.5,2)
        self.update()

    # def setRotation(self,w,x,y,z):
    #     """ rotation in quaternion notation""" 
    #     self.quat = quat.copy()



    def update(self):
        if self.isPerspective:
            self.cameraZ = 4*(1-log(self.zoom)/log(2.))
            self.scaleAll = 1.
        else:
            self.cameraZ = 0.
            self.scaleAll = 2.5**(self.zoom-1.)

    def setPerspective(self, isPerspective = True):
        self.isPerspective = isPerspective
        if isPerspective:
            self.projection = projMatPerspective(60.,1.,.1,10)
        else:
            self.projection = projMatOrtho(-2.,2.,-2.,2.,-1.5,1.5)

        self.update()
        self._perspectiveChanged.emit(isPerspective)
        self._transformChanged.emit()


    def getModelView(self):
        # modelView = dot(transMatReal(0,0,-7*(1-log(self.transform.zoom)/log(2.))),
        #                         dot(self.transform.quatRot.toRotation4(),transMatReal(*self.transform.translate)))

        # modelView = dot(transMatReal(0,0,-self.cameraZ),dot(scaleMat(*[self.scaleAll]*3),
        #                         dot(self.quatRot.toRotation4(),transMatReal(*self.translate))))
        modelView = dot(transMatReal(0,0,-self.cameraZ),dot(scaleMat(*[self.scaleAll]*3),
                                dot(transMatReal(*self.translate),self.quatRot.toRotation4())))

        return modelView

    def fromTransformData(self,transformData):
        pass

    def toTransformData(self):
        return TransformData(*self.quatRot)


class GLWidget(QtOpenGL.QGLWidget):

    def __init__(self, parent=None, N_PREFETCH = 1,**kwargs):

        super(GLWidget,self).__init__(parent,**kwargs)

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer((800,800))
        self.renderer.set_projection(projMatPerspective(60,1.,.1,10))
        # self.renderer.set_projection(projMatOrtho(-2,2,-2,2,-10,10))

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
        self.transform._transformChanged.connect(self.refresh)
        self.transform._stackUnitsChanged.connect(self.setStackUnits)

        self.refresh()


    def setModel(self,dataModel):
        self.dataModel = dataModel
        if self.dataModel:
            self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
            self.dataModel._dataPosChanged.connect(self.dataPosChanged)
            self.dataSourceChanged()
            self.transform.reset(amax(self.dataModel[0]),self.dataModel.dataContainer.stackUnits)


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
        # if self.dataModel.dataContainer.stackUnits != None:
        #     self.renderer.set_units(self.dataModel.dataContainer.stackUnits)
        # else:
        #     self.renderer.set_units([.16,.16,.8])
        self.transform.reset(amax(self.dataModel[0]),self.dataModel.dataContainer.stackUnits)

        self.refresh()


    def setStackUnits(self,px,py,pz):
        print "set: ", px,py,pz
        self.renderer.set_units([px,py,pz])


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
        w = 1.*max(self.width,self.height)/self.width
        h = 1.*max(self.width,self.height)/self.height
        self.shaderBasic.bind()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMultMatrixf(self.renderer.projection.T)

        # glOrtho(-1.*self.width/self.height,1.*self.width/self.height,-1,1,-10,10)
        # print glGetFloatv(GL_PROJECTION_MATRIX)


        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # glTranslatef(0,0,-7*(1-log(self.transform.zoom)/log(2.)))
        # glMultMatrixf(linalg.inv(self.transform.quatRot.toRotation4()))

        # print modelView

        mScale =  self.renderer._stack_scale_mat()
        modelView = self.transform.getModelView()
        scaledModelView  = dot(modelView,mScale)
        glScale(w,h,1);

        glMultMatrixf(scaledModelView.T)

        glLineWidth(1)
        glColor(1.,1.,1.,.3)

        if not os.name == "nt" and self.transform.isBox:
            GLUT.glutWireCube(2)

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



    def render(self):

        self.renderer.set_modelView(self.transform.getModelView())
        self.renderer.set_projection(self.transform.projection)
        out = self.renderer.render()

        self.output = clip(255.*(1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal)**self.transform.gamma),0,255)


        self.count += 1


    def saveFrame(self,fName):
        print "saving frame as ", fName
        self.render()
        self.grabFrameBuffer().save(fName)


    def onRenderTimer(self):
        if self.renderUpdate:
            self.render()
            self.renderUpdate = False
            self.updateGL()
            # print self.transform.maxVal,  amax(self.renderer._data), amax(self.output), self.renderer._data.dtype



    def wheelEvent(self, event):
        """ self.transform.zoom should be within [1,2]"""
        newZoom = self.transform.zoom * 1.2**(event.delta()/1400.)
        newZoom = clip(newZoom,.4,3)
        self.transform.setZoom(newZoom)

        print newZoom
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
    from data_model import DataLoadModel, DemoData, SpimData

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(600,500))
    # win.setModel(DataLoadModel(dataContainer=DemoData(50),prefetchSize = 10))
    win.setModel(DataLoadModel("/Users/mweigert/Data/droso_test.tif",prefetchSize = 0))

    win.transform.setBox()
    win.transform.setPerspective(True)

    win.show()

    # win.dataModel.load("/Users/mweigert/Data/droso_test",prefetchSize=0)
    win.raise_()

    sys.exit(app.exec_())
