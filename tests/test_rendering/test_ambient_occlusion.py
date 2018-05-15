"""

mweigert@mpi-cbg.de
"""

from __future__ import absolute_import
import numpy as np
from spimagine.volumerender.volumerender import VolumeRenderer
from spimagine.utils.transform_matrices import *

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def render_iso(data, is_ao=True):
    from gputools.utils.utils import remove_cache_dir, get_cache_dir
    remove_cache_dir()

    rend = VolumeRenderer((400, 400))

    if is_ao:
        rend.set_occ_strength(1)
        rend.set_occ_radius(101)
        rend.set_occ_n_points(1000)
    else:
        rend.set_occ_strength(0)
        rend.set_occ_radius(21)
        rend.set_occ_n_points(30)

    rend.set_modelView(mat4_translate(0, 0, -1.))

    rend.render(data, maxVal=70., method="iso_surface")

    return rend


if __name__ == "__main__":
    from gputools import remove_cache_dir

    remove_cache_dir()

    # build some test data
    if not "data" in locals():
        N = 128
        x = np.linspace(-1, 1, N)
        Z, Y, X = np.meshgrid(x, x, x, indexing="ij")
        R1 = np.sqrt(2*(X - .2) ** 2 + Y ** 2 + Z ** 2)
        R2 = np.sqrt(2*(X + .2) ** 2 + Y ** 2 + Z ** 2)
        data = 255 * (np.exp(-30 * R1 ** 2) + np.exp(-30 * R2 ** 2))
        data += np.random.uniform(0, 1, data.shape)
        data = data.astype(np.float32)

    rend1 = render_iso(data, is_ao=False)
    rend2 = render_iso(data, is_ao=True)

    import matplotlib.pyplot as plt

    plt.figure(1)
    plt.clf()
    plt.subplot(1, 2, 1)
    plt.imshow(rend1.output)
    plt.axis('off')
    plt.subplot(1, 2, 2)
    plt.imshow(rend2.output)
    plt.axis('off')

    plt.show()
