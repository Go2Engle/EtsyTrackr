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

def convert_to_ico(png_path, ico_path):
    """Convert PNG to ICO with multiple sizes"""
    from PIL import Image
    img = Image.open(png_path)
    
    # Ensure RGBA mode
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create ICO with multiple sizes
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_sizes = []
    
    for size in sizes:
        resized_img = img.copy()
        resized_img.thumbnail(size, Image.Resampling.LANCZOS)
        icon_sizes.append(resized_img)
    
    # Save as ICO with all sizes
    icon_sizes[0].save(ico_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in icon_sizes], append_images=icon_sizes[1:])
    return ico_path

def build_executable():
    """Build the executable for the current platform"""
    # Clean previous builds
    clean_dist()
    
    # Get icon path
    icon_path = os.path.join('assets', 'icon.png')
    if not os.path.exists(icon_path):
        print(f"Warning: Icon not found at {icon_path}")
        icon_path = None
    
    # Determine platform-specific settings
    if sys.platform.startswith('win'):
        exe_name = 'EtsyTrackr.exe'
        sep = ';'
        # For Windows, convert PNG to ICO
        if icon_path:
            try:
                ico_path = os.path.join('assets', 'icon.ico')
                convert_to_ico(icon_path, ico_path)
                icon_path = ico_path
                print(f"Successfully created icon at: {icon_path}")
            except Exception as e:
                print(f"Warning: Could not process icon for Windows: {e}")
                icon_path = None
    elif sys.platform.startswith('darwin'):
        exe_name = 'EtsyTrackr'
        sep = ':'
        if icon_path:
            try:
                from PIL import Image
                im = Image.open(icon_path)
                # Ensure icon is square
                size = max(im.size)
                new_im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                new_im.paste(im, ((size - im.size[0]) // 2, (size - im.size[1]) // 2))
                # Save as PNG for macOS app bundle
                new_im.save(os.path.join('assets', 'icon_mac.png'))
                icon_path = os.path.join('assets', 'icon_mac.png')
            except Exception as e:
                print(f"Warning: Could not process icon for macOS: {e}")
    else:  # Linux
        exe_name = 'etsytrackr'
        sep = ':'
    
    # Base PyInstaller command
    command = [
        'main.py',
        '--onefile',
        '--windowed',
        '--clean',
        f'--name={exe_name}',
        f'--add-data=modules{sep}modules',
        f'--add-data=assets{sep}assets'
    ]
    
    # Add icon if available
    if icon_path:
        print(f"Using icon: {icon_path}")
        command.append(f'--icon={icon_path}')
    
    try:
        print("Starting PyInstaller build with command:", ' '.join(command))
        PyInstaller.__main__.run(command)
        print(f"Build completed! Executable created in dist/{exe_name}")
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    build_executable()
