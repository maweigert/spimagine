"""


mweigert@mpi-cbg.de

"""

import logging
logger = logging.getLogger(__name__)

import sys, os
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtOpenGL
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo


class TestWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, **kwargs):
        super(TestWidget, self).__init__(parent, **kwargs)

        self.data = np.array([[-1,-1],[1,-1],[1,1],[-1,1]],dtype=np.float32)
        self.cols= np.array([[1,0,0],[0,1,0],[0,0,1],[1,1,1]],dtype=np.float32)

        self.index = np.array([0,1,2,0,3,2],dtype=np.uint32)

        print self.cols
        self.vbo = glvbo.VBO(self.data)
        self.vbo_cols = glvbo.VBO(self.cols)
        self.vbo_index = glvbo.VBO(self.index, target=gl.GL_ELEMENT_ARRAY_BUFFER)



    def _shader_from_file(self, fname_vert, fname_frag):
        shader = QtOpenGL.QGLShaderProgram()
        shader.addShaderFromSourceFile(QtOpenGL.QGLShader.Vertex, fname_vert)
        shader.addShaderFromSourceFile(QtOpenGL.QGLShader.Fragment, fname_frag)
        shader.link()
        shader.bind()
        logger.debug("GLSL program log:%s", shader.log())
        return shader

    def initializeGL(self):

        self.program = self._shader_from_file("shaders/basic.vert",
                                                 "shaders/basic.frag")


    def paintGL(self):
        self.makeCurrent()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        self.program.bind()

        self.program.enableAttributeArray("position")
        self.vbo.bind()
        gl.glVertexAttribPointer(self.program.attributeLocation("position"), 2, gl.GL_FLOAT, gl.GL_FALSE, 0, self.vbo)


        self.program.enableAttributeArray("color")
        self.vbo_cols.bind()
        gl.glVertexAttribPointer(self.program.attributeLocation("color"), 3, gl.GL_FLOAT, gl.GL_FALSE, 0, self.vbo_cols)

        self.vbo_index.bind()

        #gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(self.data))

        gl.glDrawElements(gl.GL_TRIANGLES, len(self.index), gl.GL_UNSIGNED_INT, None)

        print self.context().format().majorVersion()
        print self.context().format().minorVersion()


        print gl.glGetString(gl.GL_VERSION);





if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)

    win = TestWidget(size=QtCore.QSize(800, 800))

    win.show()

    win.raise_()

    sys.exit(app.exec_())
