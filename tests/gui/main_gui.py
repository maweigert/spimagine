__author__ = 'mweigert'

import sys

from PyQt4 import QtGui

from spimagine.gui.mainwidget import MainWidget
from spimagine.models.data_model import DemoData, DataModel

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)


    win = MainWidget()

    win.setModel(DataModel(DemoData()))

    win.show()
    win.raise_()

    sys.exit(app.exec_())
