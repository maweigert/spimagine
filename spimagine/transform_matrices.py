#!/usr/bin/env python

"""

compatible with OpenGL, i.e.

projMatPerspective = gluPerspective
...etc


author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

import numpy as np
from quaternion import Quaternion

def rotMatX(phi):
    return np.array([np.cos(phi),0,np.sin(phi),0,
                  0,1, 0,0,
                  -np.sin(phi),0, np.cos(phi),0,
                  0,0,0,1]).reshape(4,4)

def rotMat(w=0,x=1,y=0,z=0):
    """ the rotation matrix for a rotation by angle w around axis [x,y,z]"""
    u_cross = np.array([[0,-z,y],
                        [z,0,-x],
                        [-y,x,0]])

    u_tens = np.outer([x,y,z],[x,y,z])

    return np.cos(w)*np.identity(3)+np.sin(w)*u_cross + (1-np.cos(w))*u_tens

def rotMat4(w=0,x=1,y=0,z=0):
    n = 1.*np.array([x,y,z])
    n *= 1./np.sqrt(np.sum(n**2))
    q = Quaternion(np.cos(.5*w),*(np.sin(.5*w)*n))
    return q.toRotation4()


def transMatReal(x=0,y=0,z=0):
    return np.array([1.0, 0.0, 0.0, x,
                          0.0, 1.0, 0.0, y,
                          0.0, 0.0, 1.0, z,
                          0, 0, 0, 1.0]).reshape(4,4)

def transMat(x=0,y=0,z=0):
    return np.array([1.0, 0.0, 0.0, 0.,
                          0.0, 1.0, 0.0, 0.0,
                          0.0, 0.0, 1.0, 0.0,
                          x, y, z, 1.0]).reshape(4,4)


def scaleMat(x =1.,y=1.,z=1.):
    return np.array([x, 0.0, 0.0, 0.,
                  0.0, y, 0.0, 0.0,
                  0.0, 0.0, z, 0.0,
                  0, 0, 0, 1.0]).reshape(4,4)



def projMatPerspective(fovy = 45,aspect = 1.,
                       z1 = 0.1, z2 = 10):
    """ like gluPerspective(fovy, aspect, zNear, zFar)
        fovy in degrees
    """
    f = 1./np.tan(fovy/180.*np.pi/2.)
    return np.array([[1.*f/aspect,0,0,0],
                  [0,f,0,0],
                  [0,0,-1.*(z2+z1)/(z2-z1),-2.*z1*z2/(z2-z1)],
                  [0,0,-1,0]])


def projMatOrtho(x1 = -1, x2 = 1,
                 y1 = -1, y2 = 1,
                 z1 = -1, z2 = 1):
    """ like glOrtho """
    ax,bx = x2+x1,x2-x1
    ay,by = y2+y1,y2-y1
    az,bz = z2+z1,z2-z1
    return np.array([[2./bx,0,0,-1.*ax/bx],
                     [0,2./by,0,-1.*ay/by],
                     [0,0,-2./bz,-1.*az/bz],
                     [0,0,0,1.]])





if __name__ == '__main__':

    print rotMat(.1,0,0,1)
    # orthoM = projMatOrtho(-2,2,-2,2,-10,10)

    # perspM = projMatPerspective(45,1,.1,10)

    # x  = np.dot(orthoM,[0,0,0,1])
    # print x


    # x  = np.dot(perspM,[0,0,.1,1])
    # print x

    # print orthoM
