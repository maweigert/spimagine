from __future__ import absolute_import
from __future__ import print_function
import logging

logger = logging.getLogger(__name__)

import os

from .myconfigparser import MyConfigParser
from .loadcolormaps import loadcolormaps

from gputools import init_device

__CONFIGFILE__ = os.path.expanduser("~/.spimagine")

config_parser = MyConfigParser(__CONFIGFILE__)

defaults = {
    "id_device": 0,
    "id_platform": 0,
    "use_gpu": 1,
    "colormap": "viridis",
    "texture_width": 800,
    "window_width": 900,
    "window_height": 800,
    "max_steps": 200,
    "_qualifier_constant_to_global": 0,
}


def _get_param(name, type):
    return type(config_parser.get(name, defaults[name]))


__ID_DEVICE__ = _get_param("id_device", int)

__ID_PLATFORM__ = _get_param("id_platform", int)
__USE_GPU__ = _get_param("use_gpu", int)
__DEFAULTCOLORMAP__ = _get_param("colormap", str)
__DEFAULT_TEXTURE_WIDTH__ = _get_param("texture_width", int)
__DEFAULT_WIDTH__ = _get_param("window_width", int)


__DEFAULT_HEIGHT__ = _get_param("window_height", int)
__DEFAULTMAXSTEPS__ = _get_param("max_steps", int)

__QUALIFIER_CONSTANT_TO_GLOBAL__ = _get_param("_qualifier_constant_to_global", bool)

__COLORMAPDICT__ = loadcolormaps()

init_device(id_platform=__ID_PLATFORM__,
            id_device=__ID_DEVICE__,
            use_gpu=__USE_GPU__)

# this should fix an annoying file url drag drop bug in mac yosemite
import platform

__SYSTEM_DARWIN__ = False

if platform.system() == "Darwin":
    __SYSTEM_DARWIN__ = True


    def _parseFileNameFix(fpath):
        from subprocess import check_output
        path = check_output(["osascript", "-e", "get posix path of posix file \"file://%s\" -- kthxbai" % fpath])
        path = path[:-1].decode("unicode_escape")
        print(path)
        return path

if __name__ == '__main__':
    pass
