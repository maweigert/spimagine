# -*- mode: python -*-

import os

a = Analysis(['../spimagine/spimagine_gui.py'],
             pathex=['/Users/mweigert/python/spimagine/spimagine'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)


def addAll(folderPath):
    res = []
    for fold, subs, files in os.walk(folderPath):
        for fName in files:
            res += [(fName,os.path.join(fold,fName),'Data')]

    return res

a.datas += addAll("../spimagine/kernels")
a.datas += addAll("../spimagine/images")

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='spimagine',
          debug=False,
          strip=None,
          upx=True,
          console=False )

app = BUNDLE(exe,
             name='SpImagine.app',
             icon=None)


b = Analysis(['../spimagine/spim_render.py'],
             pathex=['/Users/mweigert/python/spimagine/spimagine'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(b.pure)


b.datas += addAll("../spimagine/kernels")

pyz = PYZ(b.pure)
exe = EXE(pyz,
          b.scripts,
          b.binaries,
          b.zipfiles,
          b.datas,
          name='spimagine_render',
          debug=False,
          strip=None,
          upx=True,
          console=True)

