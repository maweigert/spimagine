import sys
from PyQt4 import QtGui

from SpimRender.gui_mainwindow import MainWindow

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())
