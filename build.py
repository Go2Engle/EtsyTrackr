import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path
import argparse

def clean_dist():
    """Clean dist and build directories"""
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist/onefile', exist_ok=True)
    os.makedirs('dist/dir', exist_ok=True)

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

def build_executable(onefile=True):
    """Build the executable for the current platform
    Args:
        onefile (bool): If True, builds a single file executable. If False, builds a directory.
    """
    # Clean build directory but preserve dist structure
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Get absolute paths for data files
    current_dir = os.path.abspath(os.path.dirname(__file__))
    modules_path = os.path.join(current_dir, 'modules')
    assets_path = os.path.join(current_dir, 'assets')
    
    # Get icon path
    icon_path = os.path.join(assets_path, 'icon.png')
    if not os.path.exists(icon_path):
        print(f"Warning: Icon not found at {icon_path}")
        icon_path = None
    
    # Determine platform-specific settings
    if sys.platform.startswith('win'):
        base_name = 'EtsyTrackr'
        exe_name = f'{base_name}.exe'
        sep = ';'
        # For Windows, convert PNG to ICO
        if icon_path:
            try:
                ico_path = os.path.join(assets_path, 'icon.ico')
                convert_to_ico(icon_path, ico_path)
                icon_path = ico_path
                print(f"Successfully created icon at: {icon_path}")
            except Exception as e:
                print(f"Warning: Could not process icon for Windows: {e}")
                icon_path = None
    elif sys.platform.startswith('darwin'):
        base_name = 'EtsyTrackr'
        exe_name = base_name
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
                new_im.save(os.path.join(assets_path, 'icon_mac.png'))
                icon_path = os.path.join(assets_path, 'icon_mac.png')
            except Exception as e:
                print(f"Warning: Could not process icon for macOS: {e}")
    else:  # Linux
        base_name = 'etsytrackr'
        exe_name = base_name
        sep = ':'
    
    # Set output directory based on mode
    output_dir = os.path.join(current_dir, 'dist', 'onefile' if onefile else 'dir')
    
    # Base PyInstaller command
    command = [
        os.path.join(current_dir, 'main.py'),
        '--windowed',
        '--workpath=build',
        '--specpath=build',
        f'--name={base_name}',
        f'--distpath={output_dir}',
        f'--add-data={modules_path}{sep}modules',
        f'--add-data={assets_path}{sep}assets'
    ]
    
    # Add onefile flag if specified
    if onefile:
        command.append('--onefile')
    
    # Add icon if available
    if icon_path:
        print(f"Using icon: {icon_path}")
        command.append(f'--icon={icon_path}')
    
    try:
        print("Starting PyInstaller build with command:", ' '.join(command))
        PyInstaller.__main__.run(command)
        print(f"Build completed! Output in {output_dir}")
        
        # Return the paths for the Inno Setup script
        if sys.platform.startswith('win'):
            return {
                'exe_path': os.path.join(output_dir, exe_name),
                'dist_dir': output_dir,
                'exe_name': exe_name,
                'base_name': base_name
            }
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Build EtsyTrackr executable')
    parser.add_argument('--mode', choices=['onefile', 'dir'], default='onefile',
                       help='Build mode: onefile for single executable, dir for directory mode')
    args = parser.parse_args()
    
    # Clean dist directory once at the start
    clean_dist()
    
    # Build both versions
    print("Building single-file version...")
    onefile_info = build_executable(onefile=True)
    print("\nBuilding directory version...")
    dir_info = build_executable(onefile=False)
