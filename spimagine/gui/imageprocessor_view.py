import sys

import numpy as np

from PyQt4 import QtCore, QtGui, Qt
from sortedcontainers import SortedDict

from spimagine.models.imageprocessor import ImageProcessor

from spimagine.gui import gui_utils

class ImageFlow(QtCore.QObject):
    # _dataPosChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        self.processors = SortedDict()


    def add_processor(self,processor):
        self.processors[len(self.processors)] = processor

    def apply(self,data):
        if len(self.processors) == 0:
            return data

        data = data.copy()
        for p in self.processors.values():
            data = p.apply(data)

        return data




def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    import os
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)


checkBoxStyleStr = """
    QCheckBox::indicator:checked {
    background:black;
    border-image: url(%s);}
    QCheckBox::indicator:unchecked {
    background:black;
    border-image: url(%s);}
    """

def createImgCheckBox(fName_active,fName_inactive):
    checkBox = QtGui.QCheckBox()
    checkBox.setStyleSheet(
            checkBoxStyleStr%(absPath(fName_active),absPath(fName_inactive)))
    return checkBox



class ImageProcessorView(QtGui.QWidget):
    _stateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, proc = None):
        super(QtGui.QWidget,self).__init__()

        self.resize(100, 50)
        self.set_processor(proc)
        self.initUI()


    def set_processor(self,proc):
        self.proc = proc


    def initUI(self):
        if self.proc is None:
            return


        # def createStandardCheckbox(parent, img1=None , img2 = None, tooltip = ""):

        vbox = QtGui.QVBoxLayout()

        gridBox = QtGui.QGridLayout()

        self.checkActive = gui_utils.createImageCheckbox(self,
                                                         absPath("images/icon_processor_active"),
                                                         absPath("images/icon_processor_inactive"))


        label = QtGui.QLabel(self.proc.name)

        gridBox.addWidget(self.checkActive,0,0)

        gridBox.addWidget(label,0,1)

        for i, (key, val)  in enumerate(self.proc.kwargs.iteritems()):
            dtype = type(val)
            if dtype == bool:
                check = QtGui.QCheckBox("",self)
                check.stateChanged.connect(self.set_proc_attr_check(check,key,val))
                gridBox.addWidget(QtGui.QLabel(key),i+1,0)
                gridBox.addWidget(check,i+1,1)

            elif dtype in (int,float,np.int,np.float):
                edit = QtGui.QLineEdit(str(val))
                edit.setValidator(QtGui.QDoubleValidator())
                edit.returnPressed.connect(self.set_proc_attr_edit(edit,key,dtype))
                gridBox.addWidget(QtGui.QLabel(key),i+1,0)
                gridBox.addWidget(edit,i+1,1)

        vbox.addLayout(gridBox)
        vbox.addStretch()

        self.setLayout(vbox)
        self.setSizePolicy(Qt.QSizePolicy.Minimum,Qt.QSizePolicy.Minimum)
        self.setStyleSheet("""
        QFrame,QLabel,QLineEdit {
        color: white;
        }
        """)

        self.checkActive.stateChanged.connect(lambda x:self._stateChanged.emit(x!=0))
        # self._stateChanged.connect(self.foo)



    def set_proc_attr_edit(self,obj, key , dtype):
        # print "set proc edit"
        def func():
            # print "setting", key , obj.text()
            setattr(self.proc,key, dtype(obj.text()))
            self._stateChanged.emit(-1)
        return func

    def set_proc_attr_check(self,obj, key , dtype):
        def func():
            # print "setting", key , obj.checkState() !=0
            setattr(self.proc,key, obj.checkState() !=0)
            self._stateChanged.emit(-1)
        return func

    def is_active(self):
        return self.checkActive.checkState() != 0



class ImageProcessorListView(QtGui.QWidget):
    _stateChanged = QtCore.pyqtSignal()
    def __init__(self, imps = []):
        super(QtGui.QWidget,self).__init__()

        self.impViews = [ImageProcessorView(p) for p in imps]

        vbox = QtGui.QVBoxLayout()
        self.gridBox = QtGui.QGridLayout()


        for impView in self.impViews:
            self._include_imp_view(impView)

        vbox.addLayout(self.gridBox)

        vbox.addStretch()

        self.setLayout(vbox)
        self.setSizePolicy(Qt.QSizePolicy.Minimum,Qt.QSizePolicy.Minimum)
        self.setStyleSheet("""
        QFrame,QLabel,QLineEdit {
        color: white;
        }
        """)

    def _include_imp_view(self,impView):
        impView._stateChanged.connect(self.stateChanged)
        # print self.gridBox.rowCount()
        self.gridBox.addWidget(impView,self.gridBox.rowCount(),0)
        # line =  QtGui.QFrame()
        # line.setFrameShape(QtGui.QFrame.HLine)
        # self.mainBox.addWidget(line)


    def add_image_processor(self, imp):
        impView = ImageProcessorView(imp)
        self.impViews.append(impView)
        self._include_imp_view(impView)
        self._stateChanged.emit()


    def stateChanged(self):
        self._stateChanged.emit()



class MainWindow(QtGui.QMainWindow):

    def __init__(self, ):
        super(QtGui.QMainWindow,self).__init__()

        self.resize(300, 200)
        self.setWindowTitle('Test')

        foo  = ImageProcessorListView([
            imageprocessor.BlurProcessor(),
            imageprocessor.FFTProcessor()
        ])

        
        foo.add_image_processor(imageprocessor.BlurProcessor())


        def myfunc(data,para=1.):
            print "myfunc with para", para
            return data*para

        imp = imageprocessor.FuncProcessor(myfunc,"myfunc",para=.1)
        foo.add_image_processor(imp)

        
        self.setCentralWidget(foo)
        self.setStyleSheet("background-color:black;")

    def close(self):
        QtGui.qApp.quit()



if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    win = MainWindow()
    win.show()
    win.raise_()

    sys.exit(app.exec_())


# if __name__ == '__main__':

#     import imgtools


#     ipf = ImageProcessorFlow()


#     ips.add_processor(BlurProcessor())
#     ips.add_processor(CopyProcessor())


#     Z,Y,X = imgtools.ZYX(128)

#     data = 100*np.exp(-100*(X**2+Y**2+Z**2))

#     data += 10.*np.random.normal(0,1.,data.shape)


#     y = ips.apply(data)
