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

__SYSTEM_DARWIN__ = False

if platform.system() =="Darwin":
    __SYSTEM_DARWIN__ = True
    def _parseFileNameFix(fpath):
        from subprocess import check_output
        path  = check_output(["osascript","-e","get posix path of posix file \"file://%s\" -- kthxbai"%fpath])
        print path[:-1]
        return path[:-1]


if __name__ == '__main__':
    pass
