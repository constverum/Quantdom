# -*- mode: python -*-

block_cipher = None


a = Analysis(
  ['quantdom/app.py'],
  pathex=['./quantdom'],
  binaries=[],
  datas=[('./quantdom/report_rows.json', '.')],
  hiddenimports=['pandas._libs.tslibs.timedeltas'],
  hookspath=[],
  runtime_hooks=[],
  excludes=['tkinter'],
  win_no_prefer_redirects=False,
  win_private_assemblies=False,
  cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
  pyz,
  a.scripts,
  a.binaries,
  a.zipfiles,
  a.datas,
  name='quantdom',
  debug=False,
  strip=False,
  upx=True,
  runtime_tmpdir=None,
  console=False)

app = BUNDLE(
  exe,
  name='quantdom.app',
  icon=None,
  bundle_identifier=None)
