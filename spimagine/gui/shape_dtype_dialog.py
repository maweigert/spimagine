"""

mweigert@mpi-cbg.de
"""
from __future__ import print_function, unicode_literals, absolute_import, division

import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5 import QtGui


class ShapeDtypeDialog(QtWidgets.QDialog):
    type_dict = {
        "uint16": np.uint16,
        "float32": np.float32,
        "uint8": np.uint8,
    }

    def __init__(self, parent=None):
        super(ShapeDtypeDialog, self).__init__(parent)

        self.setWindowTitle("set stack dimensions")
        self.shape = (512, 512, 1, 1)
        self.dtype = ShapeDtypeDialog.type_dict["uint16"]

        layout = QtWidgets.QVBoxLayout(self)

        self.edits = []

        grid = QtWidgets.QGridLayout()
        #
        # grid.setColumnStretch(1, 4)
        # grid.setColumnStretch(2, 4)

        for i, (t, s) in enumerate(zip(("x", "y", "z",  "t"), self.shape)):
            grid.addWidget(QtWidgets.QLabel(t), i, 0)
            edit = QtWidgets.QLineEdit(str(s))
            edit.setValidator(QtGui.QIntValidator(1,2**20))
            self.edits.append(edit)
            grid.addWidget(edit, i, 1)

        self.combo = self.create_combo()
        grid.addWidget(QtWidgets.QLabel("type"), len(self.shape), 0)
        grid.addWidget(self.combo, len(self.shape), 1)

        layout.addLayout(grid)
        # OK and Cancel buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

    def create_combo(self):
        combo = QtWidgets.QComboBox(self)
        for t in sorted(self.type_dict.keys()):
            combo.addItem(t)
        return combo

    def parse_properties(self):
        self.shape = tuple(int(edit.text()) for edit in self.edits)[::-1]
        self.dtype = self.type_dict[self.combo.currentText()]


    @staticmethod
    def get_properties(parent=None):
        dialog = ShapeDtypeDialog(parent)
        result = dialog.exec_()
        dialog.parse_properties()
        shape = dialog.shape
        dtype = dialog.dtype

        return (shape, dtype, result == QtWidgets.QDialog.Accepted)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    shape, dtype, res = ShapeDtypeDialog.get_properties()

    print(shape)
    print(dtype)
