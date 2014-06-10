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

def volshow(data, glWindow = None, scale = True, stackUnits = [1,1,1]):
    app = createApp()

    if not glWindow:
        window = MainWindow()
        window.show()
        window.raise_()
        glWindow = window.glWidget
        app.references = set()
        app.references.add(window)

    if scale:
        ma,mi = amax(data), amin(data)
        data = 16000.*(data-mi)/(ma-mi)


    glWindow.renderer.set_data(data)

    glWindow.transform.reset(amax(data),stackUnits)
    return glWindow


if __name__ == '__main__':

    app = createApp()

    data = DemoData(50)[0]

    w = volshow(data)


    if app:
        sys.exit(app.exec_())
