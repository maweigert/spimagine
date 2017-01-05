#!/usr/bin/env python


from __future__ import absolute_import, print_function, unicode_literals, division

import logging

logger = logging.getLogger(__name__)

import sys
import os
import numpy as np

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader, QImage, QOpenGLTexture
from PyQt5.QtWidgets import QOpenGLWidget


class BaseGLWidget(QOpenGLWidget):
    _BACKGROUND_BLACK = (0., 0., 0., 1.)
    _BACKGROUND_WHITE = (1., 1., 1., 1.)

    def __init__(self, parent=None, render_intervall=50, **kwargs):
        logger.debug("init")
        super(BaseGLWidget, self).__init__(parent, **kwargs)
        self.parent = parent

        self._render_update = True
        self._render_timer = QtCore.QTimer(self)
        self._render_timer.setInterval(render_intervall)
        self._render_timer.timeout.connect(self.onRenderTimer)
        self._render_timer.start()

    def initializeGL(self):
        self.gl = self.context().versionFunctions()
        self.gl.initializeOpenGLFunctions()
        self.set_background_mode_black()

    def resizeGL(self, width, height):
        # somehow in qt5 the OpenGLWidget width/height parameters above are double the value of self.width/height
        self._viewport_width, self._viewport_height = width, height
        w = max(self._viewport_width, self._viewport_height)
        # force viewport to always be a square
        self.gl.glViewport((self._viewport_width - w) // 2, (self._viewport_height - w) // 2, w, w)

    ################################################################

    def paintGL(self):
        print("clearing")
        self.clear_canvas()

    def render(self):
        print("render")


    ################################################################

    def refresh(self):
        self._render_update = True

    def onRenderTimer(self):
        if self._render_update:
            self.render()
            self._render_update = False
            self.update()


    def set_background_mode_black(self, mode_back=True):
        self._background_mode_black = mode_back
        if self._background_mode_black:
            self.set_background_color(*self._BACKGROUND_BLACK)
        else:
            self.set_background_color(*self._BACKGROUND_WHITE)
        self.refresh()

    def set_background_color(self, r, g, b, a=1.):
        self._background_color = (r, g, b, a)
        self.gl.glClearColor(r, g, b, a)

    def clear_canvas(self):
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)

    ################################################################

    def _shader_from_file(self, fname_vert, fname_frag):
        shader = QOpenGLShaderProgram()
        shader.addShaderFromSourceFile(QOpenGLShader.Vertex, fname_vert)
        shader.addShaderFromSourceFile(QOpenGLShader.Fragment, fname_frag)
        shader.link()
        shader.bind()
        logger.debug("GLSL program log:%s", shader.log())
        return shader

    def _arr2im(self, data):
        if data.ndim ==2:
            return QImage(data.astype(np.uint8),
                    data.shape[0],
                    data.shape[1],
                    QImage.Format_Grayscale8)


    def _fill_texture_2d(self, data, tex=None):
        """ data.shape == (Ny,Nx)
              file texture with GL_RED
            data.shape == (Ny,Nx,3)
              file texture with GL_RGB

            if tex == None, returns a new created texture
        """
        im = self._arr2im(data)

        if tex is None:
            tex = QOpenGLTexture(im)
        else:
            tex.setData(im)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication(["Test"])

    widget = BaseGLWidget()

    widget.show()

    widget._fill_texture_2d(np.zeros((200,100)))
    widget.raise_()
    app.exec_()
