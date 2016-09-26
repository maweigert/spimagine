"""


mweigert@mpi-cbg.de

"""

import numpy as np
from scipy.spatial import Delaunay, ConvexHull
from scipy.spatial.distance import cdist
from itertools import combinations



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


def alpha_shape(points, alpha = -1):
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
            return np.all([np.sum((points[simp[c1]]-points[simp[c2]])**2)<4*alpha**2 for (c1, c2) in combinations(range(ndim+1), 2)])

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

        faces = np.array(faces_dict.values())

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


if __name__ == '__main__':
    pass