import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path
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
    print(f"PySide6 directory contents: {os.listdir(pyside_dir)}")
    
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
        '--hidden-import=PySide6.QtSvg',
        '--hidden-import=PySide6.QtNetwork',
        f'--add-data=modules{sep}modules',
    ]
    
    # Add PySide6 binaries and data
    qt_plugins = ['platforms', 'styles', 'imageformats']
    for plugin in qt_plugins:
        plugin_path = os.path.join(pyside_dir, 'plugins', plugin)
        if os.path.exists(plugin_path):
            print(f"Adding Qt plugin: {plugin}")
            args.append(f'--add-data={plugin_path}{sep}PySide6/plugins/{plugin}')
    
    # Add Qt binaries
    for file in os.listdir(pyside_dir):
        if file.endswith(('.dll', '.pyd')):
            file_path = os.path.join(pyside_dir, file)
            print(f"Adding Qt binary: {file}")
            args.append(f'--add-data={file_path}{sep}.')
    
    try:
        print("Starting PyInstaller build with args:", args)
        PyInstaller.__main__.run(args)
        print(f"Build completed! Executable created in dist/{exe_name}")
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()
