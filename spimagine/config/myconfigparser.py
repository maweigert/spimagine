from __future__ import absolute_import
from __future__ import print_function
import logging
logger = logging.getLogger(__name__)
import six
if six.PY2:
    from ConfigParser import SafeConfigParser
    import StringIO as io
else:
    from configparser import SafeConfigParser
    import io



class MyConfigParser(SafeConfigParser):
    def __init__(self,fName = None, defaults = {}):
        SafeConfigParser.__init__(self,defaults)
        self.dummySection = "DUMMY"
        if fName:
            self.read(fName)

    def read(self, fName):
        try:
            text = open(fName).read()
        except IOError:
            print("could not open %s"%fName)
        else:
            file = io.StringIO("[%s]\n%s"%(self.dummySection,text))
            self.readfp(file, fName)

    def get(self,key, defaultValue = None):
        try:
            val =  SafeConfigParser.get(self,self.dummySection,key)
            logger.debug("from config file: %s = %s "%(key,val))
            return val
        except Exception as e:
            logger.debug("%s (%s)"%(e,key))
            return defaultValue
