from __future__ import absolute_import
from PyQt5 import QtGui, QtWidgets
import os


class MultipleFileDialog(QtWidgets.QFileDialog):
    def __init__(self, *args):
        QtWidgets.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, False)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QtWidgets.QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QtWidgets.QTreeView)

    def openClicked(self):
        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(os.path.join(str(self.directory().absolutePath()),str(i.data().toString())))
        self.selectedFiles = files
        self.hide()

    def filesSelected(self):
        return self.selectedFiles


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)

    win = MultipleFileDialog()

    win.exec_()

    # path = QtWidgets.QFileDialog.getOpenFileNames(None, 'Open Tif File',
    #                                           '.', selectedFilter='*.tif')

