import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.pyplot import cm
from spimagine import volshow
import OpenGL.GL as GL


if __name__ == '__main__':

    data = np.einsum("ij,k",np.ones((100,)*2), np.linspace(0,1,100))
    w = volshow(data)
    w.glWidget._set_colormap_array(cm.hot(np.linspace(0,1,2**12))[:,:3])

    print("maximal texture size: ", GL.glGetIntegerv(GL.GL_MAX_TEXTURE_SIZE))