# -*- mode: python -*-

a = Analysis(['../../spimagine/bin/spimagine_gui.py'],
             binaries=None,
             hiddenimports=[
                 'scipy.special._ufuncs_cxx',
                 'scipy.linalg.cython_blas',
                 'scipy.linalg.cython_lapack',
                 'scipy._lib.messagestream',
                ],
             excludes=["PyQt4"],
             hookspath = ["hooks"],

             runtime_hooks=None)

pyz = PYZ(a.pure)


# filter binaries.. exclude some dylibs that pyinstaller packaged but
# we actually dont need (e.g. wxPython)

import re
reg = re.compile(".*(PyQt4|mpl-data|tcl|curand|zmq|QtWebKit|wxPython|matplotlib).*")

a.binaries = [s for s in a.binaries if reg.match(s[1]) is None] 

print(a.binaries)

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          icon="spimagine.ico",
          name='spimagine',
          debug=False,
          #debug=True,
          strip=None,
          upx=True,
          console=False )

