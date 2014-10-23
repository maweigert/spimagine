global __OPENCLDEVICE__

def setOpenCLDevice(num):
    global __OPENCLDEVICE__
    __OPENCLDEVICE__ = num


setOpenCLDevice(0)

    
import logging
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)



from spimagine.volume_render import *

from spimagine.volshow import volshow, volfig
