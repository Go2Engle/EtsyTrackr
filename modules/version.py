import requests
from packaging import version
import webbrowser

class VersionChecker:
    GITHUB_API_URL = "https://api.github.com/repos/go2engle/EtsyTrackr/releases/latest"
    GITHUB_RELEASES_URL = "https://github.com/go2engle/EtsyTrackr/releases/latest"
    CURRENT_VERSION = "v0.1.0"  # This should match your current version

    @classmethod
    def check_for_updates(cls):
        """Check if there's a newer version available
        Returns:
            tuple: (bool, str) - (update_available, latest_version)
        """
        try:
            response = requests.get(cls.GITHUB_API_URL, timeout=5)
            if response.status_code == 200:
                latest_version = response.json()['tag_name']  # Already includes 'v' prefix
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
