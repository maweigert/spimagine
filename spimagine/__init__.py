import os
__CONFIGFILE__ = os.path.expanduser("~/.spimagine")


global __OPENCLDEVICE__
__OPENCLDEVICE__ = None


import ConfigParser, StringIO

class MyConfigParser(ConfigParser.ConfigParser):
    def __init__(self,fName = None):
        ConfigParser.ConfigParser.__init__(self)
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


if not __OPENCLDEVICE__:
    try:
        c = MyConfigParser(__CONFIGFILE__)
        __OPENCLDEVICE__ = int(c.get("OPENCLDEVICE"))
    except:
        __OPENCLDEVICE__ = 0


def setOpenCLDevice(num):
    global __OPENCLDEVICE__
    __OPENCLDEVICE__ = num



import logging
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)


# from spimagine.volume_render import VolumeRenderer

from spimagine.volshow import volshow, volfig
