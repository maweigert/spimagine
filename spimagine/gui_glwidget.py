#!/usr/bin/env python

"""

The rendering widget

It renderes a projection via the OpenCL (defined in volume_render.py)
into a texture which is drawn by simple OpenGL calls onto the canvas.

It should handle all user interaction via a transformation model.


author: Martin Weigert
email: mweigert@mpi-cbg.de
"""




"""
understanding glBlendFunc:

first color:     d
second color:    s
resulting color: c

c = s*S + d*D

where S and D are set with glBlendFunc(S,D)

e.g. glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

c = s*s.w + d*(1-s.w)



"""

import logging

logger = logging.getLogger(__name__)




import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL

from OpenGL.GL import *
from OpenGL.GL import shaders

from spimagine.volume_render import VolumeRenderer

from spimagine.transform_matrices import *
from spimagine.data_model import DataModel


from spimagine.transform_model import TransformModel

from numpy import *
import numpy as np

from spimagine.gui_utils import *


# on windows numpy.linalg.inv crashes without notice, so we have to import scipy.linalg
if os.name == "nt":
    from scipy import linalg


import time
from spimagine.quaternion import Quaternion

# from spimagine.shaders import vertShaderTex, fragShaderTex, vertShaderCube, fragShaderCube

# logger.setLevel(logging.DEBUG)


vertShaderTex ="""
attribute vec2 position;
attribute vec2 texcoord;
varying vec2 mytexcoord;

void main()
{
    gl_Position = vec4(position, 0., 1.0);
    mytexcoord = texcoord;
}
"""

fragShaderTex = """
uniform sampler2D texture;
uniform sampler2D texture_LUT;
varying vec2 mytexcoord;

void main()
{
  vec4 col = texture2D(texture,mytexcoord);

  vec4 lut = texture2D(texture_LUT,col.xy);

  gl_FragColor = vec4(lut.xyz,col.x);

//  gl_FragColor.w = 1.0*length(gl_FragColor.xyz);

// gl_FragColor = vec4(1.,lut.yz,1);

}
"""

vertShaderCube ="""
attribute vec3 position;
uniform mat4 mvpMatrix;

void main()
{
  vec3 pos = position;
  gl_Position = mvpMatrix *vec4(pos, 1.0);

}
"""

fragShaderCube = """

uniform vec4 color;

void main()
{
  gl_FragColor = vec4(1.,1.,1.,.6);
  gl_FragColor = color;
}
"""



def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)




class GLWidget(QtOpenGL.QGLWidget):
    _dataModelChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None, N_PREFETCH = 0,**kwargs):
        logger.debug("init")

        super(GLWidget,self).__init__(parent,**kwargs)

        self.parent= parent
        self.texture_LUT = None

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer((800,800))
        self.renderer.dev.printInfo()
        self.renderer.set_projection(projMatPerspective(60,1.,.1,10))
        # self.renderer.set_projection(projMatOrtho(-2,2,-2,2,-10,10))

        self.output = zeros([self.renderer.height,self.renderer.width],dtype = np.float32)

        self.setTransform(TransformModel())

        self.renderTimer = QtCore.QTimer(self)
        self.renderTimer.setInterval(50)
        self.renderTimer.timeout.connect(self.onRenderTimer)
        self.renderTimer.start()

        self.N_PREFETCH = N_PREFETCH

        self.dataModel = None




        self.refresh()



    def setModel(self,dataModel):
        logger.debug("setModel")

        self.dataModel = dataModel

        if self.dataModel:
            self.transform.setModel(dataModel)

            self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
            self.dataModel._dataPosChanged.connect(self.dataPosChanged)
            self._dataModelChanged.connect(self.dataModelChanged)
            self._dataModelChanged.emit()



    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        
        for url in event.mimeData().urls():
            path = url.toLocalFile().toLocal8Bit().data()

            
            if self.dataModel:
                self.dataModel.loadFromPath(path, prefetchSize = self.N_PREFETCH)
            else:
                self.setModel(DataModel.fromPath(path, prefetchSize = self.N_PREFETCH))


    def set_colormap(self,arr):
        """arr should be of shape (N,3) and gives the rgb components of the colormap"""
        self.makeCurrent()

        self.texture_LUT = fillTexture2d(arr.reshape((1,)+arr.shape),self.texture_LUT)


    def load_colormap(self, fName = "colormaps/jet.png"):
        self.set_colormap(arrayFromImage(absPath(fName))[0,:,:])



    def initializeGL(self):

        self.resized = True

        logger.debug("initializeGL")

        self.programTex = QtOpenGL.QGLShaderProgram()
        self.programTex.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderTex)
        self.programTex.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderTex)
        self.programTex.link()
        self.programTex.bind()
        logger.debug("GLSL programTex log:%s",self.programTex.log())

        self.programCube = QtOpenGL.QGLShaderProgram()
        self.programCube.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderCube)
        self.programCube.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderCube)
        self.programCube.link()
        self.programCube.bind()
        logger.debug("GLSL programCube log:%s",self.programCube.log())


        glClearColor(0,0,0,1.)

        self.texture = None

        self.quadCoord = np.array([[-1.,-1.,0.],
                           [1.,-1.,0.],
                           [1.,1.,0.],
                           [1.,1.,0.],
                           [-1.,1.,0.],
                           [-1.,-1.,0.]])

        self.quadCoordTex = np.array([[0,0],
                           [1.,0.],
                           [1.,1.],
                           [1.,1.],
                           [0,1.],
                           [0,0]])

        self.cubeCoord = np.array([[1.0,   1.0,  1.0], [-1.0,  1.0,  1.0],
                                   [-1.0,  1.0,  1.0], [-1.0, -1.0,  1.0],
                                   [-1.0, -1.0,  1.0], [ 1.0, -1.0,  1.0],
                                   [1.0,  -1.0,  1.0], [ 1.0,  1.0,  1.0],

                                   [1.0,   1.0,  -1.0], [-1.0,  1.0,  -1.0],
                                   [-1.0,  1.0,  -1.0], [-1.0, -1.0,  -1.0],
                                   [-1.0, -1.0,  -1.0], [ 1.0, -1.0,  -1.0],
                                   [1.0,  -1.0,  -1.0], [ 1.0,  1.0,  -1.0],

                                   [1.0,   1.0,  1.0], [1.0,  1.0,  -1.0],
                                   [-1.0,  1.0,  1.0], [-1.0, 1.0,  -1.0],
                                   [-1.0, -1.0,  1.0], [-1.0,-1.0,  -1.0],
                                   [1.0,  -1.0,  1.0], [1.0, -1.0,  -1.0],
                  ])

        self.cubeFaceCoord = np.array([[1.0,   1.0,  1.0], [-1.0,  1.0,  1.0], [-1.0,  -1.0,  1.0],
                                       [-1.0,  -1.0,  1.0], [1.0,  -1.0,  1.0], [1.0,  1.0,  1.0],
                                       ])

        self.load_colormap()

        glEnable( GL_BLEND )

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # glBlendFunc(GL_ONE,GL_ONE)

        glDisable(GL_DEPTH_TEST)


    def setTransform(self, transform):
        self.transform = transform
        self.transform._transformChanged.connect(self.refresh)
        self.transform._stackUnitsChanged.connect(self.setStackUnits)


    def dataModelChanged(self):
        if self.dataModel:
            self.renderer.set_data(self.dataModel[0])
            self.transform.reset(amax(self.dataModel[0])+1,self.dataModel.stackUnits())

            self.refresh()



    def dataSourceChanged(self):
        self.renderer.set_data(self.dataModel[0])
        self.transform.reset(amax(self.dataModel[0])+1,self.dataModel.stackUnits())
        self.refresh()


    def setStackUnits(self,px,py,pz):
        logger.debug("setStackUnits to %s"%[px,py,pz])
        self.renderer.set_units([px,py,pz])


    def dataPosChanged(self,pos):
        self.renderer.update_data(self.dataModel[pos])
        self.refresh()


    def refresh(self):
        # if self.parentWidget() and self.dataModel:
        #     self.parentWidget().setWindowTitle("SpImagine %s"%self.dataModel.name())
        self.renderUpdate = True

    def resizeGL(self, width, height):

        height = max(10,height)

        self.width , self.height = width, height

        #make the viewport squarelike
        w = max(width,height)
        glViewport((width-w)/2,(height-w)/2,w,w)

        self.resized = True

    def paintGL(self):

        self.makeCurrent()

        if not glCheckFramebufferStatus(GL_FRAMEBUFFER)==GL_FRAMEBUFFER_COMPLETE:
            return

        #hack
        if self.resized:
            w = max(self.width,self.height)
            glViewport((self.width-w)/2,(self.height-w)/2,w,w)
            self.resized = False


        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.dataModel:
            modelView = self.transform.getModelView()

            proj = self.transform.getProjection()

            finalMat = dot(proj,modelView)

            if self.transform.isBox:
                # Draw the cube
                self.programCube.bind()
                self.programCube.setUniformValue("mvpMatrix",QtGui.QMatrix4x4(*finalMat.flatten()))
                self.programCube.enableAttributeArray("position")

                self.programCube.setUniformValue("color",QtGui.QVector4D(1.,1.,1.,.6))
                self.programCube.setAttributeArray("position", self.cubeCoord)

                glDrawArrays(GL_LINES,0,len(self.cubeCoord))

                # self.programCube.setAttributeArray("position", .99*self.cubeFaceCoord)
                # self.programCube.setUniformValue("color",QtGui.QVector4D(0,0,0,.6))

                # glDrawArrays(GL_TRIANGLES,0,len(self.cubeFaceCoord))

            if self.transform.isSlice:
                # draw the slice
                self.programCube.bind()
                self.programCube.setUniformValue("mvpMatrix",QtGui.QMatrix4x4(*finalMat.flatten()))
                self.programCube.enableAttributeArray("position")

                self.programCube.setUniformValue("color",QtGui.QVector4D(1.,1.,1.,.6))

                pos, dim = self.transform.slicePos,self.transform.sliceDim

                coords = slice_coords(1.*pos/self.dataModel.size()[2-dim+1],dim)
                self.programCube.setAttributeArray("position", coords)
                glDrawArrays(GL_TRIANGLES,0,len(coords))


            # Draw the render texture
            self.programTex.bind()

            self.texture = fillTexture2d(self.output,self.texture)


            glEnable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)

            self.programTex.enableAttributeArray("position")
            self.programTex.enableAttributeArray("texcoord")
            self.programTex.setAttributeArray("position", self.quadCoord)
            self.programTex.setAttributeArray("texcoord", self.quadCoordTex)


            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture)
            self.programTex.setUniformValue("texture",0)

            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.texture_LUT)
            self.programTex.setUniformValue("texture_LUT",1)


            glDrawArrays(GL_TRIANGLES,0,len(self.quadCoord))




    def render(self):
        logger.debug("render")
        if self.dataModel:
            self.renderer.set_modelView(self.transform.getUnscaledModelView())
            self.renderer.set_projection(self.transform.getProjection())
            out = self.renderer.render()


            self.output = (1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal))**self.transform.gamma
            # self.output = clip(self.output,0,0.99)

            logger.debug("render: output range = %s"%([amin(self.output),amax(self.output)]))


    def saveFrame(self,fName):
        """FIXME: scaling behaviour still hast to be implemented (e.g. after setGamma)"""
        logger.info("saving frame as %s", fName)

        self.render()
        self.paintGL()
        glFlush()
        self.grabFrameBuffer().save(fName)


    def onRenderTimer(self):
        if self.renderUpdate:
            self.render()
            self.renderUpdate = False
            self.updateGL()



    def wheelEvent(self, event):
        """ self.transform.zoom should be within [1,2]"""
        newZoom = self.transform.zoom * 1.2**(event.delta()/1400.)
        newZoom = clip(newZoom,.4,3)
        self.transform.setZoom(newZoom)

        logger.debug("newZoom: %s",newZoom)
        # self.refresh()


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
            (self._x0, self._y0), self._invRotM = self.posToVec2(event.x(),event.y()), linalg.inv(self.transform.quatRot.toRotation3())


    def mouseMoveEvent(self, event):
        # Rotation
        if event.buttons() == QtCore.Qt.LeftButton:

            x1,y1,z1 = self.posToVec3(event.x(),event.y())
            n = cross(array([self._x0,self._y0,self._z0]),array([x1,y1,z1]))
            nnorm = linalg.norm(n)
            if abs(nnorm)>=1.:
                nnorm *= 1./abs(nnorm)
            w = arcsin(nnorm)
            n *= 1./(nnorm+1.e-10)
            q = Quaternion(np.cos(.5*w),*(np.sin(.5*w)*n))
            self.transform.setQuaternion(self.transform.quatRot*q)

        #Translation
        if event.buttons() == QtCore.Qt.RightButton:
            x, y = self.posToVec2(event.x(),event.y())

            dx, dy, foo = dot(self._invRotM,[x-self._x0, y-self._y0,0])
            self.transform.translate[0] += dx
            self.transform.translate[1] += dy

            self._x0,self._y0 = x,y

        self.refresh()

if __name__ == '__main__':
    from data_model import DataModel, DemoData, SpimData

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(500,500))


    win.setModel(DataModel.fromPath("C:\Users\myerslab\Desktop\HisGFP_Demo",prefetchSize = 0))

    win.transform.setStackUnits(1.,1.,5.)


    # win.transform.setBox()
    # win.transform.setPerspective(True)

    win.show()

    win.raise_()

    sys.exit(app.exec_())
