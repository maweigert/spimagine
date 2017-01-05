"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division

import numpy as np
from spimagine.volumerender.volumerender import VolumeRenderer
from spimagine.utils import mat4_translate

# two test functions to get the ray coordinates in the kernel...
def _getOrig(P, M, u=1, v=0):
    orig0 = dot(inv(P), [u, v, -1, 1])
    orig0 = dot(inv(M), orig0)
    orig0 = orig0/orig0[-1]
    return orig0


def _getDirec(P, M, u=1, v=0):
    direc0 = dot(inv(P), [u, v, 1, 1])
    direc0 = direc0/direc0[-1];
    orig0 = dot(inv(P), [u, v, -1, 1]);
    direc0 = direc0-orig0;
    direc0 = direc0/norm(direc0)
    return dot(inv(M), direc0)


def test_simple():
    import matplotlib.pyplot as plt

    N = 64
    d = np.linspace(0, 1, N**3).reshape((N,)*3).astype(np.float32)

    rend = VolumeRenderer((400, 400))

    rend.set_data(d)
    rend.render()
    out = rend.output
    plt.imshow(out)
    plt.show()

def test_time_to_render():
    import time
    from gputools import get_device

    get_device().print_info()
    N = 256

    x = np.linspace(-1, 1, N)
    Z, Y, X = np.meshgrid(x, x, x, indexing="ij")
    R = np.sqrt(X**2+Y**2+Z**2)

    d = 10000*np.exp(-10*R**2)

    rend = VolumeRenderer((600, 600))


    rend.set_modelView(mat4_translate(0, 0, -10.))

    # rend.set_box_boundaries(.3*np.array([-1,1,-1,1,-1,1]))
    t1 = time.time()

    get_device().queue.finish()
    rend.set_data(d, autoConvert=True)
    get_device().queue.finish()

    t2 = time.time()

    get_device().queue.finish()
    rend.render(maxVal=10000.)
    out = rend.output
    get_device().queue.finish()

    print("time to set data %s^3:\t %.2f ms"%(N, 1000*(t2-t1)))

    print("time to render %s^3:\t %.2f ms"%(N, 1000*(time.time()-t2)))

    return d, rend, out



def test_speed_multipass():
    import time
    from gputools import get_device

    N = 256


    x = np.linspace(-1, 1, N)
    Z, Y, X = np.meshgrid(x, x, x, indexing="ij")
    R = np.sqrt(X ** 2 + Y ** 2 + Z ** 2)

    d = 200 * np.exp(-10 * R ** 2)

    rend = VolumeRenderer((800,) * 2)

    rend.set_modelView(mat4_translate(0, 0, -10.))


    rend.set_data(d.astype(np.float32))

    get_device().queue.finish()

    for niter in range(1, 10):
        get_device().queue.finish()
        t = time.time()
        rend.render(method="max_project", maxVal=200.,
                    currentPart=0, numParts=niter)
        get_device().queue.finish()
        print("time to render with %s substeps:\t %.2f ms" % (niter, 1000 * (time.time() - t)))

    return rend

if __name__=="__main__":
    rend = test_speed_multipass()

