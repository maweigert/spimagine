from __future__ import absolute_import, print_function
from .version import __version__

# try:
#     from pkg_resources import get_distribution, DistributionNotFound
#     __version__ = get_distribution("spimagine").version
# except Exception as e:
#     print(e)


import logging
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)


from spimagine.config import config

from spimagine.models.data_model import DataModel,DemoData, SpimData, TiffData, CZIData, TiffFolderData, NumpyData

from spimagine.models.transform_model import TransformModel, TransformData

from spimagine.utils.imgutils import read3dTiff, write3dTiff

from spimagine.gui.volshow import volshow, volfig, qt_exec

from spimagine.gui.mainwidget import MainWidget

from spimagine.gui.mesh import Mesh, SphericalMesh, EllipsoidMesh

from spimagine.utils import *

from spimagine.models import *