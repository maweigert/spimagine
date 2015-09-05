# -*- mode: python -*-

import os

def addAll(folderPath,attrib = "Data", prefix = ""):
    res = []
    for fold, subs, files in os.walk(folderPath):
        for fName in files:
            res += [(prefix+fName,os.path.join(fold,fName),attrib)]

    return res


a = Analysis(['../spimagine/bin/spimagine_gui.py'],
             pathex=['/Users/mweigert/python/spimagine/spimagine'],
             hiddenimports=[
                 'scipy.special._ufuncs_cxx',
                 'scipy.linalg.cython_blas',
                 'scipy.linalg.cython_lapack',
                 "pyfft",
                 "pyopencl"],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)



a.datas += addAll("../spimagine/volumerender/kernels")
a.datas += addAll("../spimagine/gui/images")
a.datas += addAll("../spimagine/colormaps")


a.datas += addAll("/Users/mweigert/python/gputools/gputools/convolve/kernels")
a.datas += addAll("/Users/mweigert/python/gputools/gputools/transforms/kernels")
a.datas += addAll("/Users/mweigert/python/pyopencl/build/lib.macosx-10.9-x86_64-2.7/pyopencl/cl")

a.datas += addAll("../spimagine/data/")

a.datas += addAll("/Library/Python/2.7/site-packages/pyfft", prefix="pyfft/")

print a.datas

with open("_DATAS.txt","w") as f:
    f.write(str(a.datas))

with open("_BINARIES.txt","w") as f:
    f.write(str(a.binaries))

with open("_PURE.txt","w") as f:
    f.write(str(a.pure))

print a.binaries


# filter binaries.. exclude some dylibs that pyinstaller packaged but
# we actually dont need (e.g. wxPython)

import re
reg = re.compile(".*(sparsetools|QtWebKit|wxPython|matplotlib).*")

a.binaries = [s for s in a.binaries if reg.match(s[1]) is None] 


with open("_BINARIES_FILTER.txt","w") as f:
    f.write(str(a.binaries))


pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='spimagine',
          # debug=False,
          debug=True,
          strip=None,
          upx=True,
          console=False )

app = BUNDLE(exe,
             name='spimagine.app',
             icon=None)


# b = Analysis(['../spimagine/spim_render.py'],
#              pathex=['/Users/mweigert/python/spimagine/spimagine'],
#              hiddenimports=[],
#              hookspath=None,
#              runtime_hooks=None)
# pyz = PYZ(b.pure)


# b.datas += addAll("../spimagine/kernels")

# b.datas += addAll("/Library/Python/2.7/site-packages/libtiff")

# b.binaries += [("libtiff.5.dylib","/usr/local/lib/libtiff.5.dylib","BINARY")]


# pyz = PYZ(b.pure)
# exe = EXE(pyz,
#           b.scripts,
#           b.binaries,
#           b.zipfiles,
#           b.datas,
#           name='spimagine_render',
#           debug=True,
#           strip=None,
#           upx=True,
#           console=True)
