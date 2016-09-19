"""


mweigert@mpi-cbg.de

"""

import logging
logger = logging.getLogger(__name__)

import sys, os
import numpy as np
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL
import OpenGL.GL as gl
import OpenGL.arrays.vbo as glvbo


class TestWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent=None, **kwargs):
        super(TestWidget, self).__init__(parent, **kwargs)

        self.data = np.array([[-1,-1],[1,-1],[1,1],[-1,-1],[1,1],[-1,1]],dtype=np.float32)

        self.normals = np.array([[1,0,0],[0,1,0],[0,0,1],[1,0,0],[0,1,0],[0,0,1]],dtype=np.float32)

        self.vbo = glvbo.VBO(self.data)
        self.vbo_cols = glvbo.VBO(self.normals)



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


        self.program.enableAttributeArray("normal")
        self.vbo_cols.bind()
        gl.glVertexAttribPointer(self.program.attributeLocation("normal"), 3, gl.GL_FLOAT, gl.GL_FALSE, 0, self.vbo_cols)


        gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(self.data))



        print self.context().format().majorVersion()
        print self.context().format().minorVersion()


        print gl.glGetString(gl.GL_VERSION);





if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)

    win = TestWidget(size=QtCore.QSize(800, 800))

    win.show()

    win.raise_()

    sys.exit(app.exec_())
