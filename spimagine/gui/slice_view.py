#!/usr/bin/env python

"""

The 2d slice widget


author: Martin Weigert
email: mweigert@mpi-cbg.de
"""


from __future__ import absolute_import, print_function

import logging

logger = logging.getLogger(__name__)




import sys
import os
from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtOpenGL
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader

from OpenGL.GL import *
from OpenGL.GL import shaders

import spimagine


from spimagine.volumerender.volumerender import VolumeRenderer
from spimagine.utils.transform_matrices import *
from spimagine.models.data_model import DataModel
from spimagine.models.transform_model import TransformModel
from spimagine.utils.quaternion import Quaternion
from spimagine.gui.gui_utils import *

from numpy import *
import numpy as np


# on windows numpy.linalg.inv crashes without notice, so we have to import scipy.linalg
if os.name == "nt":
    from scipy import linalg


import time

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

  gl_FragColor = vec4(lut.xyz,1.);

//  gl_FragColor.w = 1.0*length(gl_FragColor.xyz);

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




class GLSliceWidget(QtOpenGL.QGLWidget):
    _dataModelChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None,**kwargs):
        logger.debug("init")

        super(GLSliceWidget,self).__init__(parent,**kwargs)

        self.renderUpdate = True
        self.parent= parent

        self.setAcceptDrops(True)

        self.texture_LUT = None
        self.setTransform(TransformModel())

        self.renderTimer = QtCore.QTimer(self)
        self.renderTimer.setInterval(50)
        self.renderTimer.timeout.connect(self.onRenderTimer)
        self.renderTimer.start()

        self.dataModel = None

        self.dataPos = 0
        self.slicePos = 0

        self.zoom_fac = 1.
        self.zoom_x = 0.5
        self.zoom_y = 0.5
        # the center in tex coords
        self.zoom_cx = 0.5
        self.zoom_cy = 0.5


        # self.refresh()



    def setModel(self,dataModel):
        logger.debug("setModel")

        self.dataModel = dataModel

        if self.dataModel:
            self.transform.setModel(dataModel)

            self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
            self.dataModel._dataPosChanged.connect(self.dataPosChanged)
            self._dataModelChanged.connect(self.dataModelChanged)
            self._dataModelChanged.emit()


    def setTransform(self, transform):
        self.transform = transform
        self.transform._transformChanged.connect(self.refresh)


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


    def set_colormap(self,name):
        """arr should be of shape (N,3) and gives the rgb components of the colormap"""

        try:
            arr = spimagine.config.__COLORMAPDICT__[name]
            self.makeCurrent()
            self.texture_LUT = fillTexture2d(arr.reshape((1,)+arr.shape),self.texture_LUT)
        except:
            print("could not load colormap %s"%name)


    def set_colormap_rgb(self,color=[1.,1.,1.]):
        self._set_colormap_array(outer(linspace(0,1.,255),np.array(color)))

    def _set_colormap_array(self,arr):
        """arr should be of shape (N,3) and gives the rgb components of the colormap"""


        self.makeCurrent()
        self.texture_LUT = fillTexture2d(arr.reshape((1,)+arr.shape),self.texture_LUT)
        self.refresh()

        
    def initializeGL(self):

        self.resized = True

        self.output = zeros((100,100))

        logger.debug("initializeGL")

        self.programTex = QOpenGLShaderProgram()
        self.programTex.addShaderFromSourceCode(QOpenGLShader.Vertex,vertShaderTex)
        self.programTex.addShaderFromSourceCode(QOpenGLShader.Fragment, fragShaderTex)
        self.programTex.link()
        self.programTex.bind()
        logger.debug("GLSL programTex log:%s",self.programTex.log())

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

        self.set_colormap(spimagine.config.__DEFAULTCOLORMAP__)

        glDisable(GL_DEPTH_TEST)
        glEnable( GL_BLEND )

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)



    def dataModelChanged(self):
        if self.dataModel:
            self.transform.reset(amin(self.dataModel[0]),
                                 amax(self.dataModel[0]),
                                 self.dataModel.stackUnits())


            self.refresh()


    def dataSourceChanged(self):
        self.transform.reset(amin(self.dataModel[0]),
                             amax(self.dataModel[0]),
                             self.dataModel.stackUnits())
        self.refresh()



    def dataPosChanged(self,pos):
        self.dataPos = pos
        self.refresh()


    def refresh(self):
        # if self.parentWidget() and self.dataModel:
        #     self.parentWidget().setWindowTitle("SpImagine %s"%self.dataModel.name())
        self.renderUpdate = True

    def resizeGL(self, width, height):
        # height = max(10,height)

        self._viewport_width, self._viewport_height = width, height

        self.resized = True
        self.resetViewPort()


    def getDataWidthHeight(self):
        if not self.dataModel:
            return 1,1

        dim = array(self.dataModel.size()[1:])[::-1].astype(np.float32)

        dim *= array(self.transform.stackUnits)

        if self.transform.sliceDim==0:
            dim = dim[[2,1]]
        elif self.transform.sliceDim==1:
            dim = dim[[0,2]]
        elif self.transform.sliceDim==2:
            dim = dim[[0,1]]

        w,h = dim[0],dim[1]


        fac = min(1.*self._viewport_width/w,1.*self._viewport_height/h)


        return int(fac*w),int(fac*h)


    def resetViewPort(self):
        w,h = self.getDataWidthHeight()
        glViewport((self._viewport_width-w)//2,(self._viewport_height-h)//2,w,h)



    def paintGL(self):

        self.makeCurrent()

        if not glCheckFramebufferStatus(GL_FRAMEBUFFER)==GL_FRAMEBUFFER_COMPLETE:
            return

        #hack
        if self.resized:
            self.resetViewPort()


        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.dataModel:
            # Draw the render texture
            self.programTex.bind()

            self.texture = fillTexture2d(self.output,self.texture)


            glEnable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)

            self.programTex.enableAttributeArray("position")
            self.programTex.enableAttributeArray("texcoord")
            self.programTex.setAttributeArray("position", self.quadCoord)
            self.programTex.setAttributeArray("texcoord",
                            self.tex_coords_from_xyzoom(self.zoom_x,self.zoom_y,self.zoom_fac))


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
            if self.transform.sliceDim==0:
                out = fliplr(self.dataModel[self.transform.dataPos][:,:,self.transform.slicePos].T)
            elif self.transform.sliceDim==1:
                out = self.dataModel[self.transform.dataPos][:,self.transform.slicePos,:]
            elif self.transform.sliceDim==2:
                out = self.dataModel[self.transform.dataPos][self.transform.slicePos,:,:]

            min_out, max_out = self.transform.minVal, self.transform.maxVal

            if max_out>min_out:
                self.output = (1.*(out-min_out)/(max_out-min_out))**self.transform.gamma
            else:
                self.output = np.zeros_like(out)


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

    def tex_coords_from_xyzoom(self,x0,y0,zoom):
        """returns array of texccords corners when zoomed
        in onto x0,y0 \in [0,1]"""

        q0 = create_quad_coords([0,1,0,1])
        q1 = create_quad_coords([x0,x0,y0,y0])

        return zoom*q0+(1.-zoom)*q1

    # def tex_coords_from_xyzoom(self,x0,y0,zoom):
    #     """returns array of texccords corners given a zoom
    #     and the tex center coords"""
    #
    #     q0 = create_quad_coords([0,1,0,1])
    #     q1 = create_quad_coords([x0,x0,y0,y0])
    #
    #     return zoom*q0+(1.-zoom)*q1

    def getRelativeCoords(self,x0,y0):
        w, h = self.getDataWidthHeight()

        w = w*self.width()/self._viewport_width
        h = w * self.height() / self._viewport_height

        x = 2.*(x0-.5*(self.width()-w))/w-1
        y = 2.*(y0-.5*(self.height()-h))/h-1

        x = (x0-.5*(self.width()-w))/w
        y = 1-(y0-.5*(self.height()-h))/h

        return x,y

    def mousePressEvent(self, event):
        super(GLSliceWidget, self).mousePressEvent(event)

        if event.buttons() == QtCore.Qt.LeftButton:
            self._x0, self._y0 = self.getRelativeCoords(event.x(),event.y())


    def mouseMoveEvent(self, event):

        if event.buttons() == QtCore.Qt.LeftButton:
            x, y = self.getRelativeCoords(event.x(),event.y())
            #print self._x0, x
            self.zoom_x += self.zoom_fac*(self._x0 - x)
            self.zoom_y += self.zoom_fac*(self._y0 - y)
            self._x0, self._y0 = x,y



            self.zoom_x , self.zoom_y = clip(self.zoom_x ,0,1), clip(self.zoom_y,0,1)

        self.refresh()


    def wheelEvent(self, event):
        # get the zoom factor

        # print self.zoom_x,self.zoom_y
        # x, y = self.getRelativeCoords(event.x(),event.y())
        # self.zoom_x , self.zoom_y = clip(x ,0,1), clip(y,0,1)



        self.zoom_fac *=  1.4**(-event.angleDelta().y()/1000.)

        self.zoom_fac = clip(self.zoom_fac,0,1.)

        self.refresh()



class SliceWidget(QtWidgets.QWidget):

    def __init__(self, parent = None,**kwargs):
        super(SliceWidget,self).__init__(parent,**kwargs)

        self.myparent = parent

        self.glSliceWidget = GLSliceWidget(self)



        self.checkSlice = createTristateCheckbox(self,absPath("images/icon_x.png"),
                                                 absPath("images/icon_y.png"),
                                                 absPath("images/icon_z.png"))

        self.sliderSlice = QtWidgets.QSlider(QtCore.Qt.Horizontal,self)
        self.sliderSlice.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.sliderSlice.setTickInterval(1)
        self.sliderSlice.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.sliderSlice.setFocusPolicy(QtCore.Qt.WheelFocus)

        self.sliderSlice.setTracking(True)


        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.spinSlice = QtWidgets.QSpinBox(self)
        self.spinSlice.setStyleSheet("color:white;")
        self.spinSlice.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.spinSlice.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.spinSlice.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)


        self.sliderSlice.valueChanged.connect(self.spinSlice.setValue)
        self.spinSlice.valueChanged.connect(self.sliderSlice.setValue)


        self.setStyleSheet("""
        background-color:black;
        color:white;
        """)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.checkSlice)

        hbox.addWidget(self.sliderSlice)
        hbox.addWidget(self.spinSlice)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.glSliceWidget)
        vbox.addLayout(hbox)


        vbox.setSpacing(1)
        hbox.setSpacing(11)

        self.setLayout(vbox)

        self.glSliceWidget._dataModelChanged.connect(self.dataModelChanged)

        self.setTransform(TransformModel())
        self.sliderSlice.setFocus()


        # self.refresh()


    def setTransform(self, transform):
        self.transform = transform
        self.glSliceWidget.setTransform(transform)
        self.checkSlice.stateChanged.connect(self.transform.setSliceDim)
        self.transform._sliceDimChanged.connect(self.update)


    def update(self):
        if self.glSliceWidget.dataModel:
            dim = self.glSliceWidget.dataModel.size()[1:][::-1][self.transform.sliceDim]

            self.sliderSlice.setRange(0,dim-1)
            self.sliderSlice.setValue(self.transform.slicePos)
            self.spinSlice.setRange(0,dim-1)


    def dataModelChanged(self):
        dataModel = self.glSliceWidget.dataModel
        dataModel._dataSourceChanged.connect(self.dataSourceChanged)
        self.glSliceWidget.transform._slicePosChanged.connect(self.sliderSlice.setValue)
        self.dataSourceChanged()

    def dataSourceChanged(self):
        self.sliderSlice.valueChanged.connect(self.glSliceWidget.transform.setSlicePos)
        self.update()

    def setModel(self,dataModel):
        self.glSliceWidget.setModel(dataModel)

    def wheelEvent(self, event):
        self.sliderSlice.wheelEvent(event)


if __name__ == '__main__':
    from spimagine import DemoData, NumpyData

    app = QtWidgets.QApplication(sys.argv)

    # win = GLSliceWidget(size=QtCore.QSize(500,500))

    win = SliceWidget(size=QtCore.QSize(500,500))


    d = random.uniform(0,1,10*20*30).reshape(10,20,30)

    win.setModel(DataModel(NumpyData(d)))
    # win.setModel(DataModel(DemoData()))

    # win.transform.setBox()
    # win.transform.setPerspective(True)

    win.show()

    win.raise_()

    sys.exit(app.exec_())
