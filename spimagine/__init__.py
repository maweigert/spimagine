import os
__CONFIGFILE__ = os.path.expanduser("~/.spimagine")


global __OPENCLDEVICE__
global __DEFAULTCOLORMAP__

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
            raise IOError()
        else:
            file = StringIO.StringIO("[%s]\n%s"%(self.dummySection,text))
            self.readfp(file, fName)

    def get(self,varStr):
        return ConfigParser.ConfigParser.get(self,self.dummySection,varStr)


try:
    c = MyConfigParser(__CONFIGFILE__,{"opencldevice":"0","colormap":"coolwarm"})
    __OPENCLDEVICE__ = int(c.get("opencldevice"))
    __DEFAULTCOLORMAP__ = c.get("colormap")
except:
    __OPENCLDEVICE__ = 0
    __DEFAULTCOLORMAP__ = "coolwarm"


from gui_utils import absPath, arrayFromImage

import re

def _load_colormaps():
    global __COLORMAPDICT__
    __COLORMAPDICT__ = {}
    basePath = absPath("colormaps")
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



import logging
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)


# from spimagine.volume_render import VolumeRenderer

from volshow import volshow, volfig
