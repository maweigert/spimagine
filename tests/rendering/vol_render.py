"""

mweigert@mpi-cbg.de
"""

import os
import numpy as np
from spimagine.utils.transform_matrices import mat4_translate
from spimagine.volumerender.volume_render import VolumeRenderer

if __name__ == '__main__':

    os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'
    os.environ['PYOPENCL_NO_CACHE'] = '1'

    N= 64

    x = np.linspace(-1,1,N)
    R = np.sqrt(np.sum([_X**2 for _X in np.meshgrid(x,x,x,indexing="ij")],axis=0))

    d = np.exp(-50*(R-.3)**2)

    rend = VolumeRenderer((400,400))
    rend.set_modelView(mat4_translate(0,0,5.))

    rend.set_data(d.astype(np.float32))
    out = rend.render(maxVal = 1., method = "max_project_part")
    # out = rend.render(maxVal = 1., method = "iso_surface")

    rend2 = VolumeRenderer((400,400))
    rend2.set_modelView(mat4_translate(0,0,5.))

    rend2.set_data(d.astype(np.float32))
    out2 = rend2.render(maxVal = 1., method = "max_project_part")

    import pylab
    pylab.figure(1)
    pylab.clf()
    pylab.imshow(out)
    pylab.show()