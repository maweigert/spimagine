import sys
import numpy as np
import os

from PyQt4 import QtCore, QtGui

from collections import OrderedDict


import spimagine

from spimagine.gui.mainwidget import MainWidget


from spimagine.models.data_model import DataModel, SpimData, TiffData, TiffFolderData,GenericData, EmptyData, DemoData, NumpyData

_MAIN_APP = None

#FIXME app issue

import logging
logger = logging.getLogger(__name__)

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import sys

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug("found MEIPASS: %s "%os.path.join(base_path, os.path.basename(myPath)))

        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)



def getCurrentApp():
    app = QtGui.QApplication.instance()

    if not app:
        app = QtGui.QApplication(sys.argv)

    if not hasattr(app,"volfigs"):
        app.volfigs = OrderedDict()

    global _MAIN_APP
    _MAIN_APP = app
    return _MAIN_APP



def volfig(num=None, raise_window = True):
    """return window"""

    logger.debug("volfig")


    app = getCurrentApp()
    app.setWindowIcon(QtGui.QIcon(absPath('images/spimagine.png')))
    
    #filter the dict
    app.volfigs =  OrderedDict((n,w) for n,w in app.volfigs.iteritems() if w.isVisible())


    if not num:
        if len(app.volfigs.keys())==0:
            num = 1
        else:
            num = max(app.volfigs.iterkeys())+1

    if app.volfigs.has_key(num):
        window = app.volfigs[num]
        app.volfigs.pop(num)
    else:
        window = MainWidget()
        window.show()
    #make num the last window
    app.volfigs[num] = window

    if raise_window:
        window.raise_()

    return window


def volshow(data, autoscale = True,
            stackUnits = [1.,1.,1.],
            blocking = False,
            cmap = None,
            raise_window = True):
    """
    class to visualize 3d/4d data

    data can be

    - a 3d/4d numpy array of dimensions (z,y,x) or (t,z,y,x)

      e.g.


volshow( randint(0,10,(10, 20,30,40) )


    - an instance of a class derived from the abstract bass class GenericData

      e.g.

from spimagine.data_model import GenericData

class myData(GenericData):
    def __getitem__(self,i):
        return (100*i+3)*ones((100,100,100)
    def size(self):
        return (4,100,100,100)

volshow(myData())

        or
from spimagine.data_model import DataModel

volshow(DataModel(dataContainer=myData(), prefetchSize= 5)



    returns window.glWidget if not in blocking mode


    available colormaps: cmap = ["coolwarm","jet","hot","grays"]
    if cmap = None, then the default one is used

    """

    logger.debug("volshow")

    logger.debug("volshow: getCurrentApp")

    app = getCurrentApp()



    from time import time

    t = time()

    # check whether there are already open windows, if not create one
    try:
        num,window = [(n,w) for n,w in app.volfigs.iteritems()][-1]
    except:
        num = 1

    window = volfig(num, raise_window = raise_window)

    logger.debug("volfig: %s s "%(time()-t))
    t = time()

    # if isinstance(data,GenericData):
    if hasattr(data,"stackUnits"):
        m = DataModel(data)
    elif isinstance(data,DataModel):
        m = data
    else:
        if not isinstance(data,np.ndarray):
            data = np.array(data)
        if autoscale:
            ma,mi = np.amax(data), np.amin(data)
            if ma==mi:
                ma +=1.
            data = 1000.*(data-mi)/(ma-mi)

        m = DataModel(NumpyData(data.astype(np.float32,copy=False)))


    logger.debug("create model: %s s "%( time()-t))
    t = time()

    window.setModel(m)

    if cmap is None or not spimagine.config.__COLORMAPDICT__.has_key(cmap):
        cmap = spimagine.config.__DEFAULTCOLORMAP__


    window.glWidget.set_colormap(cmap)



    logger.debug("set model: %s s"%( time()-t));
    t = time()

    window.glWidget.transform.setStackUnits(*stackUnits)

    if blocking:
        getCurrentApp().exec_()
    else:
        return window


def qt_exec():
    getCurrentApp().exec_()


class TimeData(GenericData):
    def __init__(self,func, dshape):
        """ func(i) returns the volume
        dshape is [Nt,Nz,Nx,Ny]
        """
        self.func = func
        self.dshape = dshape

        GenericData.__init__(self)

    def __getitem__(self,i):
        return self.func(i)

    def size(self):
        return self.dshape


if __name__ == '__main__':

    volshow(DemoData(),blocking = True)

