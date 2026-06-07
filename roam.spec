# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Roam. Build with:  pyinstaller roam.spec
# Produces a one-folder application under dist/Roam/ (dist/Roam/Roam.exe on
# Windows, dist/Roam/Roam on macOS/Linux), plus a dist/Roam.app bundle on macOS.
#
# Data files are bundled at the same relative paths the game already uses
# ("assets/...", "schemas/...", "config.yml"); src/appPaths.prepareWorkingDirectory()
# chdir's into the bundle at startup so those relative paths resolve when frozen.
import os
import sys

# Platform icon: .ico on Windows, .icns on macOS. Both are generated at build
# time (and gitignored); only set the icon if present so a from-source build
# without it still succeeds.
if sys.platform == "darwin":
    iconPath = os.path.join("src", "media", "icon.icns")
else:
    iconPath = os.path.join("src", "media", "icon.ico")
icon = iconPath if os.path.exists(iconPath) else None

a = Analysis(
    [os.path.join("src", "roam.py")],
    pathex=["src", os.path.join("src", "entity")],
    binaries=[],
    datas=[
        ("assets", "assets"),
        ("schemas", "schemas"),
        ("config.yml", "."),
        (os.path.join("src", "media"), os.path.join("src", "media")),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name="Roam",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Roam",
)

# On macOS, wrap the one-folder output in a .app bundle (dist/Roam.app).
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Roam.app",
        icon=icon,
        bundle_identifier="com.preponderous.roam",
    )
