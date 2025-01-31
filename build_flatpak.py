#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

def create_flatpak_icon():
    """Create a properly sized icon for the Flatpak package from the existing assets/icon.png"""
    # Use ImageMagick to resize the icon while maintaining aspect ratio and adding transparent padding
    subprocess.run([
        'convert',
        'assets/icon.png',
        '-background', 'none',
        '-gravity', 'center',
        '-resize', '200x200',  # Resize to slightly smaller to ensure padding
        '-extent', '256x256',  # Add transparent padding to make it 256x256
        'PNG32:flatpak/icon.png'
    ], check=True)

def build_flatpak():
    """Build the Flatpak package"""
    # Ensure the dist/flatpak directory exists
    flatpak_dist = Path('dist/flatpak')
    flatpak_dist.mkdir(parents=True, exist_ok=True)
    
    # Clean up any existing flatpak build files
    flatpak_dir = Path('flatpak')
    if flatpak_dir.exists():
        shutil.rmtree(flatpak_dir)
    flatpak_dir.mkdir()
    
    # Copy Flatpak manifest and metadata files
    manifest_content = '''app-id: com.go2engle.EtsyTrackr
runtime: org.freedesktop.Platform
runtime-version: '23.08'
sdk: org.freedesktop.Sdk
command: etsytrackr
finish-args:
  - --share=network
  - --share=ipc
  - --socket=x11
  - --socket=wayland
  - --filesystem=home
modules:
  - name: etsytrackr
    buildsystem: simple
    build-commands:
      - install -D etsytrackr /app/bin/etsytrackr
      - install -D com.go2engle.EtsyTrackr.desktop /app/share/applications/com.go2engle.EtsyTrackr.desktop
      - install -D com.go2engle.EtsyTrackr.metainfo.xml /app/share/metainfo/com.go2engle.EtsyTrackr.metainfo.xml
      - install -D icon.png /app/share/icons/hicolor/256x256/apps/com.go2engle.EtsyTrackr.png
    sources:
      - type: file
        path: ../dist/onefile/etsytrackr
      - type: file
        path: com.go2engle.EtsyTrackr.desktop
      - type: file
        path: com.go2engle.EtsyTrackr.metainfo.xml
      - type: file
        path: icon.png'''
    
    desktop_content = '''[Desktop Entry]
Name=EtsyTrackr
Comment=Track and manage your Etsy shop sales and inventory
Exec=etsytrackr
Icon=com.go2engle.EtsyTrackr
Terminal=false
Type=Application
Categories=Office;Finance;
Keywords=etsy;shop;tracking;inventory;'''
    
    metainfo_content = '''<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.go2engle.EtsyTrackr</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>MIT</project_license>
  <name>EtsyTrackr</name>
  <summary>Track and manage your Etsy shop sales and inventory</summary>
  <description>
    <p>
      EtsyTrackr is a desktop application that helps Etsy shop owners track and manage their sales and inventory.
      It provides an easy-to-use interface for monitoring shop performance and managing products.
    </p>
  </description>
  <launchable type="desktop-id">com.go2engle.EtsyTrackr.desktop</launchable>
  <url type="homepage">https://github.com/go2engle/EtsyTrackr</url>
  <developer_name>go2engle</developer_name>
  <content_rating type="oars-1.1" />
  <releases>
    <release version="1.0.0" date="2025-01-30">
      <description>
        <p>Initial release of EtsyTrackr</p>
      </description>
    </release>
  </releases>
</component>'''
    
    # Write the files
    (flatpak_dir / 'com.go2engle.EtsyTrackr.yml').write_text(manifest_content)
    (flatpak_dir / 'com.go2engle.EtsyTrackr.desktop').write_text(desktop_content)
    (flatpak_dir / 'com.go2engle.EtsyTrackr.metainfo.xml').write_text(metainfo_content)
    
    # Create properly sized icon from assets
    create_flatpak_icon()
    
    # Build Flatpak
    subprocess.run([
        'flatpak-builder',
        '--repo=repo',
        '--force-clean',
        'build-dir',
        'com.go2engle.EtsyTrackr.yml'
    ], cwd=flatpak_dir, check=True)
    
    # Create Flatpak bundle
    subprocess.run([
        'flatpak',
        'build-bundle',
        'repo',
        '../dist/flatpak/etsytrackr.flatpak',
        'com.go2engle.EtsyTrackr'
    ], cwd=flatpak_dir, check=True)
    
    # Clean up build files
    shutil.rmtree(flatpak_dir / 'build-dir', ignore_errors=True)
    shutil.rmtree(flatpak_dir / 'repo', ignore_errors=True)

if __name__ == '__main__':
    build_flatpak()
