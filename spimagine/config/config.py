import logging
logger = logging.getLogger(__name__)

import os

from myconfigparser import MyConfigParser        
from loadcolormaps import loadcolormaps

from gputools import init_device

__CONFIGFILE__ = os.path.expanduser("~/.spimagine")
            
            
config_parser = MyConfigParser(__CONFIGFILE__)

__ID_DEVICE__ = int(config_parser.get("id_device", 0))
__ID_PLATFORM__ = int(config_parser.get("id_platform", 0))
__USE_GPU__ = int(config_parser.get("use_gpu", 1))

__DEFAULTCOLORMAP__ = config_parser.get("colormap","viridis")


__DEFAULTWIDTH__ = int(config_parser.get("width",800))
__DEFAULTMAXSTEPS__ = int(config_parser.get("max_steps",200))

__COLORMAPDICT__ = loadcolormaps()

init_device(id_platform = __ID_PLATFORM__,
            id_device = __ID_DEVICE__,
            use_gpu = __USE_GPU__)

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
