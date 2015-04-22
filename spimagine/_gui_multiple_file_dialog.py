from PyQt4 import QtGui
import os


class MultipleFileDialog(QtGui.QFileDialog):
    def __init__(self, *args):
        QtGui.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, False)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QtGui.QPushButton)
        self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QtGui.QTreeView)

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

    app = QtGui.QApplication(sys.argv)

    win = MultipleFileDialog()

    win.exec_()

    # path = QtGui.QFileDialog.getOpenFileNames(None, 'Open Tif File',
    #                                           '.', selectedFilter='*.tif')

