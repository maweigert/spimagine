import os
__CONFIGFILE__ = os.path.expanduser("~/.spimagine")


import logging
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)



global __OPENCLDEVICE__
global __DEFAULTCOLORMAP__
global __DEFAULTWIDTH__
global __COLORMAPDICT__

import ConfigParser, StringIO

import sys



class MyConfigParser(ConfigParser.SafeConfigParser):
    def __init__(self,fName = None, defaults = {}):
        ConfigParser.SafeConfigParser.__init__(self,defaults)
        self.dummySection = "DUMMY"
        if fName:
            self.read(fName)

    def read(self, fName):
        try:
            text = open(fName).read()
        except IOError:
            print "could not open %s"%fName
        else:
            file = StringIO.StringIO("[%s]\n%s"%(self.dummySection,text))
            self.readfp(file, fName)

    def get(self,key, defaultVal):
        try:
            return ConfigParser.ConfigParser.get(self,self.dummySection,key)
        except:
            return defaultVal

    



# try:
#     __spimagine_config_parser = MyConfigParser(__CONFIGFILE__,{"opencldevice":"0","colormap":"coolwarm"})
#     __OPENCLDEVICE__ = int(__spimagine_config_parser.get("opencldevice"))
#     __DEFAULTCOLORMAP__ = __spimagine_config_parser.get("colormap")
# except:
#     __OPENCLDEVICE__ = 0
#     __DEFAULTCOLORMAP__ = "coolwarm"

__spimagine_config_parser = MyConfigParser(__CONFIGFILE__,{"opencldevice":"0","colormap":"hot","width":800})
__OPENCLDEVICE__ = int(__spimagine_config_parser.get("opencldevice",0))
__DEFAULTCOLORMAP__ = __spimagine_config_parser.get("colormap","hot")
__DEFAULTWIDTH__ = int(__spimagine_config_parser.get("width",800))


from spimagine.gui_utils import arrayFromImage

# try:
#     print os.listdir(sys._MEIPASS)
# except:
#     pass

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.DEBUG("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)

import re

def _load_colormaps():
    global __COLORMAPDICT__
    __COLORMAPDICT__ = {}

    try:
        basePath = sys._MEIPASS
    except:
        basePath = absPath("colormaps/")

    reg = re.compile("cmap_(.*)\.png")
    for fName in os.listdir(basePath):
        match = reg.match(fName)
        if match:
            try:
                __COLORMAPDICT__[match.group(1)] = arrayFromImage(os.path.join(basePath,fName))[0,:,:]
            except:
                print "could not load %s"%fName


_load_colormaps()

def setOpenCLDevice(num):
    global __OPENCLDEVICE__
    __OPENCLDEVICE__ = num





# from spimagine.volume_render import VolumeRenderer

from volshow import volshow, volfig, TimeData

from data_model import SpimData, TiffData, NumpyData


#this should fix an annoying file url drag drop bug in mac yosemite
import platform
if platform.system() =="Darwin" and platform.release()[:2] == "14":
    try:
        import Foundation
    except ImportError:
        raise("PyObjc module not found!\nIt appears you are using Mac OSX Yosemite which need that package to fix a bug")

    _SYSTEM_DARWIN_14 = True
    def _parseFileNameFix(fpath):
        return Foundation.NSURL.URLWithString_("file://"+fpath).fileSystemRepresentation()
else:
    _SYSTEM_DARWIN_14 = False
