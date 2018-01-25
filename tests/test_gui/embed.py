import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QPushButton
from spimagine.gui.mainwidget import MainWidget



class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super(MainWindow,self).__init__()

        self.button = QPushButton("push me", self)
        self.canvas = MainWidget(self)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.button)
        vbox.addWidget(self.canvas, stretch=3)

        self.setLayout(vbox)
        self.resize(800,800)
        self.canvas.setStyleSheet("""
        background-color:black;
        color:black;
        """)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)


    mainWin = MainWindow()
    mainWin.show()


    sys.exit(app.exec_())