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
    from itertools import chain


class MyConfigParser(SafeConfigParser):
    def __init__(self, fName=None, defaults={}):
        SafeConfigParser.__init__(self, defaults)
        self.dummySection = "dummy"
        if fName:
            self.read(fName)

    def read(self, fName):
        try:
            with open(fName) as f:
                if six.PY2:
                    f = io.StringIO("[%s]\n%s" % (self.dummySection, f.read()))
                    self.readfp(f)
                else:
                    f = chain(("[%s]"%self.dummySection,), f)
                    self.read_file(f)

        except Exception as e:
            print(e)



    def get(self, key, defaultValue=None, **kwargs):
        try:
            val = SafeConfigParser.get(self, self.dummySection, key,**kwargs)
            logger.debug("from config file: %s = %s " % (key, val))

            return val
        except Exception as e:
            logger.debug("%s (%s)" % (e, key))
            return defaultValue



if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    import os
    __CONFIGFILE__ = os.path.expanduser("~/.spimagine")
    config_parser = MyConfigParser(__CONFIGFILE__)

    print(config_parser.get("window_width", -1))
    print(config_parser.get("window_height", -1))
