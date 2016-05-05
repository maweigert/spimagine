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


if __name__ == "__main__":

    test_simple_rendering()
