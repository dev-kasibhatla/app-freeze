# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for App Freeze.

This spec file creates a single standalone binary with:
- All Python dependencies bundled
- No external Python required
- Optimized for size and startup time
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

# Determine platform
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Application metadata
APP_NAME = 'app-freeze'
APP_VERSION = '0.0.1'

# Main script
MAIN_SCRIPT = 'src/app_freeze/main.py'

# Analysis: Collect all modules and dependencies
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[],
    binaries=[],
    datas=[
        # Include any data files from prompt_toolkit if needed
        *collect_data_files('prompt_toolkit'),
    ],
    hiddenimports=[
        # prompt_toolkit dependencies
        'prompt_toolkit',
        'wcwidth',
        
        # Our modules
        'app_freeze',
        'app_freeze.adb',
        *collect_submodules('app_freeze'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'ftplib',
        'xmlrpc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols to reduce size
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Optimize for size
    optimize=2,
)

# On macOS, create an app bundle (optional)
if IS_MACOS:
    app = BUNDLE(
        exe,
        name=f'{APP_NAME}.app',
        icon=None,
        bundle_identifier=f'com.appfreeze.{APP_NAME}',
        version=APP_VERSION,
        info_plist={
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': True,
        },
    )
