# -*- mode: python -*-

import os

a = Analysis(['../../spimagine/spimagine_gui.py'],
             pathex=['/Users/mweigert/python/spimagine/build/pyinstaller'],
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


# a.datas += [('myvolume_render.cl',
#             '/Users/mweigert/python/spimagine/spimagine/kernels/myvolume_render.cl','DATA')]

# a.datas += [('icon_start.png',
#             '/Users/mweigert/python/spimagine/spimagine/images/icon_start.png','DATA')]
# a.datas += [('icon_pause.png',
#             '/Users/mweigert/python/spimagine/spimagine/images/icon_pause.png','DATA')]

a.datas += addAll("../../spimagine/kernels")
a.datas += addAll("../../spimagine/images")

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          # Tree('/Users/mweigert/python/spimagine/spimagine/kernels',prefix="kernels"),

          name='spimagine',
          debug=False,
          strip=None,
          upx=True,
          console=False )

app = BUNDLE(exe,
             name='spimagine.app',
             icon=None)
