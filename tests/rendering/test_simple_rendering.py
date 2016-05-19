"""

mweigert@mpi-cbg.de
"""

import numpy as np
from spimagine.volumerender.volume_render import VolumeRenderer
import pylab
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def test_simple_rendering():
    from gputools.utils.utils import remove_cache_dir, get_cache_dir
    remove_cache_dir()

    dtypes = [np.float32, np.uint16]

    # build some test data
    N = 128
    x = np.linspace(-1,1,N)
    Z,Y,X = np.meshgrid(x,x,x,indexing="ij")
    R1 = np.sqrt((X-.2)**2+Y**2+Z**2)
    R2 = np.sqrt((X+.2)**2+Y**2+Z**2)
    data = 255*np.exp(-30*R1**2)+ np.exp(-30*R2**2)

    rend = VolumeRenderer((400,400))
    outs = []

    for dtype in dtypes:
        rend.render(data=data.astype(dtype), maxVal = 255.)
        outs.append(rend.output)

    # drawing
    #pylab.ioff()
    pylab.figure(1)
    pylab.clf()
    for i,out in enumerate(outs):
        pylab.subplot(1,len(outs),i+1)
        pylab.imshow(out)
        pylab.axis("off")
        pylab.title("%s"%(dtype))

    pylab.show()
    pylab.pause(2)
    return rend

def test_surface():
    from spimagine.utils.transform_matrices import *
    N = 128
    x = np.linspace(-1,1,N)
    Z,Y,X = np.meshgrid(x,x,x,indexing="ij")
    R = np.sqrt(X**2+Y**2+Z**2)

    data = 900.*np.exp(-10*R)
    #data = 200*(1+Z)

    rend = VolumeRenderer((400,400))


    rend.set_modelView(mat4_translate(0,0,-5.))
    rend.render(data=data.astype(np.uint16), maxVal = 20., method="iso_surface")
    #rend.render(data=data.astype(np.float32), maxVal = 100., method="max_project")

    # drawing
    #pylab.ioff()
    pylab.figure(1)
    pylab.clf()

    pylab.imshow(rend.output)
    pylab.axis("off")

    pylab.show()
    pylab.pause(.1)
    return rend


if __name__ == "__main__":
    from gputools import remove_cache_dir

    remove_cache_dir()
    #rend = test_simple_rendering()
    rend = test_surface()
    out = rend.output
