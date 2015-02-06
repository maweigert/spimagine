import sys
from PyQt4 import QtCore, QtGui
from sortedcontainers import SortedDict

from imageprocessor import *

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

    def __init__(self):
        super(QtGui.QWidget,self).__init__()

        self.resize(100, 30)


        
        hbox = QtGui.QHBoxLayout()




class MainWindow(QtGui.QMainWindow):

    def __init__(self, ):
        super(QtGui.QMainWindow,self).__init__()

        self.resize(300, 200)
        self.setWindowTitle('Test')

        foo  = ImageProcessorView()
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
