import logging
logger = logging.getLogger(__name__)

import os

from myconfigparser import MyConfigParser        
from loadcolormaps import loadcolormaps



__CONFIGFILE__ = os.path.expanduser("~/.spimagine")
            
__spimagine_config_parser = MyConfigParser(__CONFIGFILE__)

__OPENCLDEVICE__ = int(__spimagine_config_parser.get("opencldevice",0))
__DEFAULTCOLORMAP__ = __spimagine_config_parser.get("colormap","viridis")


__DEFAULTWIDTH__ = int(__spimagine_config_parser.get("width",800))
__DEFAULTMAXSTEPS__ = int(__spimagine_config_parser.get("max_steps",200))

__COLORMAPDICT__ = loadcolormaps()


def setOpenCLDevice(num):
    global __OPENCLDEVICE__
    __OPENCLDEVICE__ = num


#this should fix an annoying file url drag drop bug in mac yosemite
import platform
__SYSTEM_DARWIN_14_AND_FOUNDATION__ = False
if platform.system() =="Darwin" and platform.release()[:2] == "14":
    try:
        import Foundation
        def _parseFileNameFix(fpath):
            return Foundation.NSURL.URLWithString_("file://"+fpath).fileSystemRepresentation()
        __SYSTEM_DARWIN_14_AND_FOUNDATION__ = True
    except ImportError:
        logger.info("PyObjc module not found!\nIt appears you are using Mac OSX Yosemite which need that package to fix a bug in the drag/dropping of files")



if __name__ == '__main__':
    pass
