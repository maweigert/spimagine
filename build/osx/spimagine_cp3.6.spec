import re
import os
import numpy as np

# -*- mode: python -*-

a = Analysis(
    [
        '../../spimagine/bin/spimagine_gui.py'
        #'../../spimagine/gui/foo.py'
    ],
    # dont give pathex as it leas to maximal recursion depth in recent version
    # for reasons I really dont know... 
    # pathex=['/Users/mweigert/python/spimagine/spimagine'],
    binaries=None,
    hiddenimports=[
        'scipy.special._ufuncs_cxx',
        'scipy.linalg.cython_blas',
        'scipy.linalg.cython_lapack',
        'scipy._lib.messagestream',
    ],
    excludes=["PyQt4", "matplotlib"],
    hookspath = ["hooks"],

    runtime_hooks=None)

pyz = PYZ(a.pure)




# filter binaries.. exclude some dylibs that pyinstaller packaged but
# we actually dont need (e.g. wxPython) - mostly to decrease bundle  size

def print_largest(binaries, n_biggest=10):
    bin_sorted = sorted(binaries, key = lambda x: os.path.getsize(x[1]), reverse = True)
    print("-------------   largest binaries   ---------")
    for b in bin_sorted[:n_biggest]:
        print("%.2f MB \t %s"%(os.path.getsize(b[1])/1.e6, b[1]))
                  

reg = re.compile(".*(PyQt4|CUDA|libcurand|mpl-data|tcl|zmq|PyQt5/Qt/lib/QtWebEngineCore|wxPython|matplotlib|lxml/etree).*")


print_largest(a.binaries)

a.binaries = [s for s in a.binaries if reg.match(s[1]) is None] 

print_largest(a.binaries)


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


app = BUNDLE(exe,
             name='spimagine.app',
             icon=None)




coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='full_folder')

