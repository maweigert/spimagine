import os
import numpy as np
from numpy import *
from spimagine.volumerender.volume_render import VolumeRenderer
from spimagine.models.transform_model import *
from time import time
if __name__ == '__main__':
    
    os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'
    os.environ['PYOPENCL_NO_CACHE'] = '1'

    if not locals().has_key("d"):
        N = 400

        x = np.linspace(-1,1,N)
        R1 = np.sqrt(reduce(np.add,[(_X-_x)**2 for _X,_x in zip(meshgrid(x,x,x,indexing="ij"),[0,0,.2])]))
        R2 = np.sqrt(reduce(np.add,[(_X-_x)**2 for _X,_x in zip(meshgrid(x,x,x,indexing="ij"),[0,0,-.2])]))
    
        d = 255*(np.exp(-50*R1**2)+np.exp(-50*R2**2))
    
    rend = VolumeRenderer((500,500))
    rend.set_modelView(mat4_translate(0,0,5.))

    rend.set_data(d.astype(np.float32))
    rend.set_alpha_pow(0)
    t = time()
    out, out_a = rend.render(maxVal = 120.,
                             method = "max_project",
                             # method = "iso_surface",
                             numParts = 1, return_alpha = True)
    print "time to render: %.2f ms"%(1000*(time()-t))
    import pylab
    pylab.figure(1)
    pylab.clf()
    pylab.imshow(out)
    pylab.draw()
    pylab.show()
