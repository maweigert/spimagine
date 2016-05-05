"""

mweigert@mpi-cbg.de
"""

from gputools import OCLImage

from spimagine.volumerender.volume_render import VolumeRenderer

import numpy as np

if __name__ == "__main__":


    x = np.linspace(0,10000,50**3).reshape((50,)*3).astype(np.float32)
    
    v= VolumeRenderer((800,800))

    im =  OCLImage.empty_like(x)
    
    print np.var(x)
    print id(x)
    im.write_array(x)
    print id(x)
    # print np.var(x)
    
