# PyInstaller spec. Run from repo root:
#   scripts\build_windows.cmd

from PyInstaller.utils.hooks import collect_all, collect_submodules
from pathlib import Path

root = Path.cwd()
datas = [
    (str(root / "data"), "data"),
    (str(root / "locales"), "locales"),
]
resources = root / "resources"
if resources.exists():
    datas.append((str(resources), "resources"))

binaries = []
hiddenimports = [
    "mss",
    "mss.windows",
    "mss.screenshot",
    "mss.tools",
    "PIL",
    "PIL.Image",
    "PIL.ImageFilter",
    "PIL.ImageOps",
    "pytesseract",
    "rapidfuzz",
    "rapidfuzz.fuzz",
    "rapidfuzz.process",
    "pynput",
    "pynput.keyboard",
    "pynput.mouse",
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "nightlord_detector",
    "nightlord_detector.i18n",
    "nightlord_detector.capture",
    "nightlord_detector.config",
    "nightlord_detector.debug_console",
    "nightlord_detector.match",
    "nightlord_detector.overlay",
    "nightlord_detector.paths",
    "nightlord_detector.predict",
]
for pkg in ("mss", "PIL", "pytesseract", "rapidfuzz", "pynput"):
    hiddenimports += collect_submodules(pkg)
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

# Dedup while keeping order
hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    [str(root / "nightlord_detector" / "__main__.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["numpy", "tkinter.test"],
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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
