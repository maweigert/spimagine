import os
import numpy as np

from PyQt4 import QtCore
from PyQt4 import QtGui
from OpenGL.GL import *

N_PREFETCH = 10

checkBoxStyleStr = """
QCheckBox::indicator:checked {
background:black;
border-image: url(%s);
}
QCheckBox::indicator:unchecked {
background:black;
border-image: url(%s);}
"""

checkBoxTristateStyleStr = """
QCheckBox::indicator:unchecked {
background:black;
border-image: url(%s);}

QCheckBox::indicator:indeterminate {
background:black;
border-image: url(%s);}

QCheckBox::indicator:checked {
background:black;
border-image: url(%s);
}

"""


def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


def createStandardButton(parent,fName = None,method = None, width = 24, tooltip = ""):
    but = QtGui.QPushButton("",parent)
    but.setStyleSheet("background-color: black")
    if fName:
        but.setIcon(QtGui.QIcon(fName))
    but.setIconSize(QtCore.QSize(width,width))
    but.clicked.connect(method)
    but.setMaximumWidth(width)
    but.setMaximumHeight(width)
    but.setToolTip(tooltip)
    return but


def createStandardCheckbox(parent, img1=None , img2 = None, tooltip = ""):
    check = QtGui.QCheckBox("",parent)
    checkStr = checkBoxStyleStr%(absPath(img1),absPath(img2))
    if os.name =="nt":
        checkStr = checkStr.replace("\\","/")

    check.setStyleSheet(checkStr)
    check.setToolTip(tooltip)
    return check


def createTristateCheckbox(parent, img1=None , img2 = None,img3 = None, tooltip = ""):
    check = QtGui.QCheckBox("",parent)
    check.setTristate()

    checkStr = checkBoxTristateStyleStr%(absPath(img1),absPath(img2),absPath(img3))
    if os.name =="nt":
        checkStr = checkStr.replace("\\","/")

    check.setStyleSheet(checkStr)
    check.setToolTip(tooltip)
    return check





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

    glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf (GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    if data.ndim == 2:
        Ny,Nx = data.shape
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                     0, GL_RED, GL_FLOAT, data.astype(np.float32))

    elif data.ndim == 3 and data.shape[2]==3:
        Ny,Nx = data.shape[:2]
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, Nx, Ny,
                         0, GL_RGB, GL_FLOAT, data.astype(np.float32))

    else:
        raise Exception("data format not supported! \ndata.shape should be either (Ny,Nx) or (Ny,Nx,3)")
    return tex

def arrayFromImage(fName):
    """converts png image to float32 array
    returns an array of shape [w,h,3]
    """
    try:
        img = QtGui.QImage(fName).convertToFormat(QtGui.QImage.Format_RGB32)


        Nx, Ny = img.width(),img.height()
        tmp = img.bits().asstring(img.numBytes())
        arr = np.frombuffer(tmp, np.uint8).reshape((Ny,Nx,4))
        arr = arr.astype(np.float32)/np.amax(arr)
        return arr[:,:,:-1][:,:,::-1]
    except Exception as e:
        print e
        print "could not load image %s"%fName
        return np.zeros((10,100,3),np.float32)





def slice_coords(relPos,dim):

    if dim ==0:
        coords = np.array([[0,-1,-1],[0,1,-1],[0,1,1],
                    [0,1,1],[0,-1,1],[0,-1,-1]],dtype=np.float32)

    elif dim ==1:
        coords = np.array([[-1,0,-1],[1,0,-1],[1,0,1],
                    [1,0,1],[-1,0,1],[-1,0,-1]],dtype=np.float32)

    elif dim ==2:
        coords = np.array([[-1,-1,0],[1,-1,0],[1,1,0],
                    [1,1,0],[-1,1,0],[-1,-1,0]],dtype=np.float32)


    coords[:,dim] = -1.+2*relPos

    return coords


def create_cube_coords(bounds = [-1,1.,-1,1,-1,1]):
    x1,x2,y1,y2,z1,z2 = bounds
    return np.array([[x2, y2, z2], [x1, y2, z2],
                     [x1, y2, z2], [x1, y1, z2],
                     [x1, y1, z2], [x2, y1, z2],
                     [x2, y1, z2], [x2, y2, z2],

                     [x2, y2, z1], [x1, y2, z1],
                     [x1, y2, z1], [x1, y1, z1],
                     [x1, y1, z1], [x2, y1, z1],
                     [x2, y1, z1], [x2, y2, z1],

                     [x2, y2, z2], [x2, y2, z1],
                     [x1, y2, z2], [x1, y2, z1],
                     [x1, y1, z2], [x1, y1, z1],
                     [x2, y1, z2], [x2, y1, z1],
                     ])

    # return np.array([[1.0,   1.0,  1.0], [-1.0,  1.0,  1.0],
    #                  [-1.0,  1.0,  1.0], [-1.0, -1.0,  1.0],
    #                  [-1.0, -1.0,  1.0], [ 1.0, -1.0,  1.0],
    #                  [1.0,  -1.0,  1.0], [ 1.0,  1.0,  1.0],

    #                  [1.0,   1.0,  -1.0], [-1.0,  1.0,  -1.0],
    #                  [-1.0,  1.0,  -1.0], [-1.0, -1.0,  -1.0],
    #                  [-1.0, -1.0,  -1.0], [ 1.0, -1.0,  -1.0],
    #                  [1.0,  -1.0,  -1.0], [ 1.0,  1.0,  -1.0],

    #                  [1.0,   1.0,  1.0], [1.0,  1.0,  -1.0],
    #                  [-1.0,  1.0,  1.0], [-1.0, 1.0,  -1.0],
    #                  [-1.0, -1.0,  1.0], [-1.0,-1.0,  -1.0],
    #                  [1.0,  -1.0,  1.0], [1.0, -1.0,  -1.0],
    #                  ])
