import logging
logger = logging.getLogger(__name__)

import ConfigParser
import StringIO


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

    def get(self,key, defaultValue = None):
        try:
            val =  ConfigParser.ConfigParser.get(self,self.dummySection,key)
            logger.debug("from config file: %s = %s "%(key,val))
            return val
        except Exception as e:
            logger.debug("%s (%s)"%(e,key))
            return defaultValue
