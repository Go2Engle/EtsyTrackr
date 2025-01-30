import requests
from packaging import version
import webbrowser
import sys

class VersionChecker:
    GITHUB_API_URL = "https://api.github.com/repos/go2engle/EtsyTrackr/releases/latest"
    GITHUB_RELEASES_URL = "https://github.com/go2engle/EtsyTrackr/releases/latest"
    CURRENT_VERSION = "v0.7.3"  # This should match your current version

    @classmethod
    def check_for_updates(cls):
        """Check if there's a newer version available and verify installer exists
        Returns:
            tuple: (bool, str) - (update_available, latest_version)
        """
        try:
            response = requests.get(cls.GITHUB_API_URL, timeout=5)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name']  # Already includes 'v' prefix
                
                # Check for platform-specific installer in assets
                if sys.platform.startswith('linux'):
                    installer_name = "EtsyTrackr-x86_64.AppImage"
                elif sys.platform == 'darwin':
                    installer_name = "EtsyTrackr.dmg"  # macOS disk image
                else:
                    installer_name = "EtsyTrackr_Setup.exe"  # Windows installer
                
                installer_exists = any(
                    asset['name'] == installer_name 
                    for asset in release_data.get('assets', [])
                )
                
                if not installer_exists:
                    return False, cls.CURRENT_VERSION
                
                # Remove 'v' prefix for version comparison
                current = version.parse(cls.CURRENT_VERSION.lstrip('v'))
                latest = version.parse(latest_version.lstrip('v'))
                return latest > current, latest_version
        except Exception:
            # If there's any error (no internet, timeout, etc.), assume no update
            pass
        return False, cls.CURRENT_VERSION

    @classmethod
    def open_releases_page(cls):
        """Open the GitHub releases page in the default browser"""
        webbrowser.open(cls.GITHUB_RELEASES_URL)
