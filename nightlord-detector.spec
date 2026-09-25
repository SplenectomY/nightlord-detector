# PyInstaller spec. Run from repo root:
#   powershell -File scripts/build_windows.ps1

from pathlib import Path

root = Path.cwd()
datas = [
    (str(root / "data"), "data"),
]
resources = root / "resources"
if resources.exists():
    datas.append((str(resources), "resources"))

a = Analysis(
    [str(root / "nightlord_detector" / "__main__.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=["pynput.keyboard._win32", "pynput.mouse._win32"],
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
    name="nightlord-detector",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
