import sys
from PyQt4 import QtGui

from spimagine.gui_mainwindow import MainWindow

def main():

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())



if __name__== '__main__':
    main()
