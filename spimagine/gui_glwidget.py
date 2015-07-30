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
logger.setLevel(logging.DEBUG)




import sys
import os
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL

from OpenGL.GL import *
from OpenGL.GL import shaders

import spimagine

from spimagine.volume_render import VolumeRenderer

from spimagine.transform_matrices import *
from spimagine.data_model import DataModel

from spimagine.transfermap import TransferMap
from spimagine.transform_model import TransformModel

from numpy import *
import numpy as np

from spimagine.gui_utils import *

import time

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
uniform sampler2D texture_alpha;
uniform sampler2D texture_LUT;
varying vec2 mytexcoord;

void main()
{
  vec4 col = texture2D(texture,mytexcoord);
  vec4 alph = texture2D(texture_alpha,mytexcoord);

  vec4 lut = texture2D(texture_LUT,col.xy);

  gl_FragColor = vec4(lut.xyz,col.x);

  gl_FragColor.w = 1.0*length(col.xyz);

//gl_FragColor.w = .8;
  //gl_FragColor = lut;

//  gl_FragColor = alph.x>0.01?gl_FragColor:vec4(0,0,0,1.);


}
"""
vertShaderSliceTex ="""
attribute vec3 position;
uniform mat4 mvpMatrix;
attribute vec2 texcoord;
varying vec2 mytexcoord;

void main()
{
    vec3 pos = position;
    gl_Position = mvpMatrix *vec4(pos, 1.0);

    mytexcoord = texcoord;
}
"""

fragShaderSliceTex = """
uniform sampler2D texture;
uniform sampler2D texture_LUT;
varying vec2 mytexcoord;

void main()
{
   vec4 col = texture2D(texture,mytexcoord);

   vec4 lut = texture2D(texture_LUT,col.xy);

  gl_FragColor = vec4(lut.xyz,1.);

  gl_FragColor.w = 1.0*length(gl_FragColor.xyz);
  gl_FragColor.w = 1.0;



}
"""

vertShaderCube ="""
attribute vec3 position;
uniform mat4 mvpMatrix;

varying float zPos;
varying vec2 texcoord;
void main()
{
  vec3 pos = position;
  gl_Position = mvpMatrix *vec4(pos, 1.0);

  texcoord = .5*(1.+.98*gl_Position.xy/gl_Position.w);
  zPos = 0.04+gl_Position.z;
}
"""

fragShaderCube = """

uniform vec4 color;
uniform sampler2D texture_alpha;
varying float zPos;
varying vec2 texcoord;
void main()
{

  // float tnear = texture2D(texture_alpha,mytexcoord.xy).x;


  gl_FragColor = vec4(1.,1.,1.,.3);


  float tnear = texture2D(texture_alpha,texcoord).x;

  float att = exp(-.4*(zPos-tnear));

  gl_FragColor = vec4(att,att,att,.3);

}
"""


vertShaderOverlay ="""
attribute vec3 position;
uniform mat4 mvpMatrix;
varying float zPos;
varying vec2 texcoord;

void main()
{
  gl_Position = mvpMatrix *vec4(position, 1.0);

  texcoord = .5*(1.+.98*gl_Position.xy/gl_Position.w);
  zPos = 0.04+gl_Position.z;
}
"""

fragShaderOverlay = """
varying float zPos;
varying vec2 texcoord;
uniform sampler2D texture_alpha;

void main()
{

  gl_FragColor = vec4(1.,1.,1.,.3);

  float tnear = texture2D(texture_alpha,texcoord).x;
  float att = exp(-1.*(zPos-tnear));

  att = tnear<0.000001?1.:att;
  gl_FragColor = vec4(att,att,att,.3);

}
"""


""" Blending:

the fragment shader computes the input color which is combined with the present color
int the framebuffer to produce the output color 

O = f(D,S) 

input color: (Sc,Sa)
present color: (Dc,Da)
output color: (Oc,Oa)

In default mode this is done by addition (but can be subtraction, max...)

Oc = sc*Sc + dc*Dc
Oa = sa*Sa + da*Da

with the parameters (sc,dc) and (sa,da)



"""
def _next_golden(n):
    res = round((sqrt(5)-1.)/2.*n)
    return int(round((sqrt(5)-1.)/2.*n))



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

        self.setAcceptDrops(True)

        self.reset_render_objects()


        self.renderTimer = QtCore.QTimer(self)
        self.renderTimer.setInterval(10)
        self.renderTimer.timeout.connect(self.onRenderTimer)
        self.renderTimer.start()
        self.renderedSteps = 0

        self.N_PREFETCH = N_PREFETCH

        self.NSubrenderSteps = 5


        self.dataModel = None

        # self.setMouseTracking(True)
        self.setTransforms(TransformModel())

        self.refresh()

    def reset_render_objects(self,n_channels=1):
        self.renderers = []
        self.transforms = []
        self.transfers = []

        self.outputs = []
        self.outputs_alpha = []
        self.outputs_slice = []
        
        for i in range(n_channels):
            rend = VolumeRenderer((spimagine.__DEFAULTWIDTH__,spimagine.__DEFAULTWIDTH__))
            rend.set_projection(mat4_perspective(60,1.,.1,100))
            self.renderers.append(rend)
            self.outputs.append(np.zeros([rend.height,rend.width],dtype = np.float32))
            self.outputs_alpha.append(np.zeros([rend.height,rend.width],dtype = np.float32))
            self.outputs_slice.append(np.zeros((100,100),dtype = np.float32))
            self.transforms.append(TransformModel())
            self.transfers.append(TransferMap())

        for t in self.transforms:
            t._transformChanged.connect(self.refresh)
            t._stackUnitsChanged.connect(self.setStackUnits)
            t._boundsChanged.connect(self.setBounds)
            
    def setModel(self,dataModel):
        logger.debug("setModel")

        self.dataModel = dataModel

        if self.dataModel:
            n_channels = self.dataModel.sizeC()
            self.reset_render_objects(n_channels)
            for t in self.transforms:
                t.setModel(dataModel)

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

            if spimagine._SYSTEM_DARWIN_14:
                path = spimagine._parseFileNameFix(path)

            self.setCursor(QtCore.Qt.BusyCursor)

            if self.dataModel:
                self.dataModel.loadFromPath(path, prefetchSize = self.N_PREFETCH)
            else:
                self.setModel(DataModel.fromPath(path, prefetchSize = self.N_PREFETCH))

            self.setCursor(QtCore.Qt.ArrowCursor)


    def set_colormap(self,name):
        """name should be either jet, hot, gray coolwarm"""

        try:
            arr = spimagine.__COLORMAPDICT__[name]
            self.makeCurrent()
            self.texture_LUT = fillTexture2d(arr.reshape((1,)+arr.shape),self.texture_LUT)
        except:
            print "could not load colormap %s"%name


    def set_colormap_rgb(self,color=[1.,1.,1.]):
        self._set_colormap_array(outer(linspace(0,1.,255),np.array(color)))


    def _set_colormap_array(self,arr):
        """arr should be of shape (N,3) and gives the rgb components of the colormap"""


        self.makeCurrent()
        self.texture_LUT = fillTexture2d(arr.reshape((1,)+arr.shape),self.texture_LUT)
        self.refresh()

    
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

        self.programSlice = QtOpenGL.QGLShaderProgram()
        self.programSlice.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,
                                                  vertShaderSliceTex)
        self.programSlice.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment,
                                                  fragShaderSliceTex)
        self.programSlice.link()
        self.programSlice.bind()
        logger.debug("GLSL programCube log:%s",self.programSlice.log())

        self.programOverlay = QtOpenGL.QGLShaderProgram()
        self.programOverlay.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex,vertShaderOverlay)
        self.programOverlay.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragShaderOverlay)
        self.programOverlay.link()
        self.programOverlay.bind()
        logger.debug("GLSL programOverlay log:%s",self.programOverlay.log())


        glClearColor(0,0,0,1.)
        # glClearColor(1,1,1,.1)

        for t in self.transfers:
            t.init_GL()
            t.fill_texture()

        self.texture = None
        self.textureAlpha = None
        self.textureSlice = None

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

        self.cubeCoords = create_cube_coords([-1,1,-1,1,-1,1])

        self.set_colormap(spimagine.__DEFAULTCOLORMAP__)

        glEnable( GL_BLEND )

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glLineWidth(2.0);
        glBlendFunc(GL_ONE,GL_ONE)

        glEnable( GL_LINE_SMOOTH )
        glDisable(GL_DEPTH_TEST)

        glBlendEquationSeparate(GL_FUNC_ADD, GL_FUNC_ADD)
        glBlendFuncSeparate(GL_ONE, GL_ONE, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # def setTransform(self, transform):
    #     self.transform = transform
    #     self.transform._transformChanged.connect(self.refresh)
    #     self.transform._stackUnitsChanged.connect(self.setStackUnits)
    #     self.transform._boundsChanged.connect(self.setBounds)

    def sizeC(self):
        if self.dataModel:
            return self.dataModel.sizeC()
        else:
            return 1
        
    def setTransforms(self, transforms):
        if not isinstance(transforms,(tuple,list)):
            transforms = [transforms]*self.sizeC()
            
        self.transforms = transforms
        for t in self.transforms:
            t._transformChanged.connect(self.refresh)
            t._stackUnitsChanged.connect(self.setStackUnits)
            t._boundsChanged.connect(self.setBounds)

    def dataModelChanged(self):
        
        if self.dataModel:
            for i,r in enumerate(self.renderers):
                r.set_data(self.dataModel[0][i,...], autoConvert = True)

                self.transforms[i].reset(minVal = amin(self.dataModel[0][i,...]),
                                 maxVal = amax(self.dataModel[0][i,...]),
                                 stackUnits= self.dataModel.stackUnits())

            self.refresh()



    def dataSourceChanged(self):
        self.reset_render_objects(self.dataModel.sizeC())
        for i,r in enumerate(self.renderers):
            r.set_data(self.dataModel[0][i,...], autoConvert = True)

            self.transforms[i].reset(minVal = amin(self.dataModel[0][i,...]),
                                 maxVal = amax(self.dataModel[0][i,...]),
                                 stackUnits= self.dataModel.stackUnits())

        self.refresh()


    def setBounds(self,x1,x2,y1,y2,z1,z2):
        self.cubeCoords = create_cube_coords([x1,x2,y1,y2,z1,z2])
        for r in self.renderers:
            r.set_box_boundaries([x1,x2,y1,y2,z1,z2])

    def setStackUnits(self,px,py,pz):
        logger.debug("setStackUnits to %s"%[px,py,pz])
        for r in self.renderers:
            r.set_units([px,py,pz])


    def dataPosChanged(self,pos):
        for i,r in enumerate(self.renderers):
            r.update_data(self.dataModel[pos][i,...])
            
        self.refresh()


    def refresh(self):
        # if self.parentWidget() and self.dataModel:
        #     self.parentWidget().setWindowTitle("SpImagine %s"%self.dataModel.name())
        print "refresh!"
        self.renderUpdate = True
        self.renderedSteps = 0

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

            # self.textureAlpha = fillTexture2d(self.outputs_alpha[0],self.textureAlpha)

            modelView = self.transforms[0].getModelView()

            proj = self.transforms[0].getProjection()

            self.finalMat = dot(proj,modelView)


            if self.transforms[0].isBox:
                # Draw the cube
                self.programCube.bind()
                self.programCube.setUniformValue("mvpMatrix",QtGui.QMatrix4x4(*self.finalMat.flatten()))
                self.programCube.enableAttributeArray("position")

                self.programCube.setUniformValue("color",QtGui.QVector4D(1.,1.,1.,.6))
                self.programCube.setAttributeArray("position", self.cubeCoords)


                # glActiveTexture(GL_TEXTURE0)
                # glBindTexture(GL_TEXTURE_2D, self.textureAlpha)
                # self.programCube.setUniformValue("texture_alpha",0)

                # glEnable(GL_DEPTH_TEST)
                glDrawArrays(GL_LINES,0,len(self.cubeCoords))


                glDisable(GL_DEPTH_TEST)

            # if self.transform.isSlice and self.sliceOutput is not None:
            #     #draw the slice
            #     self.programSlice.bind()
            #     self.programSlice.setUniformValue("mvpMatrix",QtGui.QMatrix4x4(*self.finalMat.flatten()))
            #     self.programSlice.enableAttributeArray("position")

            #     pos, dim = self.transform.slicePos,self.transform.sliceDim

            #     coords = slice_coords(1.*pos/self.dataModel.size()[2-dim+1],dim)

            #     texcoords = [[0.,0.],[1,0.],[1.,1.],
            #                  [1.,1.],[0.,1.],[0.,0.]]



            #     self.programSlice.setAttributeArray("position", coords)
            #     self.programSlice.setAttributeArray("texcoord", texcoords)

            #     self.textureSlice = fillTexture2d(self.sliceOutput,self.textureSlice)


            #     glActiveTexture(GL_TEXTURE0)
            #     glBindTexture(GL_TEXTURE_2D, self.textureSlice)
            #     self.programSlice.setUniformValue("texture",0)


            #     glActiveTexture(GL_TEXTURE1)
            #     glBindTexture(GL_TEXTURE_2D, self.texture_LUT)
            #     self.programSlice.setUniformValue("texture_LUT",1)


            #     glDrawArrays(GL_TRIANGLES,0,len(coords))

            # Draw the render texture
            self.programTex.bind()

            for output,output_alpha,transf in zip(self.outputs,self.outputs_alpha, self.transfers):

                self.texture = fillTexture2d(output,self.texture)
                self.textureAlpha = fillTexture2d(output_alpha,self.textureAlpha)

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
                glBindTexture(GL_TEXTURE_2D, self.textureAlpha)
                self.programTex.setUniformValue("texture_alpha",1)

                glActiveTexture(GL_TEXTURE2)
                glBindTexture(GL_TEXTURE_2D, transf._texture)
                self.programTex.setUniformValue("texture_LUT",2)


                glDrawArrays(GL_TRIANGLES,0,len(self.quadCoord))




    def render(self):
        logger.debug("render")
        if self.dataModel:
            # import time

            for i,r in enumerate(self.renderers):
                
                r.set_modelView(self.transforms[i].getUnscaledModelView())
                r.set_projection(self.transforms[i].getProjection())
                r.set_min_val(self.transforms[i].minVal)

                r.set_max_val(self.transforms[i].maxVal)
                r.set_gamma(self.transforms[i].gamma)
                r.set_alpha_pow(self.transforms[i].alphaPow)

                
                if self.transforms[i].isIso:
                    renderMethod = "iso_surface"
                
                else:
                    renderMethod = "max_project_part"

                t = time.time()
                print "haha", self.NSubrenderSteps, _next_golden(self.NSubrenderSteps)

                self.outputs[i], self.outputs_alpha[i] = r.render(method = renderMethod, return_alpha = True, numParts = self.NSubrenderSteps, currentPart = (self.renderedSteps*_next_golden(self.NSubrenderSteps)) %self.NSubrenderSteps)

                logger.debug("time to render channel: %.2f ms"%(1000.*(time.time()-t)))

            # if self.transform.isSlice:
            #     if self.transform.sliceDim==0:
            #         out = self.dataModel[self.transform.dataPos][i,:,:,self.transform.slicePos]
            #     elif self.transform.sliceDim==1:
            #         out = self.dataModel[self.transform.dataPos][i,:,self.transform.slicePos,:]
            #     elif self.transform.sliceDim==2:
            #         out = self.dataModel[self.transform.dataPos][i,self.transform.slicePos,:,:]

            #     self.sliceOutput = (1.*(out-np.amin(out))/(np.amax(out)-np.amin(out)))

            
    def saveFrame(self,fName):
        """FIXME: scaling behaviour still hast to be implemented (e.g. after setGamma)"""
        logger.info("saving frame as %s", fName)

        self.render()
        self.paintGL()
        glFlush()
        self.grabFrameBuffer().save(fName)

        
    def onRenderTimer(self):
        # if self.renderUpdate:
        #     self.render()
        #     self.renderUpdate = False
        #     self.updateGL()
        if self.renderedSteps<self.NSubrenderSteps:
            # print ((self.renderedSteps*7)%self.NSubrenderSteps)
            s = time.time()
            self.render()
            logger.debug("time to render:  %.2f"%(1000.*(time.time()-s)))
            self.renderedSteps +=1 
            self.updateGL()



    def wheelEvent(self, event):
        """ self.transform.zoom should be within [1,2]"""
        newZoom = self.transforms[0].zoom * 1.2**(event.delta()/1400.)
        newZoom = clip(newZoom,.4,3)
        for t in self.transforms:
            t.setZoom(newZoom)

        logger.debug("newZoom: %s",newZoom)
        # self.refresh()


    def posToVec3(self,x,y, r0 = .8, isRot = True ):
        x, y = 2.*x/self.width-1.,1.-2.*y/self.width
        r = sqrt(x*x+y*y)
        if r>r0-1.e-7:
            x,y = 1.*x*r0/r, 1.*y*r0/r
        z = sqrt(max(0,r0**2-x*x-y*y))
        if isRot:
            M = linalg.inv(self.transforms[0].quatRot.toRotation3())
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
            (self._x0, self._y0), self._invRotM = self.posToVec2(event.x(),event.y()), linalg.inv(self.transforms[0].quatRot.toRotation3())

        # self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        super(GLWidget, self).mouseReleaseEvent(event)

        # self.setCursor(QtCore.Qt.ArrowCursor)

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

            for t in self.transforms[:]:
                t.setQuaternion(t.quatRot*q)

        #Translation
        if event.buttons() == QtCore.Qt.RightButton:
            x, y = self.posToVec2(event.x(),event.y())

            dx, dy, foo = dot(self._invRotM,[x-self._x0, y-self._y0,0])

            for t in self.transforms[:]:
                t.addTranslate(dx,dy,foo)
                
            self._x0,self._y0 = x,y

        self.refresh()



def test_sphere():
    from data_model import DataModel, NumpyData, SpimData, TiffData

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(500,500))


    x = np.linspace(-1,1,128)
    Z,Y,X = np.meshgrid(x,x,x)
    # R = sqrt(Z**2+Y**2+(X-.35)**2)
    # R2 = sqrt(Z**2+Y**2+(X+.35)**2)

    # d = 100.*exp(-10*R**2)+.0*np.random.normal(0,1.,X.shape)

    # d += 100.*exp(-10*R2**2)+.0*np.random.normal(0,1.,X.shape)

    Ns = 5
    r = .6
    phi = linspace(0,2*pi,Ns+1)[:-1]
    d = zeros_like(X)
    for p in phi:
        d += 100.*exp(-10*(Z**2+(Y-r*sin(p))**2+(X-r*cos(p))**2))

    
    d = np.array([d,40*X])
    print d.shape

    m = DataModel(NumpyData(d))

    win.setModel(m)


    win.transform.setValueScale(0,40)

    win.transform.setIso(True)

    win.show()

    win.raise_()

    sys.exit(app.exec_())


def test_multi():
    from data_model import DataModel, NumpyData

    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800,800))


    
    x = np.linspace(-1,1,400)
    Z,Y,X = np.meshgrid(x,x,x)
    R1 = sqrt(Z**2+Y**2+(X-.35)**2)
    R2 = sqrt(Z**2+Y**2+(X+.35)**2)
    # R3 = sqrt(Z**2+Y**2+(X)**2)

    d1 = 100.*exp(-7*R1**2)

    d2 = 100.*exp(-7*R2**2)

    d2[100:110,100:110,100:110] = 100
    # d3 = 100.*exp(-4*R3**2)

    d = np.array([d1,d2])
    print d.shape
    m = DataModel(NumpyData(d))

    print m.size()
    win.setModel(m)


    
    win.show()

    win.transfers[0].set_cmap((1.,0.,0.,1.))
    win.transfers[0].fill_texture()

    win.transfers[1].set_cmap((0.,1.,0.,1.))
    win.transfers[1].fill_texture()

    # win.transfers[2].set_cmap((0.,0.,1.,1.))
    # win.transfers[2].fill_texture()

    win.raise_()

    sys.exit(app.exec_())

    
def test_demo():

    from data_model import DataModel, DemoData, SpimData, TiffData, NumpyData
    import imgtools
    
    app = QtGui.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800,800))

    

    # sys.exit(app.exec_())

    win.setModel(DataModel(DemoData()))


    # win.transform.setValueScale(0,10000.)
    # win.transform.setIso(True)

    win.show()


    win.raise_()

    sys.exit(app.exec_())



if __name__ == '__main__':

    # test_sphere()

    # test_demo()

    test_multi()

    
