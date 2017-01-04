"""
defines mesh object that are to be rendered with OpenGL

mweigert@mpi-cbg.de

"""

from __future__ import absolute_import, print_function

import numpy as np
from spimagine.utils.transform_matrices import *
from spimagine.utils import alpha_shape
from six.moves import range

class Mesh(object):
    """
    A mesh object is defined by its vertices, normals, indices  and edge/facecolors
    """

    def __init__(self,
                 vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0]],
                 indices = [0,1,2],
                 normals= [[0, 0, 1], [0, 0, 1], [0,0,1]],
                 facecolor=(1., 1., 1.),
                 edgecolor=None,
                 alpha=.6,
                 light=(-1,-1,1)):
        """
        vertices are a list of 3d coordinates like [[0,0,0], [1,0,0],...]
        where 3 consecutive coordinates define a triangle to be rendered.

        normals, facecolor , edgecolor,  alpha are optional

        face/edgecolor are (r,g,b) colors or None if they should not be drawn at all

        if normals and light are given (and facecolor is not None), a simple
        Phong shading is applied
        """

        assert len(indices)%3==0

        self.vertices = vertices
        self.normals = normals
        self.indices = indices



        self.alpha = np.clip(alpha, 0, 1.)

        # self.edges = []
        # # FIXME: this includes every edge twice which is not efficient
        # for i in range(len(vertices)/3):
        #     v1, v2, v3 = vertices[3*i], vertices[3*i+1], vertices[3*i+2]
        #     self.edges.append(v1)
        #     self.edges.append(v2)
        #     self.edges.append(v1)
        #     self.edges.append(v3)
        #     self.edges.append(v2)
        #     self.edges.append(v3)


        self.facecolor = facecolor
        self.edgecolor = edgecolor

        self.light = light


    @classmethod
    def mesh_from_points(points, alpha = -1):
        """
        creates the mesh from the convex or concave (alpha shape) hull of points

        See definition of spimagine.utils.alpha_shape

        Parameters
        ----------
        alpha: float,
            the alpha shape parameter. Set to -1 get the convex hull.
             The smaller, the more concave details will be visible, but the more
             points might get lost.

        Returns
        -------
        points, normals, indices
        which can be directly used in Mesh()
        """
        points, normals, indices = alpha_shape(points, alpha)

        return points.flatten(), normals.flatten(), indices.flatten()

class EllipsoidMesh(Mesh):
    memoize_dict = {}

    def __init__(self, rs=(1., .5, .5),
                 pos=(0, 0, 0),
                 n_phi=30,
                 n_theta=20,
                 facecolor=(1., 1., 1.),
                 edgecolor=None,
                 alpha=1.,
                 light=(-1,-1,1),
                 transform_mat = mat4_identity()):
        """creates an ellipsoidal mesh at pos with half axes rs = (rx,ry,rz)
        of equally distributing points n_phi x n_theta"""

        vertices, normals, indices = EllipsoidMesh.create_verts(rs, pos, n_phi, n_theta, transform_mat)

        super(EllipsoidMesh, self).__init__(vertices=vertices,
                                            normals=normals,
                                            indices = indices,
                                            facecolor=facecolor,
                                            edgecolor=edgecolor,
                                            alpha=alpha,
                                            light=light)

    @staticmethod
    def create_verts0(rs, pos, n_phi, n_theta, transform_mat = mat4_identity()):
        ts = np.linspace(0, np.pi, n_theta)
        ps = np.linspace(0, 2.*np.pi, n_phi+1)



        T, P = np.meshgrid(ts, ps, indexing="ij")
        rx, ry, rz = rs
        xs = np.array([rx*np.cos(P)*np.sin(T), ry*np.sin(P)*np.sin(T), rz*np.cos(T)])

        # normalized normals
        ns = np.stack([xs[0]/rx**2, xs[1]/ry**2, xs[2]/rz**2])
        ns *= 1./(np.linalg.norm(ns, axis=0)+1.e-10)

        verts = []
        normals = []
        # FIXME: this is still very slow
        for i in range(len(ts)-1):
            for j in range(len(ps)-1):
                verts.append(xs[:, i, j])
                verts.append(xs[:, i+1, j])
                verts.append(xs[:, i+1, j+1])
                verts.append(xs[:, i, j])
                verts.append(xs[:, i+1, j+1])
                verts.append(xs[:, i, j+1])

                # # #FIXME, wrong for rx != ry ....
                normals.append(1.*ns[:, i, j])
                normals.append(1.*ns[:, i+1, j])
                normals.append(1.*ns[:, i+1, j+1])
                normals.append(1.*ns[:, i, j])
                normals.append(1.*ns[:, i+1, j+1])
                normals.append(1.*ns[:, i, j+1])

        return np.array(pos)+np.array(verts), np.array(normals)


    @classmethod
    def create_verts2(cls, rs, pos, n_phi, n_theta, transform_mat = None):
        ts = np.linspace(0, np.pi, n_theta)
        ps = np.linspace(0, 2.*np.pi, n_phi)

        T, P = np.meshgrid(ts, ps, indexing="ij")
        rx, ry, rz = rs
        xs = np.array([rx*np.cos(P)*np.sin(T), ry*np.sin(P)*np.sin(T), rz*np.cos(T)]).reshape((3,n_phi*n_theta))

        # normalized normals
        ns = np.stack([xs[0]/rx**2, xs[1]/ry**2, xs[2]/rz**2])
        ns *= 1./(np.linalg.norm(ns, axis=0)+1.e-10)


        inds = np.empty((n_theta-1)*(n_phi-1)*6)

        ind_base = []
        for i in range(len(ts)-1):
            ind_base += [n_phi*i, n_phi*(i+1),n_phi*(i+1)+1,n_phi*i, n_phi*(i+1)+1,n_phi*i+1]

        ind_base = np.array(ind_base)

        xs, ns = xs.reshape((3,n_phi*n_theta)), ns.reshape((3,n_phi*n_theta))
        for j in range(len(ps)-1):
            inds[6*(n_theta-1)*j:6*(n_theta-1)*(j+1)] = j+ind_base

        if not transform_mat is None:
            xs = np.dot(transform_mat[:3,:3],xs)
            ns = np.dot(transform_mat[:3,:3],ns)

        xs, ns = xs.T, ns.T

        xs += np.array(pos)

        return xs, ns, inds

    @classmethod
    def create_verts(cls, rs, pos, n_phi, n_theta, transform_mat = None):
        in_memoize_dict = (n_theta, n_phi) in cls.memoize_dict


        if in_memoize_dict:
            xs0, inds =  cls.memoize_dict[(n_theta, n_phi)]
        else:
            ts = np.linspace(0, np.pi, n_theta)
            ps = np.linspace(0, 2.*np.pi, n_phi)
            T, P = np.meshgrid(ts, ps, indexing="ij")
            xs0 = np.array([np.cos(P)*np.sin(T), np.sin(P)*np.sin(T), np.cos(T)]).reshape((3,n_phi*n_theta))

        xs = np.empty_like(xs0)
        rx, ry, rz = rs
        xs[0] = rx*xs0[0]
        xs[1] = ry*xs0[1]
        xs[2] = rz*xs0[2]

        # normalized normals
        ns = np.stack([xs[0]/rx**2, xs[1]/ry**2, xs[2]/rz**2])
        ns *= 1./(np.linalg.norm(ns, axis=0)+1.e-10)

        # generate triangle indices
        if not in_memoize_dict:
            inds = np.empty((n_theta-1)*(n_phi-1)*6)

            ind_base = []
            for i in range(len(ts)-1):
                ind_base += [n_phi*i, n_phi*(i+1),n_phi*(i+1)+1,n_phi*i, n_phi*(i+1)+1,n_phi*i+1]

            ind_base = np.array(ind_base)


            for j in range(len(ps)-1):
                inds[6*(n_theta-1)*j:6*(n_theta-1)*(j+1)] = j+ind_base

            cls.memoize_dict[(n_theta, n_phi)] = (xs0, inds)

        if not transform_mat is None:
            xs = np.dot(transform_mat[:3,:3],xs)
            ns = np.dot(transform_mat[:3,:3],ns)

        xs, ns = xs.T, ns.T

        xs += np.array(pos)

        return xs, ns, inds

class SphericalMesh(EllipsoidMesh):
    def __init__(self, r=1.,
                 pos=(0, 0, 0),
                 n_phi=30,
                 n_theta=20,
                 facecolor=(1., 1., 1.),
                 edgecolor=None,
                 alpha=1.,
                 light = (-1,-1,1)):
        """creates a spherical mesh at pos with radius r
        of equally distributing points n_phi x n_theta"""

        super(SphericalMesh, self).__init__(rs=(r,)*3,
                                            pos=pos,
                                            n_phi=n_phi, n_theta=n_theta,
                                            facecolor=facecolor,
                                            edgecolor=edgecolor,
                                            alpha=alpha,
                                            light=light)


if __name__=='__main__':
    from time import time

    t = time()
    for _ in range(5):
        EllipsoidMesh.create_verts0((1, 1, 1), (0, 0, 0), 30, 20)
    print(time()-t)

    t = time()
    for _ in range(50):
        v1, n1, i1 = EllipsoidMesh.create_verts((1, 1, 1), (0, 0, 0), 30, 20)
    print(time()-t)


    t = time()
    for _ in range(50):
        v2, n2, i2 = EllipsoidMesh.create_verts2((1, 1, 1), (0, 0, 0), 30, 20)
    print(time()-t)


    print(np.allclose(v1,v2),np.allclose(n1,n2),np.allclose(i1,i2), end=' ')


    m1 = EllipsoidMesh((1, 2, 1), (0, 0, 0), 30, 20)
