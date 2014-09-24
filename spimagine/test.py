#!/usr/bin/env python

"""

The rendering widget

It renderes a projection via the OpenCL (defined in volume_render.py)
into a texture which is drawn by simple OpenGL calls onto the canvas.

It should handle all user interaction via a transformation model.


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

from spimagine.volume_render import VolumeRenderer

from spimagine.transform_matrices import *
from spimagine.data_model import DataModel


from spimagine.keyframe_model import TransformData

from spimagine.transform_model import TransformModel

from numpy import *
import numpy as np


# on windows numpy.linalg.inv crashes without notice, so we have to import scipy.linalg
if os.name == "nt":
    from scipy import linalg


import time
from spimagine.quaternion import Quaternion



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

  //gl_FragColor = col.x*vec4(1.,1.,1.,1.);
  //gl_FragColor.w = 1.*length(gl_FragColor.xyz);

  gl_FragColor = vec4(lut.xyz,col.x);

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
void main()
{
  gl_FragColor = vec4(1.,1.,1.,1.);
}
"""


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
uniform sampler1D LUT_tex;

void main() {

  vec4 col = texture2D(tex, gl_TexCoord[0].st);
  gl_FragColor  = texture2D(tex, gl_TexCoord[0].st);

gl_FragColor = col;
gl_FragColor.w = 1.*length(gl_FragColor.xyz);


//texture1D(LUT_tex, col.x);

}
"""

def fillTexture2d(data,tex = None):
    """ data.shape == (Ny,Nx)
          file texture with GL_RED
        data.shape == (Ny,Nx,3)
          file texture with GL_RGB

        if tex == None, returns a new created texture
    """

    if tex is None:
        tex = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, tex)
    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    glTexParameterf (GL_TEXTURE_2D,
                     GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameterf (GL_TEXTURE_2D,
                     GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)

    if data.ndim == 2:
        Ny,Nx = data.shape
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                     0, GL_RED, GL_FLOAT, data.astype(float32))

    elif data.ndim == 3 and data.shape[2]==3:
        Ny,Nx = data.shape[:2]
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                         0, GL_RGB, GL_FLOAT, data.astype(float32))

    else:
        raise Exception("data format not supported! \ndata.shape shoul be either (Ny,Nx) or (Ny,Nx,3)")

    return tex

def arrayFromImage(fName):
    """converts png image to float32 array"""
    img = QtGui.QImage(fName).convertToFormat(QtGui.QImage.Format_RGB32)
    Nx, Ny = img.width(),img.height()
    tmp = img.bits().asstring(img.numBytes())
    arr = frombuffer(tmp, uint8).reshape((Ny,Nx,4))
    arr = arr.astype(float32)/amax(arr)
    return arr[:,:,:-1][:,:,::-1]


class GLWidget(QtOpenGL.QGLWidget):
    _dataModelChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None, N_PREFETCH = 1,**kwargs):

        super(GLWidget,self).__init__(parent,**kwargs)

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer((800,800))
        self.renderer.set_projection(projMatPerspective(60,1.,.1,10))
        # self.renderer.set_projection(projMatOrtho(-2,2,-2,2,-10,10))

        self.output = zeros([self.renderer.height,self.renderer.width],dtype = np.float32)

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
        self.transform.setModel(dataModel)
        if self.dataModel:
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


    def load_colormap(self):
        self.texture_LUT = fillTexture2d(arrayFromImage("colormaps/grays.png"))

    def initializeGL(self):


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

        self.width , self.height = 200, 200

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

        self.cubeCoord *= .5

        self.load_colormap()


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
        self.renderer.set_units([px,py,pz])


    def dataPosChanged(self,pos):
        self.renderer.update_data(self.dataModel[pos])
        self.refresh()


    def refresh(self):
        if self.parentWidget() and self.dataModel:
            self.parentWidget().setWindowTitle("SpImagine %s"%self.dataModel.name())
        self.renderUpdate = True

    def resizeGL(self, width, height):
        if height == 0: height = 1

        self.width , self.height = width, height
        glViewport(0, 0, width, height)


    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.dataModel:
            Ny, Nx = self.output.shape
            w = 1.*max(self.width,self.height)/self.width
            h = 1.*max(self.width,self.height)/self.height

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glMultMatrixf(self.renderer.projection.T)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            mScale =  self.renderer._stack_scale_mat()
            modelView = self.transform.getModelView()
            scaledModelView  = dot(modelView,mScale)
            glScale(w,h,1);

            glMultMatrixf(scaledModelView.T)

            # print glGetFloatv(GL_PROJECTION_MATRIX)

            # projMat = self.renderer.projection.T

            # mvpMat = dot(projMat,scaledModelView)

            mvpMat = np.identity(4)

            modelMat =  glGetFloatv(GL_MODELVIEW_MATRIX)
            projMat =  glGetFloatv(GL_PROJECTION_MATRIX)

            print "kkk"
            # print modelView
            # print dot([0,0,1,1.],modelMat)
            # print dot([0,0,1,1.],modelView.T)

            # print dot([0,0,1,1.],projMat)
            # print dot([0,0,1,1.],dot(projMat,modelMat))

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(0,0,-3)
            # print glGetFloatv(GL_MODELVIEW_MATRIX)
            # print transMat(0,0,-3)

            finalMat = transMat(0.4,0,0)

            finalMat = modelView.T

            finalMat = dot(projMat,modelMat).T

            finalMat = dot(projMatPerspective(),transMat(0,0,-4))

            finalMat = dot(transMat(0,0,-1),projMatOrtho())
            # finalMat = dot(transMat(0,0,-1),projMatOrtho())

            finalMat = dot(transMat(0,0,-5),projMatPerspective())


            modelM = self.transform.getModelView()
            viewM = transMat(0,0,-1)
            projM = projMatOrtho()

            finalMat = dot(projM,dot(viewM,modelM))

            print dot([.5,.5,.5,1.],finalMat)


            # mvpmat = scaledModelView

            # mvpMat = dot(scaledModelView,projMatg)

            # Draw the cube


            self.programCube.bind()

            self.programCube.setUniformValue("mvpMatrix",QtGui.QMatrix4x4(*finalMat.flatten()))
            self.programCube.enableAttributeArray("position")
            self.programCube.setAttributeArray("position", self.cubeCoord)


            glDrawArrays(GL_LINES,0,len(self.cubeCoord))

            # glDrawArrays(GL_TRIANGLES,0,len(self.cubeCoord))

            # # Draw the render texture
            # self.programTex.bind()

            # self.texture = fillTexture2d(self.output,self.texture)

            # glEnable(GL_TEXTURE_2D)
            # glDisable(GL_DEPTH_TEST)

            # self.programTex.enableAttributeArray("position")
            # self.programTex.enableAttributeArray("texcoord")
            # self.programTex.setAttributeArray("position", self.quadCoord)
            # self.programTex.setAttributeArray("texcoord", self.quadCoordTex)


            # glActiveTexture(GL_TEXTURE0)
            # glBindTexture(GL_TEXTURE_2D, self.texture)
            # self.programTex.setUniformValue("texture",0)

            # glActiveTexture(GL_TEXTURE1)
            # glBindTexture(GL_TEXTURE_2D, self.texture_LUT)
            # self.programTex.setUniformValue("texture_LUT",1)


            # glDrawArrays(GL_TRIANGLES,0,len(self.quadCoord))




    def render(self):
        self.renderer.set_modelView(self.transform.getModelView())
        self.renderer.set_projection(self.transform.projection)
        out = self.renderer.render()

        # self.output = clip(255.*(1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal)**self.transform.gamma),0,255)

        self.output = 1.*(out-self.transform.minVal)/(self.transform.maxVal-self.transform.minVal)**self.transform.gamma

        self.count += 1


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
            # print self.transform.maxVal,  amax(self.renderer._data), amax(self.output), self.renderer._data.dtype



    def wheelEvent(self, event):
        """ self.transform.zoom should be within [1,2]"""
        newZoom = self.transform.zoom * 1.2**(event.delta()/1400.)
        newZoom = clip(newZoom,.4,3)
        self.transform.setZoom(newZoom)

        logger.debug("newZoom: %s",newZoom)
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
            q = Quaternion(np.cos(.5*w),*(np.sin(.5*w)*n))
            self.transform.setQuaternion(self.transform.quatRot*q)

        if event.buttons() == QtCore.Qt.RightButton:
            x, y = self.posToVec2(event.x(),event.y())
            self.transform.translate[0] += (x-self._x0)
            self.transform.translate[1] += (y-self._y0)
            self._x0,self._y0 = x,y

        self.refresh()

if __name__ == '__main__':
    from data_model import DataModel, DemoData, SpimData

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(600,500))
    win.setModel(DataModel.fromPath("/Users/mweigert/Data/droso_test.tif",prefetchSize = 0))

    # win.transform.setBox()
    # win.transform.setPerspective(True)

    win.show()

    win.raise_()

    sys.exit(app.exec_())
