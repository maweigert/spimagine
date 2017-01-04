"""


mweigert@mpi-cbg.de

"""

from __future__ import absolute_import
import numpy as np
from scipy.spatial import Delaunay, ConvexHull
from scipy.spatial.distance import cdist
from itertools import combinations
from six.moves import range
from six.moves import zip



def _normal_from_simplex(ps):
    ndim = ps.shape[-1]
    if ndim == 2:
        dr = ps[1]-ps[0]
        return np.array([dr[1],-dr[0]])
    elif ndim ==3:
        return np.cross(ps[1]-ps[0],ps[2]-ps[0])

    else:
        raise NotImplementedError("wrong dimension")

def _reduce_indices(indices):
    """return indices, such that every indices is used
    """
    ind_sort = sorted(set(indices.flatten()))
    ind_dict = dict((ind,i) for i,ind in enumerate(ind_sort))
    indices_new = np.array([ind_dict[ind] for ind in indices.flatten()]).reshape(indices.shape)
    return ind_sort, indices_new


def alpha_shape2(points, alpha = -1):
    """
    Computes the alpha shape (generalized convex hull) for a set of points
    by removing all faces from tyhe delaunay triangulation that are smaller than alpha
    and then finding its border.

    See https://en.wikipedia.org/wiki/Alpha_shape

    only 2d and 3d versions are implemented now.

    Parameters
    ----------
    points: ndarray of shape(n_points, ndim)
        the points in R^2/3 to build the shape from
    alpha: float
        If set to -1 the result corresponds to the convex hull,
        the smaller alpha, the finer the shape is (but the more faces will be removed)

    Returns
    -------
        indices, normals

    """
    ndim = points.shape[-1]

    if not ndim in [2,3]:
        raise NotImplementedError("only defined for 2 and 3 dimensions")

    # simple convex hull
    if alpha==-1:
        hull = ConvexHull(points)
        normals = np.zeros_like(points)
        count = np.zeros_like(points[:,0, np.newaxis])+1.e-10
        for i, ind in enumerate(hull.simplices):
            n = hull.equations[i, :ndim]
            normals[ind, :] += n/np.linalg.norm(n)
            count[ind] += 1
        normals = normals/count

        faces = hull.simplices

    else:

        # Alpha shape

        tri = Delaunay(points)

        # filter simplices by face length
        def is_alpha_simp(simp):
            return np.all([np.sum((points[simp[c1]]-points[simp[c2]])**2)<4*alpha**2 for (c1, c2) in combinations(list(range(ndim+1)), 2)])

        #enforce clockwise order
        def make_simp_cw(simp):
            if np.linalg.det(np.vstack([points[simp].T,np.ones(len(simp))]))>=0:
                return simp
            else:
                simp[-1],simp[-2] = simp[-2],simp[-1]
                return simp

        simplices = [make_simp_cw(simp) for simp in tri.simplices if is_alpha_simp(simp)]

        # get faces
        if ndim==2:
            c_combi = [[0,1],[1,2],[2,0]]
        elif ndim ==3:
            c_combi = [[0,1,2],[1,3,2],[2,3,0],[3,1,0]]

        all_faces = [tuple([simp[_c] for _c in c]) for simp in simplices for c in c_combi]

        faces_dict = dict()
        already_present = set()
        for e in all_faces:
            e_sort = tuple(sorted(e))
            if e_sort in already_present:
                faces_dict.pop(e_sort)
            else:
                faces_dict[e_sort] = e
                already_present.add(e_sort)

        faces = np.array(list(faces_dict.values()))

        # normals
        normals = np.zeros_like(points)
        count = np.zeros_like(points[:,0, np.newaxis])+1.e-10
        for i, face in enumerate(faces):
            n = _normal_from_simplex(points[face])
            normals[face, :] += n/np.linalg.norm(n)
            count[face] += 1

        normals = normals/count


    # reduce the points/normals/indices to only those that are actually used
    #
    # face_sort, faces = _reduce_indices(faces)
    #
    # points = points[face_sort]
    # normals = normals[face_sort]
    #


    return points,  normals, faces



def alpha_shape(points, alpha = -1):
    """
    Computes the alpha shape (generalized convex hull) for a set of points
    by removing all faces from tyhe delaunay triangulation that are smaller than alpha
    and then finding its border.

    See https://en.wikipedia.org/wiki/Alpha_shape

    only 2d and 3d versions are implemented now.

    This is still an inefficient implementation (lots of python looping) and hence
    might be slow

    Parameters
    ----------
    points: ndarray of shape(n_points, ndim)
        the points in R^2/3 to build the shape from
    alpha: float
        If set to -1 the result corresponds to the convex hull,
        the smaller alpha, the finer the shape is (but the more faces will be removed)

    Returns
    -------
        indices, normals

    """
    #FIXME: still has issues with the normals in 3d + still is too slow...

    # FIXME: still has issues with the normals in 3d + still is too slow...

    ndim = points.shape[-1]

    if not ndim in [2, 3]:
        raise NotImplementedError("only defined for 2 and 3 dimensions")

    # simple convex hull
    if alpha==-1:
        hull = ConvexHull(points)
        normals = np.zeros_like(points)
        count = np.zeros_like(points[:, 0, np.newaxis])+1.e-10
        for i, ind in enumerate(hull.simplices):
            n = hull.equations[i, :ndim]
            normals[ind, :] += n/np.linalg.norm(n)
            count[ind] += 1
        normals = normals/count
        faces = hull.simplices

    else:

        # enforce clockwise order
        def cw_order(simp):
            order = list(range(len(simp)))
            if np.linalg.det(np.vstack([points[simp].T, np.ones(len(simp))]))<0:
                order[-1], order[-2] = order[-2], order[-1]
            return order

        def valid_face(face):
            return np.all([np.sum((points[face[c1]]-points[face[c2]])**2)<4*alpha**2 for (c1, c2) in
                           combinations(list(range(ndim)), 2)])

        tri = Delaunay(points)


        orders = [cw_order(simp) for simp in tri.simplices]


        simplices = [simp[order] for simp, order in zip(tri.simplices, orders)]
        neighbors = [neigh[order] for neigh, order in zip(tri.neighbors, orders)]


        # get the valid faces (i.e. those that are smaller than 2*alpha)
        faces_all = [[list(s)[:j]+list(s)[j+1:] for j in range(ndim+1)] for s in simplices]
        faces_points = points[faces_all]
        faces_valid = np.ones((len(simplices), ndim+1), np.bool)
        for (c1, c2) in combinations(list(range(ndim)), 2):
            faces_valid *= np.linalg.norm(faces_points[:, :, c1, :]-faces_points[:, :, c2, :], axis=-1)<2.*alpha

        # faces_valid = [[valid_face(list(s)[:j]+list(s)[j+1:]) for j in xrange(ndim+1)] for s in simplices]
        #
        # the current border simplices
        border = set([i for i, neigh in enumerate(neighbors) if -1 in neigh])

        removed = set()
        looping = True

        while looping:
            border_old = border.copy()

            valid_mask = faces_valid.copy()
            valid_mask[np.array(neighbors)!=-1] = True
            valid_mask = np.all(valid_mask,axis = -1)

            # check wether they are reducible
            for i in border_old:
                n = neighbors[i]
                s = simplices[i]
                fv = faces_valid[i]

                # if one of the bordering faces is too big, remove the simplex and add the neighbors
                # if not np.all([valid_face(s[:j]+s[j+1:]) for j in xrange(len(n)) if n[j] ==-1]):
                if not valid_mask[i]:
                #if not np.all([fv[j] for j in xrange(ndim+1) if n[j]==-1]):
                    border.remove(i)
                    removed.add(i)
                    for _n in n:
                        if _n>-1 and not _n in removed:
                            border.add(_n)
                    # we have to update the neighbors of the newly formed boundary
                    for _n, _s in zip(n, s):
                        if _n!=-1:
                            for k, _ns in enumerate(simplices[_n]):
                                if not _ns in s:
                                    neighbors[_n][k] = -1
            looping = border!=border_old




        # get the faces

        if ndim==2:
            c_combi = {2: [0, 1], 0: [1, 2], 1: [2, 0]}
        elif ndim==3:
            c_combi = {3: [0, 1, 2], 0: [1, 3, 2], 1: [2, 3, 0], 2: [3, 1, 0]}

        faces = []
        for b in border:
            n = neighbors[b]
            s = simplices[b]
            for j in range(len(n)):
                if n[j]==-1:
                    faces.append(s[c_combi[j]])

        faces = np.array(faces)

        normals = np.zeros_like(points)
        count = np.zeros_like(points[:, 0, np.newaxis])+1.e-10
        for i, face in enumerate(faces):
            n = _normal_from_simplex(points[face])
            normals[face, :] += n/np.linalg.norm(n)
            count[face] += 1

        normals = normals/count

    return points, normals, faces

if __name__ == '__main__':
    pass