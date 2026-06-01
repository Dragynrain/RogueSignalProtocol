# -*- mode: python ; coding: utf-8 -*-
# Linux-specific PyInstaller spec file
# Build with: pyinstaller RogueSignalProtocol-linux.spec
import sys

from PyInstaller.utils.hooks import collect_submodules

# Auto-discover every rsp submodule so PyInstaller bundles the whole package.
# Using collect_submodules instead of a hand-maintained list prevents this spec and
# RogueSignalProtocol.spec from drifting - a stale list once shipped this Linux
# binary with no rsp package ("ModuleNotFoundError: No module named 'rsp'").
# 'src' must be importable for discovery to find the package.
sys.path.insert(0, "src")
rsp_hiddenimports = collect_submodules("rsp")

a = Analysis(
    ['RogueSignalProtocol.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=rsp_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RogueSignalProtocol',  # No .exe extension on Linux
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.png',  # PNG for Linux instead of .ico
)
