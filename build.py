import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path
import site
import PySide6

def get_pyside_dir():
    """Get the PySide6 installation directory"""
    pyside_path = os.path.dirname(PySide6.__file__)
    print(f"Found PySide6 at: {pyside_path}")
    return pyside_path

def clean_dist():
    """Clean dist and build directories"""
    for dir_name in ['dist', 'build']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable for the current platform"""
    # Clean previous builds
    clean_dist()
    
    # Get PySide6 directory
    pyside_dir = get_pyside_dir()
    
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
        '--hidden-import=PySide6',
        '--hidden-import=PySide6.QtCore',
        '--hidden-import=PySide6.QtGui',
        '--hidden-import=PySide6.QtWidgets',
        '--collect-all=PySide6',
        '--collect-data=PySide6',
        '--copy-metadata=PySide6',
        f'--add-data=modules{sep}modules',
    ]
    
    # Add PySide6 binaries and plugins
    if os.path.exists(pyside_dir):
        plugins_dir = os.path.join(pyside_dir, 'plugins')
        if os.path.exists(plugins_dir):
            args.append(f'--add-binary={plugins_dir}{sep}PySide6/plugins')
        
        # Add Qt binaries
        for dll in os.listdir(pyside_dir):
            if dll.endswith('.dll'):
                dll_path = os.path.join(pyside_dir, dll)
                args.append(f'--add-binary={dll_path}{sep}.')
    
    try:
        print("Starting PyInstaller build with args:", args)
        PyInstaller.__main__.run(args)
        print(f"Build completed! Executable created in dist/{exe_name}")
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()
