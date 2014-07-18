# -*- mode: python -*-

import os

def addAll(folderPath):
    res = []
    for fold, subs, files in os.walk(folderPath):
        for fName in files:
            res += [(fName,os.path.join(fold,fName),'Data')]

    return res


a = Analysis(['../spimagine/spimagine_gui.py'],
             pathex=['/Users/mweigert/python/spimagine/spimagine'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)



a.datas += addAll("../spimagine/kernels")
a.datas += addAll("../spimagine/images")

a.datas += addAll("/Library/Python/2.7/site-packages/libtiff")


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='spimagine',
          debug=True,
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
b.datas += addAll("/Library/Python/2.7/site-packages/libtiff")

pyz = PYZ(b.pure)
exe = EXE(pyz,
          b.scripts,
          b.binaries,
          b.zipfiles,
          b.datas,
          name='spimagine_render',
          debug=True,
          strip=None,
          upx=True,
          console=True)
