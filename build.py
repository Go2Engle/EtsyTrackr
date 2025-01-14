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
    elif sys.platform.startswith('darwin'):
        exe_name = 'EtsyTrackr'
    else:  # Linux
        exe_name = 'etsytrackr'
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=' + exe_name,
        '--onefile',
        '--windowed',
        '--clean',
        '--add-data=modules;modules',  # For Windows
    ]
    
    # Platform specific arguments
    if sys.platform.startswith('darwin'):
        args[4] = '--add-data=modules:modules'  # Use colon for macOS
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print(f"Build completed! Executable created in dist/{exe_name}")

if __name__ == '__main__':
    build_executable()
