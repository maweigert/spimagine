# -*- mode: python -*-
import re
from glob import glob
import os


def get_qt5_binaries():

    qt_sos = glob("/usr/local/lib/python2.7/dist-packages/PyQt5/*.so")

    return [(so,os.path.basename(so)) for so in qt_sos]


def addAll(root ,attrib = "Data", prefix = "", keep_relative_structure = False, reg_str = ".*"):
    reg = re.compile(reg_str)
    res = []
    for fold, subs, files in os.walk(root):
        rel_dir = os.path.relpath(fold,root)
        for fName in files:
            if reg.match(fName):
                if keep_relative_structure:
                    name = os.path.join(prefix,rel_dir, fName)
                else:
                    name = os.path.join(prefix, fName)

                joined = os.path.join(fold,fName)
                joined.replace("/./","/")
                res += [(name,joined,attrib)]
    return res


print "XXXXXX"*100
print addAll("/usr/local/lib/python2.7/dist-packages/pyopencl/",
                  prefix = "",
                  reg_str = "(.*\.cl|.*\.h)",
                  keep_relative_structure = False)
print "XXXXXX"*100

print addAll("/usr/local/lib/python2.7/dist-packages/pyopencl/",
                  prefix = "pyopencl/",
                  keep_relative_structure = True)




a = Analysis(['../spimagine/bin/spimagine_gui.py'],
             pathex=['/home/mweigert/python/spimagine/spimagine'],
             binaries=get_qt5_binaries(),
             hiddenimports=[
                 'scipy.special._ufuncs_cxx',
                 'scipy.linalg.cython_blas',
                 'scipy.linalg.cython_lapack',
                 "pyopencl",
                 "reikna",
                 "PyQt5"],
             excludes=["PyQt4"],

             hookspath = ["hooks"],

             runtime_hooks=None)

pyz = PYZ(a.pure)



a.datas += addAll("/home/mweigert/python/gputools/gputools/core/kernels")
a.datas += addAll("/home/mweigert/python/gputools/gputools/denoise/kernels")
a.datas += addAll("/home/mweigert/python/gputools/gputools/deconv/kernels")
a.datas += addAll("/home/mweigert/python/gputools/gputools/convolve/kernels")
a.datas += addAll("/home/mweigert/python/gputools/gputools/noise/kernels")
a.datas += addAll("/home/mweigert/python/gputools/gputools/fft/kernels")
a.datas += addAll("/home/mweigert/python/gputools/gputools/transforms/kernels")


a.datas += addAll("/usr/local/lib/python2.7/dist-packages/pyopencl/",
                  prefix = "pyopencl/",
                  keep_relative_structure = True)


a.datas += addAll("/usr/local/lib/python2.7/dist-packages/pyopencl/",
                  prefix = "",
                  reg_str = "(.*\.cl|.*\.h)",
                  keep_relative_structure = False)


a.datas += addAll("/usr/local/lib/python2.7/dist-packages/reikna",
                  reg_str = ".*\.mako",
                  prefix = "reikna/",
                  keep_relative_structure=True)


a.datas += addAll("../spimagine/volumerender/kernels")
a.datas += addAll("../spimagine/gui/shaders")

a.datas += addAll("../spimagine/gui/images")
a.datas += addAll("../spimagine/colormaps")
a.datas += addAll("../spimagine/data/")



# filter binaries.. exclude some dylibs that pyinstaller packaged but
# we actually dont need (e.g. wxPython)

import re
reg = re.compile(".*(PyQt4|PyQt5\.Qt|mpl-data|tcl|zmq|QtWebKit|wxPython|matplotlib).*")
a.binaries = [s for s in a.binaries if reg.match(s[1]) is None] 


with open("_BINARIES.log","w") as f:
    f.write(str(a.binaries))
with open("_PURE.log","w") as f:
    f.write(str(a.pure))
with open("_DATAS.log","w") as f:
    f.write(str(a.pure))


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='spimagine',
          #debug=False,
          debug=True,
          strip=None,
          upx=True,
          console=False )


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='full_folder')

