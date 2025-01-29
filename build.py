import PyInstaller.__main__
import sys
import os
import shutil
from pathlib import Path
import argparse
import subprocess
import stat

def clean_dist():
    """Clean dist and build directories"""
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    os.makedirs('dist/onefile', exist_ok=True)
    os.makedirs('dist/dir', exist_ok=True)
    os.makedirs('dist/appimage', exist_ok=True)

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

def create_desktop_file(output_dir):
    """Create .desktop file for Linux"""
    desktop_content = """[Desktop Entry]
Name=EtsyTrackr
Comment=Track and manage your Etsy shop finances and inventory
Exec=etsytrackr
Icon=etsytrackr
Terminal=false
Type=Application
Categories=Office;Finance;
Keywords=etsy;shop;tracking;finance;inventory;"""
    
    desktop_path = os.path.join(output_dir, 'etsytrackr.desktop')
    with open(desktop_path, 'w') as f:
        f.write(desktop_content)
    return desktop_path

def build_executable(onefile=True):
    """Build the executable for the current platform
    Args:
        onefile (bool): If True, builds a single file executable. If False, builds a directory.
    Returns:
        dict: Dictionary containing paths and names of the built executable
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
        
        # Return the paths for any platform
        return {
            'exe_path': os.path.join(output_dir, exe_name),
            'dist_dir': output_dir,
            'exe_name': exe_name,
            'base_name': base_name
        }
    except Exception as e:
        print(f"Error during build: {str(e)}")
        sys.exit(1)

def build_appimage(pyinstaller_dir):
    """Build AppImage from PyInstaller directory"""
    print("Creating AppImage...")
    
    # Create AppDir structure
    appdir = os.path.join('dist', 'appimage', 'EtsyTrackr.AppDir')
    if os.path.exists(appdir):
        shutil.rmtree(appdir)
    os.makedirs(appdir)
    
    # Copy PyInstaller build to AppDir
    shutil.copytree(os.path.join(pyinstaller_dir, 'etsytrackr'), os.path.join(appdir, 'usr', 'bin'))
    
    # Create symlink for AppRun
    os.symlink('usr/bin/etsytrackr', os.path.join(appdir, 'AppRun'))
    
    # Copy and set up icons in standard Linux directory structure
    icon_sizes = ['16x16', '32x32', '48x48', '64x64', '128x128', '256x256', '512x512']
    icon_source = 'assets/icon.png'
    
    # Create base icon directories
    for size in icon_sizes:
        icon_dir = os.path.join(appdir, 'usr', 'share', 'icons', 'hicolor', size, 'apps')
        os.makedirs(icon_dir, exist_ok=True)
        
        # Convert and save icon for each size
        try:
            from PIL import Image
            img = Image.open(icon_source)
            size_px = int(size.split('x')[0])
            resized_img = img.resize((size_px, size_px), Image.Resampling.LANCZOS)
            resized_img.save(os.path.join(icon_dir, 'etsytrackr.png'))
        except Exception as e:
            print(f"Warning: Could not create {size} icon: {e}")
            # Fallback to copying original icon
            shutil.copy2(icon_source, os.path.join(icon_dir, 'etsytrackr.png'))
    
    # Copy original icon to root of AppDir (required by AppImage spec)
    shutil.copy2(icon_source, os.path.join(appdir, 'etsytrackr.png'))
    os.symlink('etsytrackr.png', os.path.join(appdir, '.DirIcon'))
    
    # Create and copy desktop file
    desktop_dir = os.path.join(appdir, 'usr', 'share', 'applications')
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_file = create_desktop_file(desktop_dir)
    shutil.copy2(desktop_file, appdir)
    
    # Create AppStream metadata
    metainfo_dir = os.path.join(appdir, 'usr', 'share', 'metainfo')
    os.makedirs(metainfo_dir, exist_ok=True)
    
    # Save a screenshot for AppStream
    screenshot_dir = os.path.join(appdir, 'usr', 'share', 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    shutil.copy2(icon_source, os.path.join(screenshot_dir, 'screenshot.png'))
    
    metainfo_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>etsytrackr.desktop</id>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <name>EtsyTrackr</name>
  <summary>Track and manage your Etsy shop finances and inventory</summary>
  <description>
    <p>
      EtsyTrackr helps you manage your Etsy shop by tracking finances, inventory,
      and providing insights into your shop's performance.
    </p>
  </description>
  
  <launchable type="desktop-id">etsytrackr.desktop</launchable>
  
  <screenshots>
    <screenshot type="default">
      <image>https://raw.githubusercontent.com/go2engle/EtsyTrackr/main/assets/icon.png</image>
      <caption>EtsyTrackr main window</caption>
    </screenshot>
  </screenshots>
  
  <url type="homepage">https://github.com/go2engle/EtsyTrackr</url>
  
  <provides>
    <binary>etsytrackr</binary>
  </provides>
  
  <developer_name>go2engle</developer_name>
  
  <releases>
    <release version="1.0.0" date="2025-01-29">
      <description>
        <p>Initial release of EtsyTrackr</p>
      </description>
    </release>
  </releases>
  
  <content_rating type="oars-1.1" />
</component>"""
    
    with open(os.path.join(metainfo_dir, 'etsytrackr.appdata.xml'), 'w') as f:
        f.write(metainfo_content)
    
    # Download AppImage tool if not present
    apptool_path = os.path.join('build', 'appimagetool-x86_64.AppImage')
    if not os.path.exists(apptool_path):
        os.makedirs('build', exist_ok=True)
        subprocess.run([
            'wget', 'https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage',
            '-O', apptool_path
        ], check=True)
        os.chmod(apptool_path, os.stat(apptool_path).st_mode | stat.S_IEXEC)
    
    # Build AppImage with validation disabled
    subprocess.run([
        apptool_path,
        '--no-appstream',  # Skip AppStream validation
        appdir,
        os.path.join('dist', 'appimage', 'EtsyTrackr-x86_64.AppImage')
    ], check=True)
    
    print("AppImage created successfully!")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Build EtsyTrackr executable')
    parser.add_argument('--mode', choices=['onefile', 'dir', 'appimage'], default='onefile',
                       help='Build mode: onefile for single executable, dir for directory mode, appimage for Linux AppImage')
    args = parser.parse_args()
    
    # Clean dist directory once at the start
    clean_dist()
    
    if args.mode == 'appimage':
        if not sys.platform.startswith('linux'):
            print("AppImage can only be built on Linux")
            sys.exit(1)
        print("Building directory version for AppImage...")
        dir_info = build_executable(onefile=False)
        build_appimage(dir_info['dist_dir'])
    else:
        # Build both versions
        print("Building single-file version...")
        onefile_info = build_executable(onefile=True)
        print("\nBuilding directory version...")
        dir_info = build_executable(onefile=False)
