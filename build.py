import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path

def clean_dist():
    """Clean dist and build directories"""
    for dir_name in ['dist', 'build']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable for the current platform"""
    # Clean previous builds
    clean_dist()
    
    # Determine platform-specific settings
    if sys.platform.startswith('win'):
        exe_name = 'EtsyTrackr.exe'
        sep = ';'
    elif sys.platform.startswith('darwin'):
        exe_name = 'EtsyTrackr'
        sep = ':'
    else:  # Linux
        exe_name = 'etsytrackr'
        sep = ':'
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=' + exe_name,
        '--onefile',
        '--windowed',
        '--clean',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        f'--add-data=modules{sep}modules',
    ]
    
    try:
        print("Starting PyInstaller build with args:", args)
        PyInstaller.__main__.run(args)
        print(f"Build completed! Executable created in dist/{exe_name}")
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()
