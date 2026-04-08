"""
Wayland text injection using wtype
Layout-aware keyboard input for Wayland compositors
"""

import subprocess


class WaylandTextInjector:
    """Handles text injection on Wayland using wtype"""

    def __init__(self, key_delay_ms: int = 12):
        self.key_delay = key_delay_ms
        self._available = self._check_wtype()

    def _check_wtype(self) -> bool:
        """Check if wtype is installed"""
        try:
            result = subprocess.run(
                ['which', 'wtype'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def is_available(self) -> bool:
        """Check if Wayland injection via wtype is available"""
        return self._available

    def type_text(self, text: str) -> bool:
        """Type text using wtype"""
        if not self._available:
            return False
        try:
            result = subprocess.run(
                ['wtype', '-d', str(self.key_delay), text],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
