from __future__ import absolute_import, print_function

import os
import numpy as np

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets
import OpenGL.GL as GL
from six.moves import range

N_PREFETCH = 10

checkBoxStyleStr = """
QCheckBox::indicator:checked {
background:black;
border-image: url(%s);
}
QCheckBox::indicator:unchecked {
background:black;
color:white;
border-image: url(%s);}

QToolTip { color:white;}
"""
checkNormalBoxStyleStr = """
QCheckBox::indicator:checked {
}
QCheckBox::indicator:unchecked {
background:black;
color:white;}
QToolTip { color:white;}
"""

checkBoxTristateStyleStr = """
QCheckBox::indicator:unchecked {
background:black;
color:white;
border-image: url(%s);}

QCheckBox::indicator:indeterminate {
background:black;
color:white;
border-image: url(%s);}

QCheckBox::indicator:checked {
background:black;
color:white;
border-image: url(%s);
}
QToolTip { color:white;}
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
    but = QtWidgets.QPushButton("",parent)
    but.setStyleSheet("background-color: black;color:black;color:lightgrey;")
    if fName:
        but.setIcon(QtGui.QIcon(fName))
    but.setIconSize(QtCore.QSize(width,width))
    if method:
        but.clicked.connect(method)
    but.setMaximumWidth(width)
    but.setMaximumHeight(width)
    if tooltip:
        but.setToolTip(tooltip)
    return but


def createImageCheckbox(parent, img1=None, img2 = None, tooltip =""):
    check = QtWidgets.QCheckBox("",parent)
    checkStr = checkBoxStyleStr%(absPath(img1),absPath(img2))
    if os.name =="nt":
        checkStr = checkStr.replace("\\","/")

    check.setStyleSheet(checkStr)
    if tooltip:
        check.setToolTip(tooltip)
    return check

def createStandardCheckbox(parent,  tooltip =""):
    check = QtWidgets.QCheckBox("",parent)
    checkStr = checkNormalBoxStyleStr
    if os.name =="nt":
        checkStr = checkStr.replace("\\","/")

    check.setStyleSheet(checkStr)
    check.setToolTip(tooltip)
    return check

def createTristateCheckbox(parent, img1=None , img2 = None,img3 = None, tooltip = ""):
    check = QtWidgets.QCheckBox("",parent)
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
        tex = GL.glGenTextures(1)

    GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT,1)
    GL.glTexParameterf (GL.GL_TEXTURE_2D,
                     GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameterf (GL.GL_TEXTURE_2D,
                     GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

    GL.glTexParameterf (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
    GL.glTexParameterf (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
    # GL.glTexParameterf (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
    # GL.glTexParameterf (GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)

    if data.ndim == 2:
        Ny,Nx = data.shape
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, Nx, Ny,
                     0, GL.GL_RED, GL.GL_FLOAT, data.astype(np.float32))

    elif data.ndim == 3 and data.shape[2]==3:
        Ny,Nx = data.shape[:2]
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, Nx, Ny,
                         0, GL.GL_RGB, GL.GL_FLOAT, data.astype(np.float32))

    elif data.ndim == 3 and data.shape[2]==4:
        Ny,Nx = data.shape[:2]
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, Nx, Ny,
                         0, GL.GL_RGBA, GL.GL_FLOAT, data.astype(np.float32))

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
        print(e)
        print("could not load image %s"%fName)
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


def create_quad_coords(bounds = [-1,1.,-1,1]):
    x1,x2,y1,y2 = bounds
    return  np.array([[x1,y1],
                   [x2,y1],
                       [x2,y2],
                       [x2,y2],
                       [x1,y2],
                       [x1,y1]])



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



def create_sphere_coords(rx,ry,rz,Nphi=50, Ntheta=30, return_normals = False):
    ts = np.arccos(np.linspace(-1.,1.,Ntheta))
    ps = np.linspace(0,2.*np.pi,Nphi+1)

    T,P = np.meshgrid(ts,ps, indexing = "ij")

    xs = np.array([rx*np.cos(P)*np.sin(T),ry*np.sin(P)*np.sin(T),rz*np.cos(T)])

    coords = []
    normals = []
    for i in range(len(ts)-1):
        for j in range(len(ps)-1):
            coords.append(xs[:,i,j])
            coords.append(xs[:,i+1,j])
            coords.append(xs[:,i+1,j+1])
            coords.append(xs[:,i,j])
            coords.append(xs[:,i+1,j+1])
            coords.append(xs[:,i,j+1])

            #FIXME, wrong for rx != ry ....
            normals.append(1.*xs[:,i,j]/rx)
            normals.append(1.*xs[:,i+1,j]/rx)
            normals.append(1.*xs[:,i+1,j+1]/rx)
            normals.append(1.*xs[:,i,j]/rx)
            normals.append(1.*xs[:,i,j+1]/rx)
            normals.append(1.*xs[:,i+1,j+1]/rx)
    if return_normals:
        return np.array(coords), np.array(normals)
    else:
        return np.array(coords)



if __name__ == '__main__':
    c =  create_sphere_coords(.8,10,10)
    
