"""


mweigert@mpi-cbg.de

"""
import numpy as np
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtOpenGL
from PyQt5.QtGui import QOpenGLShaderProgram, QOpenGLShader
import OpenGL.GL as GL

from spimagine.gui.gui_utils import fillTexture2d


class MyWidget(QtOpenGL.QGLWidget):
    def __init__(self, parent = None):
        super(MyWidget, self).__init__(parent)

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

    def initializeGL(self):
        GL.glClearColor(1.0, 0.0, 0.0, 1.0)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        print("OpenGL.GL: " + str(GL.glGetString(GL.GL_VERSION)))
        print("GL.GLSL: " + str(GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)))
        print("OpenGL ATTRIBUTES:\n",", ".join(d for d in dir(GL) if d.startswith("GL_")))

        self.program = QOpenGLShaderProgram()
        self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, """#version 120
        attribute vec2 position;
        attribute vec2 texcoord;
        varying vec2 mytexcoord;
        void main() {
            gl_Position = vec4(position, 0., 1.0);
            mytexcoord = texcoord;
        }""")

        self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, """#version 120
        uniform sampler2D texture;
        varying vec2 mytexcoord;
        void main() {
            
            gl_FragColor = texture2D(texture,mytexcoord);
        }""")
        print(self.program.log())
        self.program.link()

        self.texture = fillTexture2d(np.outer(np.linspace(0, 1, 128), np.ones(128)))

    def paintGL(self):
        #GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.program.bind()

        self.program.enableAttributeArray("position")
        self.program.enableAttributeArray("texcoord")
        self.program.setAttributeArray("position", self.quadCoord)
        self.program.setAttributeArray("texcoord", self.quadCoordTex)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        self.program.setUniformValue("texture", 0)

        GL.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.quadCoord))


if __name__ == '__main__':
    app = QtWidgets.QApplication(["PyQt OpenGL.GL"])


    widget = MyWidget()

    widget.show()
    QtCore.QTimer.singleShot(400, widget.close)
    app.exec_()
