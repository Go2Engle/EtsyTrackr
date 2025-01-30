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
    os.makedirs('dist/dmg', exist_ok=True)

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

def create_icns(png_path, output_path):
    """Create ICNS file for macOS from PNG"""
    print("Creating ICNS file...")
    try:
        from PIL import Image
        import tempfile
        
        # Create temporary directory for iconset
        with tempfile.TemporaryDirectory() as iconset:
            # Define icon sizes for macOS
            icon_sizes = [
                (16, '16x16'), (32, '16x16@2x'),
                (32, '32x32'), (64, '32x32@2x'),
                (128, '128x128'), (256, '128x128@2x'),
                (256, '256x256'), (512, '256x256@2x'),
                (512, '512x512'), (1024, '512x512@2x')
            ]
            
            # Open and convert source image
            img = Image.open(png_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create each size and save to iconset
            for size, name in icon_sizes:
                scaled_img = img.copy()
                scaled_img.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # Ensure icon is square with transparent background
                icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                paste_x = (size - scaled_img.width) // 2
                paste_y = (size - scaled_img.height) // 2
                icon.paste(scaled_img, (paste_x, paste_y))
                
                icon_path = os.path.join(iconset, f'icon_{name}.png')
                icon.save(icon_path)
            
            # Use iconutil to create ICNS (macOS only)
            if sys.platform == 'darwin':
                iconset_path = os.path.join(iconset, 'icon.iconset')
                os.makedirs(iconset_path, exist_ok=True)
                
                # Move files to .iconset directory with macOS naming
                for size, name in icon_sizes:
                    src = os.path.join(iconset, f'icon_{name}.png')
                    dst = os.path.join(iconset_path, f'icon_{name}.png')
                    shutil.move(src, dst)
                
                # Convert to ICNS using iconutil
                subprocess.run(['iconutil', '-c', 'icns', iconset_path, '-o', output_path], check=True)
                print(f"Successfully created ICNS file at: {output_path}")
                return output_path
    except Exception as e:
        print(f"Warning: Could not create ICNS file: {e}")
        return None

def create_mac_plist(plist_path, bundle_name, version, icon_name):
    """Create Info.plist file for macOS app bundle"""
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleDisplayName</key>
    <string>{bundle_name}</string>
    <key>CFBundleExecutable</key>
    <string>{bundle_name}</string>
    <key>CFBundleIconFile</key>
    <string>{icon_name}</string>
    <key>CFBundleIdentifier</key>
    <string>com.go2engle.etsytrackr</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{bundle_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>CFBundleVersion</key>
    <string>{version}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>"""
    
    with open(plist_path, 'w', encoding='utf-8') as f:
        f.write(plist_content)
    return plist_path

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

def sign_mac_app(app_path):
    """Sign the macOS app bundle with ad-hoc signature"""
    try:
        print("Signing app bundle...")
        # Create an ad-hoc signature
        cmd = ['codesign', '--force', '--deep', '--sign', '-', app_path]
        subprocess.run(cmd, check=True)
        print(f"Successfully signed app bundle at: {app_path}")
        return True
    except Exception as e:
        print(f"Warning: Could not sign app bundle: {e}")
        return False

def build_dmg():
    """Build DMG for macOS"""
    print("Building DMG...")
    
    try:
        # First build the app bundle
        print("Building app bundle...")
        result = build_executable(onefile=False)
        if not result:
            print("Error: Failed to build app bundle")
            return False
            
        app_path = os.path.join(result['dist_dir'], f"{result['base_name']}.app")
        if not os.path.exists(app_path):
            print(f"Error: App bundle not found at {app_path}")
            return False
            
        # Sign the app bundle
        sign_mac_app(app_path)
            
        print(f"Found app bundle at: {app_path}")
        print("App bundle contents:")
        os.system(f"ls -R {app_path}")
        
        # Create DMG
        print("\nCreating DMG...")
        dmg_dir = os.path.join('dist', 'dmg')
        os.makedirs(dmg_dir, exist_ok=True)
        dmg_path = os.path.join(dmg_dir, 'EtsyTrackr.dmg')
        
        # Remove existing DMG
        if os.path.exists(dmg_path):
            print(f"Removing existing DMG: {dmg_path}")
            os.remove(dmg_path)
        
        # Create DMG using create-dmg
        cmd = [
            'create-dmg',
            '--volname', 'EtsyTrackr',
            '--volicon', os.path.join('assets', 'icon.icns'),
            '--window-pos', '200', '120',
            '--window-size', '800', '400',
            '--icon-size', '100',
            '--icon', 'EtsyTrackr.app', '200', '200',
            '--hide-extension', 'EtsyTrackr.app',
            '--app-drop-link', '600', '200',
            dmg_path,
            app_path
        ]
        
        print("Running create-dmg command:", ' '.join(cmd))
        subprocess.run(cmd, check=True)
        
        if os.path.exists(dmg_path):
            print(f"Successfully created DMG at: {dmg_path}")
            return True
        else:
            print(f"Error: DMG not found at expected path: {dmg_path}")
            return False
            
    except Exception as e:
        print(f"Error creating DMG: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

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
    
    # Get icon path and version
    from modules.version import VersionChecker
    version = VersionChecker.CURRENT_VERSION.lstrip('v')
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
                # Create ICNS file for macOS
                icns_path = os.path.join(assets_path, 'icon.icns')
                icon_path = create_icns(icon_path, icns_path)
                print(f"Successfully created ICNS file at: {icon_path}")
                
                # Create Info.plist template if building directory
                if not onefile:
                    plist_path = os.path.join(current_dir, 'Info.plist')
                    create_mac_plist(plist_path, base_name, version, 'icon.icns')
                    print(f"Created Info.plist at: {plist_path}")
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
    
    # Add platform-specific options
    if sys.platform.startswith('darwin') and not onefile:
        command.extend([
            '--osx-bundle-identifier=com.go2engle.etsytrackr'
        ])
    
    # Add icon if available
    if icon_path:
        print(f"Using icon: {icon_path}")
        command.append(f'--icon={icon_path}')
    
    # Add onefile flag if specified
    if onefile:
        command.append('--onefile')
    
    try:
        print("Starting PyInstaller build with command:", ' '.join(command))
        PyInstaller.__main__.run(command)
        print(f"Build completed! Output in {output_dir}")
        
        # For macOS, handle Info.plist and app bundle
        if sys.platform == 'darwin' and not onefile:
            app_path = os.path.join(output_dir, f'{base_name}.app')
            if os.path.exists(app_path):
                # Copy Info.plist to the app bundle
                contents_path = os.path.join(app_path, 'Contents')
                plist_path = os.path.join(current_dir, 'Info.plist')
                if os.path.exists(plist_path):
                    dest_plist = os.path.join(contents_path, 'Info.plist')
                    shutil.copy2(plist_path, dest_plist)
                    print(f"Copied Info.plist to app bundle at: {dest_plist}")
                
                # Copy icon to Resources
                if icon_path and icon_path.endswith('.icns'):
                    resources_path = os.path.join(contents_path, 'Resources')
                    os.makedirs(resources_path, exist_ok=True)
                    icon_dest = os.path.join(resources_path, 'icon.icns')
                    shutil.copy2(icon_path, icon_dest)
                    print(f"Copied icon to app bundle at: {icon_dest}")
        
        # Return the paths for any platform
        result = {
            'exe_path': os.path.join(output_dir, exe_name),
            'dist_dir': output_dir,
            'exe_name': exe_name,
            'base_name': base_name
        }
        
        return result
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
    parser.add_argument('--mode', choices=['onefile', 'dir', 'appimage', 'dmg'], default='onefile',
                       help='Build mode: onefile for single executable, dir for directory mode, appimage for Linux AppImage, dmg for macOS DMG')
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
    elif args.mode == 'dmg':
        if not sys.platform.startswith('darwin'):
            print("DMG can only be built on macOS")
            sys.exit(1)
        build_dmg()
    else:
        # Build both versions
        print("Building single-file version...")
        onefile_info = build_executable(onefile=True)
        print("\nBuilding directory version...")
        dir_info = build_executable(onefile=False)
