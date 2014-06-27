#!/usr/bin/env python

"""
author: Martin Weigert
email: mweigert@mpi-cbg.de
"""


import logging
logger = logging.getLogger(__name__)



import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
from OpenGL import GLU
from OpenGL import GLUT

from OpenGL.GL import *
from OpenGL.GL import shaders

from spimagine.transform_matrices import *
from spimagine.data_model import DataModel


from spimagine.keyframe_model import TransformData

from spimagine.transform_model import TransformModel

from numpy import *
import numpy as np


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




class GLSliceView(QtOpenGL.QGLWidget):
    _dataModelChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None, orient = 0, **kwargs):


        self.orient = orient
        self.pos = 10
        self.output = zeros([100,100],dtype = np.float32)

        self.transform = TransformModel()

        super(GLSliceView,self).__init__(parent,**kwargs)

        # self.refresh()


    def setModel(self,dataModel):
        self.dataModel = dataModel
        if self.dataModel:
            self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
            self.dataModel._dataPosChanged.connect(self.dataPosChanged)
            self.updateGL()



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

        # set up shaders...
        self.shaderBasic = QtOpenGL.QGLShaderProgram()
        self.shaderBasic.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderStrBasic)
        self.shaderBasic.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderStrBasic)

        logger.debug("shader log:%s",self.shaderBasic.log())

        self.shaderBasic.link()

        self.shaderTex = QtOpenGL.QGLShaderProgram()
        self.shaderTex.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderStrBasic)
        self.shaderTex.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderStrTex)

        logger.debug("shader log:%s",self.shaderTex.log())

        self.shaderTex.link()


    # def dataModelChanged(self):
    #     if self.dataModel:
    #         self.renderer.set_data(self.dataModel[0])
    #         self.transform.reset(amax(self.dataModel[0])+1,self.dataModel.stackUnits())
    #         self.refresh()


    def dataSourceChanged(self):
        # self.updateGL()
        pass

    def dataPosChanged(self,pos):
        # self.updateGL()
        pass


    def resizeGL(self, width, height):
        if height == 0: height = 1

        self.width , self.height = width, height
        glViewport(0, 0, width, height)


    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


        if self.dataModel:
            out = self.dataModel[0][10,:,:].astype(float32)
            self.output = 1.*out/amax(out)

            # self.output = linspace(0,1.,10000).reshape((100,100))
            Ny, Nx = self.output.shape

            print np.amax(self.output)
            w = .6*max(Nx,Ny)/Nx
            h = .6*max(Nx,Ny)/Ny
            self.shaderBasic.bind()

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            self.shaderTex.bind()


            glEnable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()

            glBindTexture(GL_TEXTURE_2D,self.texture)

            glTexImage2D(GL_TEXTURE_2D, 0, 1, Ny, Nx,
                         0, GL_RED, GL_FLOAT, self.output.T.astype(float32))


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



    # def render(self):
    #     self.renderer.set_modelView(self.transform.getModelView())
    #     self.renderer.set_projection(self.transform.projection)
    #     out = self.renderer.render()

    #     # self.output = clip(255.*(1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal)**self.transform.gamma),0,255)

    #     self.output = 1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal)**self.transform.gamma

    #     self.count += 1


    # def onRenderTimer(self):
    #     if self.renderUpdate:
    #         self.render()
    #         self.renderUpdate = False
    #         self.updateGL()
    #         # print self.transform.maxVal,  amax(self.renderer._data), amax(self.output), self.renderer._data.dtype



    # def wheelEvent(self, event):
    #     """ self.transform.zoom should be within [1,2]"""
    #     newZoom = self.transform.zoom * 1.2**(event.delta()/1400.)
    #     newZoom = clip(newZoom,.4,3)
    #     self.transform.setZoom(newZoom)

    #     logger.debug("newZoom: %s",newZoom)
    #     self.refresh()


    # def posToVec3(self,x,y, r0 = .8, isRot = True ):
    #     x, y = 2.*x/self.width-1.,1.-2.*y/self.width
    #     r = sqrt(x*x+y*y)
    #     if r>r0-1.e-7:
    #         x,y = 1.*x*r0/r, 1.*y*r0/r
    #     z = sqrt(max(0,r0**2-x*x-y*y))
    #     if isRot:
    #         M = linalg.inv(self.transform.quatRot.toRotation3())
    #         x,y,z = dot(M,[x,y,z])

    #     return x,y,z

    # def posToVec2(self,x,y):
    #     x, y = 2.*x/self.width-1.,1.-2.*y/self.width
    #     return x,y


    # def mousePressEvent(self, event):
    #     super(GLWidget, self).mousePressEvent(event)

    #     if event.buttons() == QtCore.Qt.LeftButton:
    #         self._x0, self._y0, self._z0 = self.posToVec3(event.x(),event.y())

    #     if event.buttons() == QtCore.Qt.RightButton:
    #         self._x0, self._y0, self._z0 = self.posToVec3(event.x(),event.y())


    # def mouseMoveEvent(self, event):
    #     if event.buttons() == QtCore.Qt.LeftButton:

    #         x1,y1,z1 = self.posToVec3(event.x(),event.y())
    #         n = cross(array([self._x0,self._y0,self._z0]),array([x1,y1,z1]))
    #         nnorm = linalg.norm(n)
    #         if abs(nnorm)>=1.:
    #             nnorm *= 1./abs(nnorm)
    #         w = arcsin(nnorm)
    #         n *= 1./(nnorm+1.e-10)
    #         q = Quaternion(np.cos(.5*w),*(np.sin(.5*w)*n))
    #         self.transform.setQuaternion(self.transform.quatRot*q)

    #     if event.buttons() == QtCore.Qt.RightButton:
    #         x, y = self.posToVec2(event.x(),event.y())
    #         self.transform.translate[0] += (x-self._x0)
    #         self.transform.translate[1] += (y-self._y0)
    #         self._x0,self._y0 = x,y

    #     self.refresh()



if __name__ == '__main__':
    from data_model import DataModel, DemoData, SpimData

    app = QtGui.QApplication(sys.argv)

    win = GLSliceView(size=QtCore.QSize(600,500))

    win.setModel(DataModel.fromPath("/Users/mweigert/Data/droso_test.tif",prefetchSize = 0))

    # win.transform.setBox()
    # win.transform.setPerspective(True)

    win.show()

    win.raise_()

    sys.exit(app.exec_())
