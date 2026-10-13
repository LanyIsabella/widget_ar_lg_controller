# PyInstaller one-file build for the Windows desktop widget.
from PyInstaller.utils.hooks import collect_submodules


hiddenimports = collect_submodules("thinqconnect")

a = Analysis(
    ["../src/lg_ac_controller/main.py"],
    pathex=["../src"],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LGAcController",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
