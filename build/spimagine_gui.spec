# -*- mode: python -*-
a = Analysis(['../spimagine/spimagine_gui.py'],
             pathex=['c:\\Users\\myerslab\\python\\spimagine\\build'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='spimagine_gui.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
