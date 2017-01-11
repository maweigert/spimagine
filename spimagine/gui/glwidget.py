#!/usr/bin/env python

"""

The rendering widget

It renderes a projection via the OpenCL (defined in volumerender.py)
into a texture which is drawn by simple OpenGL calls onto the canvas.

It should handle all user interaction via a transformation model.


author: Martin Weigert
email: mweigert@mpi-cbg.de

understanding glBlendFunc:

first color:     d
second color:    s
resulting color: c

c = s*S + d*D

where S and D are set with glBlendFunc(S,D)

e.g. glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

c = s*s.w + d*(1-s.w)



"""

from __future__ import absolute_import, print_function, unicode_literals, division

import logging

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

import sys
import os
from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtOpenGL
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader
from OpenGL.GL import *
import OpenGL.arrays.vbo as glvbo
import spimagine
from spimagine.volumerender.volumerender import VolumeRenderer
from spimagine.utils.transform_matrices import *
from spimagine.models.transform_model import TransformModel
from spimagine.models.data_model import DataModel
from spimagine.gui.mesh import Mesh, SphericalMesh, EllipsoidMesh
import numpy as np
from spimagine.gui.gui_utils import *

# on windows numpy.linalg.inv crashes without notice, so we have to import scipy.linalg
if os.name == "nt":
    from scipy import linalg
else:
    from numpy import linalg

import time
from spimagine.utils.quaternion import Quaternion


# from spimagine.shaders import vertShaderTex, fragShaderTex, vertShaderCube, fragShaderCube

# logger.setLevel(logging.DEBUG)

def _next_golden(n):
    res = round((np.sqrt(5) - 1.) / 2. * n)
    return int(round((np.sqrt(5) - 1.) / 2. * n))


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

    _BACKGROUND_BLACK = (0., 0., 0., 0.)
    _BACKGROUND_WHITE = (1., 1., 1., 0.)

    def __init__(self, parent=None, N_PREFETCH=0, **kwargs):
        logger.debug("init")

        super(GLWidget, self).__init__(parent, **kwargs)

        self.parent = parent
        self.texture_LUT = None

        self.setAcceptDrops(True)

        self.renderer = VolumeRenderer((spimagine.config.__DEFAULTWIDTH__,
                                        spimagine.config.__DEFAULTWIDTH__))

        self.renderer.set_projection(mat4_perspective(60, 1., .1, 100))
        # self.renderer.set_projection(projMatOrtho(-2,2,-2,2,-10,10))

        self.output = np.zeros([self.renderer.height, self.renderer.width], dtype=np.float32)
        self.output_alpha = np.zeros([self.renderer.height, self.renderer.width], dtype=np.float32)

        self.sliceOutput = np.zeros((100, 100), dtype=np.float32)

        self.setTransform(TransformModel())

        self.renderTimer = QtCore.QTimer(self)
        self.renderTimer.setInterval(10)
        self.renderTimer.timeout.connect(self.onRenderTimer)
        self.renderTimer.start()
        self.renderedSteps = 0

        self.N_PREFETCH = N_PREFETCH

        self.NSubrenderSteps = 1

        self.dataModel = None

        self.meshes = []

        # self.setMouseTracking(True)

        self._dataModelChanged.connect(self.dataModelChanged)

        self.refresh()

        # self.installEventFilter(self)

    def set_background_mode_black(self, mode_back=True):
        self._background_mode_black = mode_back
        self.refresh()

    def setModel(self, dataModel):
        logger.debug("setModel to %s" % dataModel)
        if self.dataModel is None or (self.dataModel != dataModel):
            self.dataModel = dataModel
            self.transform.setModel(dataModel)
            self.dataModel._dataSourceChanged.connect(self.dataSourceChanged)
            self.dataModel._dataPosChanged.connect(self.dataPosChanged)
            self._dataModelChanged.emit()




    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):

        for url in event.mimeData().urls():

            # path = url.toLocalFile().toLocal8Bit().data()

            path = url.toLocalFile()

            if spimagine.config.__SYSTEM_DARWIN__:
                path = spimagine.config._parseFileNameFix(path)

            self.setCursor(QtCore.Qt.BusyCursor)

            if self.dataModel:
                self.dataModel.loadFromPath(path, prefetchSize=self.N_PREFETCH)
            else:
                self.setModel(DataModel.fromPath(path, prefetchSize=self.N_PREFETCH))

            self.setCursor(QtCore.Qt.ArrowCursor)

    def set_colormap(self, name):
        """name should be either jet, hot, gray, coolwarm"""

        try:
            arr = spimagine.config.__COLORMAPDICT__[name]
            self._set_colormap_array(arr)
        except KeyError:
            print("could not load colormap '%s'" % name)
            print("valid names: %s" % list(spimagine.config.__COLORMAPDICT__.keys()))

    def set_colormap_rgb(self, color=[1., 1., 1.]):
        self._set_colormap_array(np.outer(np.linspace(0, 1., 255), np.array(color)))

    def _set_colormap_array(self, arr):
        """arr should be of shape (N,3) and gives the rgb components of the colormap"""
        self.makeCurrent()
        self.texture_LUT = fillTexture2d(arr.reshape((1,) + arr.shape), self.texture_LUT)
        self.refresh()

    def _shader_from_file(self, fname_vert, fname_frag):
        shader = QOpenGLShaderProgram()
        shader.addShaderFromSourceFile(QOpenGLShader.Vertex, fname_vert)
        shader.addShaderFromSourceFile(QOpenGLShader.Fragment, fname_frag)
        shader.link()
        shader.bind()
        logger.debug("GLSL program log:%s", shader.log())
        return shader

    def initializeGL(self):

        self.resized = True

        logger.debug("initializeGL")

        self.programTex = self._shader_from_file(absPath("shaders/texture.vert"),
                                                 absPath("shaders/texture.frag"))

        self.programCube = self._shader_from_file(absPath("shaders/box.vert"),
                                                  absPath("shaders/box.frag"))

        self.programSlice = self._shader_from_file(absPath("shaders/slice.vert"),
                                                   absPath("shaders/slice.frag"))

        self.programMesh = self._shader_from_file(absPath("shaders/mesh.vert"),
                                                  absPath("shaders/mesh.frag"))

        self.programMeshLight = self._shader_from_file(
            absPath("shaders/mesh_light.vert"),
            absPath("shaders/mesh_light.frag"))

        self.texture = None
        self.textureAlpha = None
        self.textureSlice = None

        self.quadCoord = np.array([[-1., -1., 0.],
                                   [1., -1., 0.],
                                   [1., 1., 0.],
                                   [1., 1., 0.],
                                   [-1., 1., 0.],
                                   [-1., -1., 0.]])

        self.quadCoordTex = np.array([[0, 0],
                                      [1., 0.],
                                      [1., 1.],
                                      [1., 1.],
                                      [0, 1.],
                                      [0, 0]])

        # self.cubeCoords = create_cube_coords([-1,1,-1,1,-1,1])

        self.set_colormap(spimagine.config.__DEFAULTCOLORMAP__)

        glEnable(GL_BLEND)

        # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


        # glLineWidth(1.0);
        glBlendFunc(GL_ONE, GL_ONE)

        glEnable(GL_LINE_SMOOTH);
        glDisable(GL_DEPTH_TEST)

        # self.set_background_color(0,0,0,.0)
        self.set_background_mode_black(True)
        self.clear_canvas()


        # self.set_background_color(1,1,1,.6)

    def clear_canvas(self):
        if self._background_mode_black:
            glClearColor(*self._BACKGROUND_BLACK)
        else:
            glClearColor(*self._BACKGROUND_WHITE)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def setTransform(self, transform):
        self.transform = transform
        self.transform._transformChanged.connect(self.refresh)
        self.transform._stackUnitsChanged.connect(self.setStackUnits)
        self.transform._boundsChanged.connect(self.setBounds)

    def dataModelChanged(self):
        logger.debug("+++++++++ data model changed")

        if self.dataModel:
            logger.debug("dataModelchanged: min %s max %s" % (np.amin(self.dataModel[0]),
                                                              np.amax(self.dataModel[0])))

            self.renderer.set_data(self.dataModel[0], autoConvert=True)

            self.transform.reset(minVal=np.amin(self.dataModel[0]),
                                 maxVal=np.amax(self.dataModel[0]),
                                 stackUnits=self.dataModel.stackUnits())


            self.meshes = []
            self.refresh()

    def set_background_color(self, r, g, b, a=1.):
        self._background_color = (r, g, b, a)
        glClearColor(r, g, b, a)

    def dataSourceChanged(self):

        logger.debug("dataSourcechanged: min %s max %s" % (np.amin(self.dataModel[0]),
                                                           np.amax(self.dataModel[0])))
        self.renderer.set_data(self.dataModel[0], autoConvert=True)

        self.transform.reset(minVal=np.amin(self.dataModel[0]),
                             maxVal=np.amax(self.dataModel[0]),
                             stackUnits=self.dataModel.stackUnits())

        self.refresh()

    def setBounds(self, x1, x2, y1, y2, z1, z2):
        self.cubeCoords = create_cube_coords([x1, x2, y1, y2, z1, z2])
        self.renderer.set_box_boundaries([x1, x2, y1, y2, z1, z2])

    def setStackUnits(self, px, py, pz):
        logger.debug("setStackUnits to %s" % [px, py, pz])
        self.renderer.set_units([px, py, pz])

    def dataPosChanged(self, pos):
        self.renderer.update_data(self.dataModel[pos])
        self.refresh()

    def refresh(self):
        # if self.parentWidget() and self.dataModel:
        #     self.parentWidget().setWindowTitle("SpImagine %s"%self.dataModel.name())

        self.renderUpdate = True
        self.renderedSteps = 0

    def resizeGL(self, width, height):
        # somehow in qt5 the OpenGLWidget width/height parameters above are double the value of self.width/height
        self._viewport_width, self._viewport_height = width, height

    def add_mesh(self, mesh=SphericalMesh()):
        """
        adds a mesh with vertices and facecolor/edgecolor to be drawn

        mesh is an instance of spimagine.gui.Mesh, e.g.

        mesh = Mesh(vertices = [[0,1,0],[0,1,0],...],
                    normals = [[0,1,0],[0,1,0],...],
                    facecolor = (1.,.4,.4,.2),
                    edgecolor = None,...)

        there are some predefined meshes like
        SphericalMesh, EllipsoidMesh ...
        """

        self.meshes.append([mesh,
                            glvbo.VBO(mesh.vertices.astype(np.float32, copy=False)),
                            glvbo.VBO(np.array(mesh.normals).astype(np.float32, copy=False)),
                            glvbo.VBO(np.array(mesh.indices).astype(np.uint32, copy=False),
                                      target=GL_ELEMENT_ARRAY_BUFFER)])

        self.refresh()
        # sort according to opacity as the opaque objects should be drawn first
        # self.meshes.sort(key=lambda x: x[0].alpha, reverse=True)

    def _paintGL_render(self):
        # Draw the render texture

        self.programTex.bind()

        self.texture = fillTexture2d(self.output, self.texture)

        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)

        self.programTex.enableAttributeArray("position")
        self.programTex.enableAttributeArray("texcoord")
        self.programTex.setAttributeArray("position", self.quadCoord)
        self.programTex.setAttributeArray("texcoord", self.quadCoordTex)

        self.programTex.setUniformValue("is_mode_black", self._background_mode_black)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        self.programTex.setUniformValue("texture", 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.textureAlpha)
        self.programTex.setUniformValue("texture_alpha", 1)

        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.texture_LUT)
        self.programTex.setUniformValue("texture_LUT", 2)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glDrawArrays(GL_TRIANGLES, 0, len(self.quadCoord))

    def _paintGL_slice(self):
        # draw the slice
        self.programSlice.bind()
        self.programSlice.setUniformValue("mvpMatrix", QtGui.QMatrix4x4(*self._mat_modelviewproject.flatten()))
        self.programSlice.enableAttributeArray("position")

        pos, dim = self.transform.slicePos, self.transform.sliceDim

        coords = slice_coords(1. * pos / self.dataModel.size()[2 - dim + 1], dim)

        texcoords = [[0., 0.], [1, 0.], [1., 1.],
                     [1., 1.], [0., 1.], [0., 0.]]

        self.programSlice.setAttributeArray("position", coords)
        self.programSlice.setAttributeArray("texcoord", texcoords)

        self.textureSlice = fillTexture2d(self.sliceOutput, self.textureSlice)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textureSlice)
        self.programSlice.setUniformValue("texture", 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.texture_LUT)
        self.programSlice.setUniformValue("texture_LUT", 1)

        glDrawArrays(GL_TRIANGLES, 0, len(coords))

    def _paintGL_box(self):

        glEnable(GL_BLEND)
        # Draw the cube
        self.programCube.bind()
        self.programCube.setUniformValue("mvpMatrix", QtGui.QMatrix4x4(*self._mat_modelviewproject.flatten()))
        self.programCube.enableAttributeArray("position")

        if self._background_mode_black:
            self.programCube.setUniformValue("color",
                                             QtGui.QVector4D(1, 1, 1, 0.6))
        else:
            self.programCube.setUniformValue("color",
                                             QtGui.QVector4D(0, 0, 0, 0.6))

        self.programCube.setAttributeArray("position", self.cubeCoords)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.textureAlpha)
        self.programCube.setUniformValue("texture_alpha", 0)

        glEnable(GL_DEPTH_TEST)
        # glBlendFunc(GL_ONE_MINUS_SRC_ALPHA, GL_SRC_ALPHA)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDrawArrays(GL_LINES, 0, len(self.cubeCoords))
        glDisable(GL_DEPTH_TEST)

    def _paintGL_mesh(self, mesh, vbo_vertices, vbo_normals, vbo_indices):
        """
        paint a mesh (which has all the coordinates and colors in it
        """
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        prog = self.programMeshLight
        prog.bind()
        prog.setUniformValue("mvpMatrix",
                             QtGui.QMatrix4x4(*self._mat_modelviewproject.flatten()))

        prog.setUniformValue("mvMatrix",
                             QtGui.QMatrix4x4(*self._mat_modelview.flatten()))

        prog.setUniformValue("normMatrix",
                             QtGui.QMatrix4x4(*self._mat_normal.flatten()))

        if mesh.light:
            prog.setUniformValue("light",
                                 QtGui.QVector3D(*mesh.light))
            prog.setUniformValue("light_components",
                                 QtGui.QVector3D(.2, .5, .3))
        else:
            prog.setUniformValue("light",
                                 QtGui.QVector3D(0, 0, 0))
            prog.setUniformValue("light_components",
                                 QtGui.QVector3D(1., 0, 0))

        if not mesh.facecolor is None:
            r, g, b = mesh.facecolor[:3]
            a = mesh.alpha
            prog.setUniformValue("color",
                                 QtGui.QVector4D(r, g, b, a))

            prog.enableAttributeArray("position")
            vbo_vertices.bind()

            glVertexAttribPointer(prog.attributeLocation("position"), 3, GL_FLOAT, GL_FALSE, 0, vbo_vertices)

            prog.enableAttributeArray("normal")
            vbo_normals.bind()
            glVertexAttribPointer(prog.attributeLocation("normal"), 3, GL_FLOAT, GL_FALSE, 0, vbo_normals)

            vbo_indices.bind()

            glDrawElements(GL_TRIANGLES, len(vbo_indices.data), GL_UNSIGNED_INT, None)

            vbo_indices.unbind()
            vbo_vertices.unbind()

            glDisable(GL_DEPTH_TEST)
            prog.disableAttributeArray("position")
            prog.disableAttributeArray("normal")



            #
            # if not mesh.edgecolor is None:
            #     r, g, b = mesh.edgecolor
            #     a = mesh.alpha
            #
            #     prog.enableAttributeArray("position")
            #     vbo_vertices.bind()
            #     glVertexAttribPointer(prog.attributeLocation("position"), 2, GL_FLOAT, GL_FALSE, 0, vbo_edges)
            #
            #     prog.setUniformValue("color",
            #                          QtGui.QVector4D(r, g, b, a))
            #
            #     glDrawArrays(GL_LINES, 0, len(mesh.edges))



    def paintGL(self):


        self.makeCurrent()

        if not glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
            return

        w = max(self._viewport_width, self._viewport_height)
        # force viewport to always be a square
        glViewport((self._viewport_width - w) // 2, (self._viewport_height - w) // 2, w, w)

        self.clear_canvas()

        self._mat_modelview = self.transform.getModelView()
        self._mat_proj = self.transform.getProjection()
        self._mat_normal = np.linalg.inv(self._mat_modelview).T

        self._mat_modelviewproject = np.dot(self._mat_proj, self._mat_modelview)

        if self.dataModel:

            self.textureAlpha = fillTexture2d(self.output_alpha, self.textureAlpha)

            if self.transform.isBox:
                self._paintGL_box()

            if self.transform.isSlice and self.sliceOutput is not None:
                self._paintGL_slice()

            self._paintGL_render()

        for (m, vbo_verts, vbo_normals, vbo_indices) in self.meshes:
            self._paintGL_mesh(m, vbo_verts, vbo_normals, vbo_indices)

    def render(self):
        logger.debug("render")

        if self.dataModel:

            self.renderer.set_modelView(self.transform.getUnscaledModelView())
            self.renderer.set_projection(self.transform.getProjection())
            self.renderer.set_min_val(self.transform.minVal)

            self.renderer.set_max_val(self.transform.maxVal)
            self.renderer.set_gamma(self.transform.gamma)
            self.renderer.set_alpha_pow(self.transform.alphaPow)

            self.renderer.set_occ_strength(self.transform.occ_strength)
            self.renderer.set_occ_radius(self.transform.occ_radius)
            self.renderer.set_occ_n_points(self.transform.occ_n_points)

            if self.transform.isIso:
                renderMethod = "iso_surface"

            else:
                renderMethod = "max_project"

            self.renderer.render(method=renderMethod, return_alpha=True, numParts=self.NSubrenderSteps, currentPart=(
                                                                                                                        self.renderedSteps * _next_golden(
                                                                                                                            self.NSubrenderSteps)) % self.NSubrenderSteps)
            self.output, self.output_alpha = self.renderer.output, self.renderer.output_alpha

            if self.transform.isSlice:
                if self.transform.sliceDim == 0:
                    out = self.dataModel[self.transform.dataPos][:, :, self.transform.slicePos]
                elif self.transform.sliceDim == 1:
                    out = self.dataModel[self.transform.dataPos][:, self.transform.slicePos, :]
                elif self.transform.sliceDim == 2:
                    out = self.dataModel[self.transform.dataPos][self.transform.slicePos, :, :]

                min_out, max_out = np.amin(out), np.amax(out)
                if max_out > min_out:
                    self.sliceOutput = (1. * (out - min_out) / (max_out - min_out))
                else:
                    self.sliceOutput = np.zeros_like(out)

    def getFrame(self):
        self.render()
        self.paintGL()
        glFlush()
        ilm = self.grabFrameBuffer()
        im = im.convertToFormat(QtGui.QImage.Format_RGB32)

        width = im.width()
        height = im.height()

        ptr = im.bits()
        ptr.setsize(im.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # Copies the data
        return arr[..., [2, 1, 0, 3]].copy()

    def saveFrame(self, fName):
        """FIXME: scaling behaviour still hast to be implemented (e.g. after setGamma)"""
        logger.info("saving frame as %s", fName)

        # has to be png

        name, ext = os.path.splitext(fName)
        if ext != ".png":
            fName = name + ".png"

        self.render()
        self.paintGL()
        glFlush()
        im = self.grabFrameBuffer()
        im.save(fName)

    def onRenderTimer(self):
        # if self.renderUpdate:
        #     self.render()
        #     self.renderUpdate = False
        #     self.updateGL()
        if self.renderedSteps < self.NSubrenderSteps:
            # print ((self.renderedSteps*7)%self.NSubrenderSteps)
            s = time.time()
            self.render()
            logger.debug("time to render:  %.2f" % (1000. * (time.time() - s)))
            self.renderedSteps += 1
            self.updateGL()

    def wheelEvent(self, event):
        """ self.transform.zoom should be within [1,2]"""
        newZoom = self.transform.zoom * 1.2 ** (event.angleDelta().y() / 1000.)
        newZoom = np.clip(newZoom, .4, 3)
        self.transform.setZoom(newZoom)

        logger.debug("newZoom: %s", newZoom)
        # self.refresh()

    def posToVec3(self, x, y, r0=.8, isRot=True):
        x, y = 2. * x / self.width() - 1., 1. - 2. * y / self.width()

        r = np.sqrt(x * x + y * y)
        if r > r0 - 1.e-7:
            x, y = 1. * x * r0 / r, 1. * y * r0 / r
        z = np.sqrt(max(0, r0 ** 2 - x * x - y * y))

        if isRot:
            M = np.linalg.inv(self.transform.quatRot.toRotation3())
            x, y, z = np.dot(M, [x, y, z])

        return x, y, z

    def posToVec2(self, x, y):
        x, y = 2. * x / self.width() - 1., 1. - 2. * y / self.width()
        return x, y

    def mousePressEvent(self, event):
        super(GLWidget, self).mousePressEvent(event)

        if event.buttons() == QtCore.Qt.LeftButton:
            self._x0, self._y0, self._z0 = self.posToVec3(event.x(), event.y())

        if event.buttons() == QtCore.Qt.RightButton:
            (self._x0, self._y0), self._invRotM = self.posToVec2(event.x(), event.y()), linalg.inv(
                self.transform.quatRot.toRotation3())

            # self.setCursor(QtCore.Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        super(GLWidget, self).mouseReleaseEvent(event)

        # self.setCursor(QtCore.Qt.ArrowCursor)

    def mouseMoveEvent(self, event):

        # c = append(self.cubeCoords,ones(24)[:,newaxis],axis=1)
        # cUser = dot(c,self.finalMat)
        # cUser = cUser[:,:3]/cUser[:,-1,newaxis]
        # print self.finalMat
        # print c[0], cUser[0]
        # Rotation


        if event.buttons() == QtCore.Qt.LeftButton:
            x1, y1, z1 = self.posToVec3(event.x(), event.y())
            logger.debug("mouse position: %s %s %s " % (x1, y1, z1))
            n = np.cross(np.array([self._x0, self._y0, self._z0]), np.array([x1, y1, z1]))
            nnorm = linalg.norm(n)
            if np.abs(nnorm) >= 1.:
                nnorm *= 1. / np.abs(nnorm)
            w = np.arcsin(nnorm)
            n *= 1. / (nnorm + 1.e-10)
            q = Quaternion(np.cos(.5 * w), *(np.sin(.5 * w) * n))
            self.transform.setQuaternion(self.transform.quatRot * q)

        # Translation
        if event.buttons() == QtCore.Qt.RightButton:
            x, y = self.posToVec2(event.x(), event.y())

            dx, dy, foo = np.dot(self._invRotM, [x - self._x0, y - self._y0, 0])

            self.transform.addTranslate(dx, dy, foo)
            self._x0, self._y0 = x, y

        self.refresh()

    def _enforce_resize(self):
        """ this is to enforce the resizeGL event """
        self.resize(self.width() + 1, self.height())
        self.resize(self.width() - 1, self.height())

    def onScreenNumberChange(self, evt):
        self._enforce_resize()

    def _get_screen_number(self):
        return QtGui.QGuiApplication.instance().desktop().screenNumber(QtGui.QCursor.pos())

    def moveEvent(self, evt):
        current_screen = self._get_screen_number()
        if hasattr(self, "_current_screen") and self._current_screen != current_screen:
            self.onScreenNumberChange(evt)

        self._current_screen = current_screen


def test_sphere():
    from data_model import DataModel, NumpyData, SpimData, TiffData

    app = QtWidgets.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(500, 500))

    x = np.linspace(-1, 1, 128)
    Z, Y, X = np.meshgrid(x, x, x)
    # R = sqrt(Z**2+Y**2+(X-.35)**2)
    # R2 = sqrt(Z**2+Y**2+(X+.35)**2)

    # d = 100.*exp(-10*R**2)+.0*np.random.normal(0,1.,X.shape)

    # d += 100.*exp(-10*R2**2)+.0*np.random.normal(0,1.,X.shape)

    Ns = 5
    r = .6
    phi = np.linspace(0, 2 * pi, Ns + 1)[:-1]
    d = np.zeros_like(X)
    for p in phi:
        d += 100. * np.exp(-10 * (Z ** 2 + (Y - r * np.sin(p)) ** 2 + (X - r * np.cos(p)) ** 2))

    win.setModel(DataModel(NumpyData(d)))

    win.transform.setValueScale(0, 40)

    win.show()

    win.raise_()

    sys.exit(app.exec_())


def test_empty():
    from spimagine import DataModel, NumpyData, SpimData, TiffData

    app = QtWidgets.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(1000, 1000))

    d = np.zeros((800,) * 3, np.float32)

    d[0, 0, 0] = 1.


    win.show()

    win.raise_()

    QtCore.QThread.msleep(1000)

    win.setModel(DataModel(NumpyData(d)))

    sys.exit(app.exec_())


def test_demo():
    from data_model import DataModel, DemoData, SpimData, TiffData, NumpyData

    app = QtWidgets.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800, 800))

    win.setModel(DataModel(DemoData()))

    win.show()

    win.raise_()

    sys.exit(app.exec_())


def test_demo_simple():
    from spimagine import DataModel, DemoData

    app = QtWidgets.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800, 800))

    win.setModel(DataModel(DemoData()))
    win.show()

    win.raise_()

    sys.exit(app.exec_())


def test_surface():
    from spimagine import DataModel, DemoData

    app = QtWidgets.QApplication(sys.argv)

    win = GLWidget(size=QtCore.QSize(800, 600))

    win.setModel(DataModel(DemoData()))

    # win.add_surface_sphere((0,0,0), 1., facecolor = (.0,.3,1.,.5),
    #                                 Nphi = 30, Ntheta=20)

    # win.add_mesh(SphericalMesh(r = .8,
    #                            facecolor = (1.,0.,0.),
    #                            #edgecolor = (1.,1.,1.),
    #                            edgecolor = None,
    #                            alpha = .3))

    # win.add_mesh(EllipsoidMesh(rs = (.3,.6,.6),
    #                             pos = (0,0,-.5),
    #
    #                            facecolor = (0.,1.,1.),
    #                            #edgecolor = (1.,1.,1.),
    #                            edgecolor = None,
    #                            alpha = .4))
    #

    win.show()

    win.raise_()

    sys.exit(app.exec_())


if __name__ == '__main__':
    test_empty()


    # test_sphere()

    # test_demo_simple()
    # test_surface()
