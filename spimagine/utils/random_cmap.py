import numpy as np
def random_cmap(n=2**16, l_min = 0.4, l_max = 1.):
    """ random colormap to be used for labeled images (where 0=background is black)"""
    import matplotlib
    import colorsys
    h,l,s = np.random.uniform(0,1,n), l_min + (l_max-l_min)*np.random.uniform(0,1.,n), 0.2 + np.random.uniform(0,0.8,n)
    cols = np.stack([colorsys.hls_to_rgb(_h,_l,_s) for _h,_l,_s in zip(h,l,s)],axis=0)
    cols[0] = 0
    return matplotlib.colors.ListedColormap(cols)

