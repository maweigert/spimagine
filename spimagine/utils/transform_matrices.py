#!/usr/bin/env python

"""

compatible with OpenGL, i.e.

mat4_perspective = gluPerspective
...etc


author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

from __future__ import absolute_import, print_function

import numpy as np
from spimagine.utils.quaternion import Quaternion


def mat4_scale(x=1., y=1., z=1.):
    return np.array([x, 0.0, 0.0, 0.,
                     0.0, y, 0.0, 0.0,
                     0.0, 0.0, z, 0.0,
                     0, 0, 0, 1.0],np.float32).reshape(4, 4)


def mat4_rotation(w=0, x=1, y=0, z=0):
    n = np.array([x, y, z], np.float32)
    n *= 1./np.sqrt(1.*np.sum(n**2))
    q = Quaternion(np.cos(.5*w), *(np.sin(.5*w)*n))
    return q.toRotation4()


def mat4_rotation_euler(yaw = 0, pitch = 0, roll = 0):
    """ in z-y'-x' convention


    """
    Z = mat4_rotation(yaw, 0, 0, 1)
    Y = mat4_rotation(pitch, 0, 1, 0)
    X = mat4_rotation(roll, 1, 0, 0)

    return np.dot(Z, np.dot(Y, X))


def mat4_perspective(fovy=45, aspect=1.,
                     z1=0.1, z2=10):
    """ like gluPerspective(fovy, aspect, zNear, zFar)
        fovy in degrees
    """
    f = 1./np.tan(fovy/180.*np.pi/2.)
    return np.array([[1.*f/aspect, 0, 0, 0],
                     [0, f, 0, 0],
                     [0, 0, -1.*(z2+z1)/(z2-z1), -2.*z1*z2/(z2-z1)],
                     [0, 0, -1, 0]], np.float32)


def mat4_stereo_perspective(fovy=45, aspect=1.,
                            z1=0.1, z2=10, eye_shift=0):
    h = z1*np.tan(fovy/180.*np.pi/2.)
    w = h*aspect;

    return mat4_frustrum(-w-eye_shift, w-eye_shift, -h, h, z1, z2)


def mat4_frustrum(left, right, bottom, top, zNear, zFar):
    return np.array([[2.*zNear/(right-left), 0, 1.*(right+left)/(right-left), 0],
                     [0, 2.*zNear/(top-bottom), (top+bottom)/(top-bottom), 0],
                     [0, 0, -1.*(zFar+zNear)/(zFar-zNear), -2.*zFar*zNear/(zFar-zNear)],
                     [0, 0, -1., 0]],np.float32)


def mat4_ortho(x1=-1, x2=1,
               y1=-1, y2=1,
               z1=-1, z2=1):
    """ like glOrtho """
    ax, bx = x2+x1, x2-x1
    ay, by = y2+y1, y2-y1
    az, bz = z2+z1, z2-z1
    return np.array([[2./bx, 0, 0, -1.*ax/bx],
                     [0, 2./by, 0, -1.*ay/by],
                     [0, 0, -2./bz, -1.*az/bz],
                     [0, 0, 0, 1.]],np.float32)


def mat4_identity():
    return np.identity(4)


def mat4_translate(x=0, y=0, z=0):
    M = mat4_identity()
    M[:3, 3] = x, y, z
    return M


def mat4_lookat(eye, center, up):
    _eye = np.array(eye, np.float32)
    _center = np.array(center, np.float32)
    _up = np.array(up,np.float32)

    _fwd = _center-_eye

    # normalize
    _fwd *= 1./np.sqrt(np.sum(_fwd**2))

    s = np.cross(_fwd, _up)

    s *= 1./np.sqrt(np.sum(s**2))

    _up = np.cross(s, _fwd)

    M = np.identity(4)
    M[0, :3] = s
    M[1, :3] = _up
    M[2, :3] = - _fwd

    return np.dot(M, mat4_translate(*(-_eye)))


# gluLookAt(GLdouble eyex, GLdouble eyey, GLdouble eyez, GLdouble centerx,
#       GLdouble centery, GLdouble centerz, GLdouble upx, GLdouble upy,
#       GLdouble upz)
# {
#     float forward[3], side[3], up[3];
#     GLfloat m[4][4];

#     forward[0] = centerx - eyex;
#     forward[1] = centery - eyey;
#     forward[2] = centerz - eyez;

#     up[0] = upx;
#     up[1] = upy;
#     up[2] = upz;

#     normalize(forward);

#     /* Side = forward x up */
#     cross(forward, up, side);
#     normalize(side);

#     /* Recompute up as: up = side x forward */
#     cross(side, forward, up);

#     __gluMakeIdentityf(&m[0][0]);
#     m[0][0] = side[0];
#     m[1][0] = side[1];
#     m[2][0] = side[2];

#     m[0][1] = up[0];
#     m[1][1] = up[1];
#     m[2][1] = up[2];

#     m[0][2] = -forward[0];
#     m[1][2] = -forward[1];
#     m[2][2] = -forward[2];

#     glMultMatrixf(&m[0][0]);
#     glTranslated(-eyex, -eyey, -eyez);
# }


if __name__=='__main__':
    print(mat4_lookat([0, 0, 10], [0, 0, 0], [0, 1, 0]))


    # print rotMat(.1,0,0,1)
    # orthoM = projMatOrtho(-2,2,-2,2,-10,10)

    # perspM = projMatPerspective(45,1,.1,10)

    # x  = np.dot(orthoM,[0,0,0,1])
    # print x


    # x  = np.dot(perspM,[0,0,.1,1])
    # print x

    # print orthoM
