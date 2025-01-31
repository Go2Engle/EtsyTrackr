#!/usr/bin/env python3
import re
import os
import sys
import datetime
from pathlib import Path

def update_version_file(version):
    """Update version in modules/version.py"""
    version_file = Path('modules/version.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update version string
    content = re.sub(
        r'CURRENT_VERSION = "v[0-9]+\.[0-9]+\.[0-9]+"',
        f'CURRENT_VERSION = "v{version}"',
        content
    )
    
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(content)

def update_installer(version):
    """Update version in installer.iss"""
    installer_file = Path('installer.iss')
    with open(installer_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update version string
    content = re.sub(
        r'#define MyAppVersion "[0-9]+\.[0-9]+\.[0-9]+"',
        f'#define MyAppVersion "{version}"',
        content
    )
    
    with open(installer_file, 'w', encoding='utf-8') as f:
        f.write(content)

def update_flatpak_metadata(version):
    """Update version in Flatpak metadata files"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Update metainfo in build_flatpak.py
    flatpak_build = Path('build_flatpak.py')
    with open(flatpak_build, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update version and date in release tag
    content = re.sub(
        r'<release version="[0-9]+\.[0-9]+\.[0-9]+" date="[0-9]{4}-[0-9]{2}-[0-9]{2}">',
        f'<release version="{version}" date="{today}">',
        content
    )
    
    with open(flatpak_build, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Update standalone metainfo file if it exists
    metainfo_file = Path('flatpak/com.go2engle.EtsyTrackr.metainfo.xml')
    if metainfo_file.exists():
        with open(metainfo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(
            r'<release version="[0-9]+\.[0-9]+\.[0-9]+" date="[0-9]{4}-[0-9]{2}-[0-9]{2}">',
            f'<release version="{version}" date="{today}">',
            content
        )
        
        with open(metainfo_file, 'w', encoding='utf-8') as f:
            f.write(content)

def validate_version(version):
    """Validate version string format"""
    if not re.match(r'^[0-9]+\.[0-9]+\.[0-9]+$', version):
        print("Error: Version must be in format X.Y.Z (e.g., 1.0.0)")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python bump.py VERSION")
        print("Example: python bump.py 1.0.0")
        sys.exit(1)
    
    version = sys.argv[1]
    validate_version(version)
    
    # Update all version references
    update_version_file(version)
    update_installer(version)
    update_flatpak_metadata(version)
    
    print(f"Successfully updated version to {version} in all files!")
    print("\nFiles updated:")
    print("- modules/version.py")
    print("- installer.iss")
    print("- build_flatpak.py")
    if Path('flatpak/com.go2engle.EtsyTrackr.metainfo.xml').exists():
        print("- flatpak/com.go2engle.EtsyTrackr.metainfo.xml")
    
    print("\nNext steps:")
    print("1. Review the changes")
    print("2. Commit the changes")
    print(f"3. Create a new tag: git tag v{version}")
    print("4. Push changes and tag: git push && git push --tags")

if __name__ == '__main__':
    main()
