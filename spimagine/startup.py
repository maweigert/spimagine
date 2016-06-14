"""
Description

some utils functions that are called  from __init__.py

author: Martin Weigert
email: mweigert@mpi-cbg.de
"""

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
