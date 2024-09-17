# -*- mode: python -*-
a = Analysis(['.\cli.py'],
             pathex=['.\pdfprofile'],
             hiddenimports=['lxml'],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win64\\pdfprofile', 'pdfprofile.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=True )

profiles_tree = Tree('./pdfprofile/profiles', prefix = 'profiles')
schemas_tree = Tree('./pdfprofile/schemas', prefix = 'schemas')
          
coll = COLLECT(exe,
               a.binaries +
               [('./license/LICENSE.txt','LICENSE','DATA')],
               profiles_tree,
               schemas_tree,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist_win64', 'pdfprofile'))
