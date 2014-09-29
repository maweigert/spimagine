# -*- mode: python -*-

import os

def addAll(folderPath,attrib = "Data"):
    res = []
    for fold, subs, files in os.walk(folderPath):
        for fName in files:
            res += [(fName,os.path.join(fold,fName),attrib)]

    return res


a = Analysis(['../spimagine/spimagine_gui.py'],
             pathex=['/Users/mweigert/python/spimagine/spimagine',
                     '/Library/Python/2.7/site-packages/libtiff'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)



a.datas += addAll("../spimagine/kernels")
a.datas += addAll("../spimagine/images")
a.datas += addAll("../spimagine/colormaps")

# include the libtiff dylib and all the py files (work around)
a.datas += addAll("/Library/Python/2.7/site-packages/libtiff")
# a.datas += [("tiff_h_4_0_3.py","/Library/Python/2.7/site-packages/libtiff/tiff_h_4_0_3.py","Data")]


print a.datas

# a.binaries += addAll("/usr/local/Cellar/libtiff/4.0.3/lib/","BINARY")


# a.binaries += [("libtiff.dylib","/usr/local/lib/libtiff.dylib","BINARY")]

# a.binaries += [("libtiff.dylib","/usr/local/Cellar/libtiff/4.0.3/lib/libtiff.dylib","BINARY")]

print a.binaries


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

b.binaries += [("libtiff.5.dylib","/usr/local/lib/libtiff.5.dylib","BINARY")]


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
