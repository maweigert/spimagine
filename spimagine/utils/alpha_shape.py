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

def alpha_shape(points, alpha = -1):
    """
    Computes the alpha shape (generalized convex hull) for a set of points
    by removing all edges from tyhe delaunay triangulation that are smaller than alpha
    and then finding its border.

    See https://en.wikipedia.org/wiki/Alpha_shape

    only 2d and 3d versions are implemented now.

    Parameters
    ----------
    points: ndarray of shape(n_points, ndim)
        the points in R^2/3 to build the shape from
    alpha: float
        If set to -1 the result corresponds to the convex hull,
        the smaller alpha, the finer the shape is (but the more edges will be removed)

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

        return hull.simplices, normals

    # Alpha shape

    tri = Delaunay(points)

    # filter simplices by edge length
    def is_alpha_simp(simp, alpha):
        return np.all([np.sum((points[simp[c1]]-points[simp[c2]])**2)<4*alpha**2 for (c1, c2) in combinations(range(ndim+1), 2)])

    #enforce clockwise order
    def make_simp_cw(simp):
        if np.linalg.det(np.vstack([points[simp].T,np.ones(len(simp))]))>=0:
            return simp
        else:
            simp[-1],simp[-2] = simp[-2],simp[-1]
            return simp

    simplices = [make_simp_cw(simp) for simp in tri.simplices if is_alpha_simp(simp, alpha)]


    # get faces
    if ndim==2:
        c_combi = [[0,1],[1,2],[2,0]]
    elif ndim ==3:
        c_combi = [[0,1,2],[1,3,2],[2,3,0],[3,1,0]]

    all_edges = [tuple([simp[_c] for _c in c]) for simp in simplices for c in c_combi]

    edges_dict = dict()
    already_present = set()
    for e in all_edges:
        e_sort = tuple(sorted(e))
        if e_sort in already_present:
            edges_dict.pop(e_sort)
        else:
            edges_dict[e_sort] = e
            already_present.add(e_sort)

    edges = np.array(edges_dict.values())

    # normals
    normals = np.zeros_like(points)
    count = np.zeros_like(points[:,0, np.newaxis])+1.e-10
    for i, edge in enumerate(edges):
        n = _normal_from_simplex(points[edge])
        normals[edge, :] += n/np.linalg.norm(n)
        count[edge] += 1

    normals = normals/count

    return edges, normals
