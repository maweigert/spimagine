"""
defines mesh object that are to be rendered with OpenGL

mweigert@mpi-cbg.de

"""

import numpy as np


class Mesh(object):
    """
    A mesh object is defined by its vertices, normals and edge/facecolors
    """
    def __init__(self,
                 vertices = [[0,0,0],[1,0,0],[0,1,0]],
                 normals = None,
                 facecolor = (1.,1.,1.),
                 edgecolor = None,
                 alpha = 1.,
                 light = [1,1,-1]):
        """
        vertices are a list of 3d coordinates like [[0,0,0], [1,0,0],...]
        where 3 consecutive coordinates define a triangle to be rendered.

        normals, facecolor , edgecolor,  alpha are optional

        face/edgecolor are (r,g,b) colors or None if they should not be drawn at all

        if normals and light are given (and facecolor is not None), a simple
        Phong shading is applied
        """

        assert len(vertices)%3==0

        self.vertices = vertices
        self.edges = []
        self.alpha = np.clip(alpha,0,1.)

        #FIXME: this includes every edge twice which is stupid
        for i in range(len(vertices)/3):
            v1,v2, v3 = vertices[3*i], vertices[3*i+1], vertices[3*i+2]
            self.edges.append(v1)
            self.edges.append(v2)
            self.edges.append(v1)
            self.edges.append(v3)
            self.edges.append(v2)
            self.edges.append(v3)


        self.normals = normals

        self.facecolor = facecolor
        self.edgecolor = edgecolor


        self.light = light


class EllipsoidMesh(Mesh):
    def __init__(self, rs = (1.,.5,.5),
                 pos = (0,0,0),
                 n_phi = 30,
                 n_theta = 20,
                 facecolor = (1.,1.,1.),
                 edgecolor = None,
                 alpha = 1.,
                 light = [1,1,-1]):
        """creates an ellipsoidal mesh at pos with half axes rs = (rx,ry,rz)
        of equally distributing points n_phi x n_theta"""

        vertices, normals = EllipsoidMesh.create_verts(rs, pos, n_phi, n_theta)

        super(EllipsoidMesh,self).__init__(vertices = vertices,
                                           normals = normals,
                                           facecolor = facecolor,
                                           edgecolor = edgecolor,
                                           alpha = alpha,
                                           light = light)
    @staticmethod
    def create_verts(rs, pos, n_phi, n_theta):
        ts = np.linspace(0,np.pi,n_theta)
        ps = np.linspace(0,2.*np.pi,n_phi+1)

        T,P = np.meshgrid(ts,ps, indexing = "ij")
        rx,ry,rz = rs
        xs = np.array([rx*np.cos(P)*np.sin(T),ry*np.sin(P)*np.sin(T),rz*np.cos(T)])

        verts = []
        normals = []
        for i in range(len(ts)-1):
            for j in range(len(ps)-1):
                verts.append(xs[:,i,j])
                verts.append(xs[:,i+1,j])
                verts.append(xs[:,i+1,j+1])
                verts.append(xs[:,i,j])
                verts.append(xs[:,i+1,j+1])
                verts.append(xs[:,i,j+1])

                #FIXME, wrong for rx != ry ....
                normals.append(1.*xs[:,i,j]/rx)
                normals.append(1.*xs[:,i+1,j]/rx)
                normals.append(1.*xs[:,i+1,j+1]/rx)
                normals.append(1.*xs[:,i,j]/rx)
                normals.append(1.*xs[:,i,j+1]/rx)
                normals.append(1.*xs[:,i+1,j+1]/rx)

        return  np.array(pos)+np.array(verts), np.array(normals)


class SphericalMesh(EllipsoidMesh):
    def __init__(self,r = 1.,
                 pos = (0,0,0),
                 n_phi = 30,
                 n_theta = 20,
                 facecolor = (1.,1.,1.),
                 edgecolor = None,
                 alpha = 1.,
                 light = [1,1,-1]):
        """creates a spherical mesh at pos with radius r
        of equally distributing points n_phi x n_theta"""


        super(SphericalMesh,self).__init__(rs = (r,)*3,
                                           pos = pos,
                                           n_phi = n_phi, n_theta = n_theta,
                                           facecolor = facecolor,
                                           edgecolor = edgecolor,
                                           alpha = alpha,
                                           light = light)


if __name__ == '__main__':
    print Mesh().vertices
    print EllipsoidMesh().vertices
    print SphericalMesh().facecolor
