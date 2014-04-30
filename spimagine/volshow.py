import sys
from PyQt4 import QtCore,QtGui


from spimagine.gui_mainwindow import MainWindow

from spimagine.data_model import DemoData
from numpy import *


def createApp():
    app = QtCore.QCoreApplication.instance()
    if app == None:
        app = QtGui.QApplication(sys.argv)
    return app

def volshow(data, window = None, scale = True):
    app = createApp()

    if not window:
        window = MainWindow()
        window.show()
        window.raise_()

    app.references = set()
    app.references.add(window)

    if scale:
        ma,mi = amax(data), amin(data)
        data = 16000.*(data-mi)/(ma-mi)
        
    window.glWidget.renderer.set_data(data)
    window.glWidget.transform.reset(amax(data))
    return window


if __name__ == '__main__':

    app = createApp()

    data = DemoData()[0]

    volshow(data)

    if app:
        sys.exit(app.exec_())
