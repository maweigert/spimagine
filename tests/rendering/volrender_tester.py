
import os
import sys
import shutil
import numpy as np

from PyQt4 import QtGui, QtCore

from spimagine.gui.mainwidget import MainWidget
from spimagine.models.data_model import DataModel, NumpyData

from gputools import OCLProgram

CACHEDIRS = ["~/.nv/ComputeCache","~/.cache/pyopencl/pyopencl-compiler-cache-v2-py2.7.6.final.0"]

CACHEDIRS = [os.path.expanduser(_C) for _C in CACHEDIRS]

import spimagine

def absPath(myPath):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, os.path.basename(myPath))
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, myPath)



class MyWidget(MainWidget):
    def __init__(self):
        super(MyWidget,self).__init__()

        self.compileTimer = QtCore.QTimer(self)
        self.compileTimer.setInterval(2000)
        self.compileTimer.timeout.connect(self.on_compile_timer)
        self.compileTimer.start()

    def on_compile_timer(self):
        for c in CACHEDIRS:
            if os.path.exists(c):
                print "removing cache: ", c
                shutil.rmtree(c)

        print "compiling..."


        try:
            dirname = os.path.join(os.path.dirname(spimagine.volumerender.__file__),"kernels")
            build_options = ["-cl-fast-relaxed-math",
                                    "-cl-unsafe-math-optimizations",
                                    "-cl-mad-enable",
                                    "-I %s" %dirname,
                                    "-D maxSteps=%s"%spimagine.config.__DEFAULTMAXSTEPS__]

            kerns = ["volume_kernel.cl","iso_kernel.cl","all_render_kernels.cl"]
            #enforce recompilations....
            for k in kerns:
                OCLProgram(os.path.join(dirname,k), build_options = build_options)

            proc = OCLProgram(os.path.join(dirname,"iso_kernel.cl"),
                                   build_options = build_options)

            self.glWidget.renderer.proc = proc
            self.glWidget.refresh()
            print np.amin(self.glWidget.output),np.amax(self.glWidget.output)



        except Exception as e:
            print e

    def closeEvent(self,event):
        self.compileTimer.stop()
        super(MyWidget,self).closeEvent(event)






if __name__ == '__main__':


    x = np.linspace(-1,1,64)
    Z,Y,X = np.meshgrid(x,x,x)
    R1 = np.sqrt((X+.35)**2+(Y+.0)**2+(Z+.0)**2)
    R2 = np.sqrt((X-.35)**2+(Y-.0)**2+(Z-.0)**2)
    d = np.exp(-10*R1**2)+np.exp(-10*R2**2)

    app = QtGui.QApplication(sys.argv)

    win = MyWidget()

    win.setModel(DataModel(NumpyData(d)))
    win.transform.setIso(True)
    win.transform.setZoom(1.2)
    win.show()

    win.raise_()

    sys.exit(app.exec_())

