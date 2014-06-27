import sys
import numpy as np

from PyQt4 import QtCore,QtGui

from collections import OrderedDict
from spimagine.gui_mainwindow import MainWindow

from spimagine.data_model import DataModel, EmptyData, DemoData, NumpyData

_MAIN_APP = None

#FIXME app issue

def getCurrentApp():
    app = QtGui.QApplication.instance()

    if not app:
        app = QtGui.QApplication(sys.argv)

    if not hasattr(app,"volfigs"):
        app.volfigs = OrderedDict()

    global _MAIN_APP
    _MAIN_APP = app
    return _MAIN_APP



def volfig(num=None):
    """return window"""

    app = getCurrentApp()
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
        window = MainWindow(dataContainer=EmptyData())
        window.show()

    #make num the last window
    app.volfigs[num] = window
    window.raise_()
    return window



def volshow(data, scale = True, stackUnits = [.1,.1,.1], blocking = False ):
    """return window.glWidget if not in blocking mode """
    app = getCurrentApp()

    # check whether there are already open windows, if not create one
    try:
        num,window = [(n,w) for n,w in app.volfigs.iteritems()][-1]
    except:
        num = 1

    window = volfig(num)

    if scale:
        ma,mi = np.amax(data)+1, np.amin(data)
        data = 16000.*(data-mi)/(ma-mi)

    m = DataModel(NumpyData(data.astype(np.float32)))
    # m = NumpyData(data.astype(np.float32))
    # window = MainWindow(dataContainer = m)

    window.glWidget.setModel(m)

    if blocking:
        getCurrentApp().exec_()
    else:
        return window.glWidget


if __name__ == '__main__':

    N = 256
    # d = np.linspace(0,100,N**3).reshape((N,)*3)
    d = np.zeros((100,)*3,dtype=np.float32)
    d[50,:,:] = 1.

    
    volshow(d, blocking = True)
