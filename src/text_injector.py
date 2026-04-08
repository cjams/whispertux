"""
Text injector for WhisperTux
Handles injecting transcribed text into other applications
"""

import subprocess
import time
import os
import threading
import re
import pyperclip


class TextInjector:
    """Handles injecting text into focused applications"""

    def __init__(self, config_manager=None):
        # Configuration
        self.config_manager = config_manager

        # Initialize settings from config if available
        if self.config_manager:
            self.key_delay = self.config_manager.get_setting('key_delay', 15)
            self.use_clipboard_fallback = self.config_manager.get_setting('use_clipboard', False)
        else:
            self.key_delay = 15  # Default key delay in milliseconds
            self.use_clipboard_fallback = False

        # Detect display server and initialize injectors
        self.display_server = self._detect_display_server()
        self.x11_injector = None
        self.wayland_injector = None

        # Check if ydotool is available
        self.ydotool_available = self._check_ydotool()

        self._init_injectors()

    def _detect_display_server(self) -> str:
        """Detect the current display server (x11 or wayland)"""
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type in ('x11', 'wayland'):
            return session_type
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        if os.environ.get('DISPLAY'):
            return 'x11'
        return 'unknown'

    def _check_ydotool(self) -> bool:
        """Check if ydotool is available on the system"""
        try:
            result = subprocess.run(['which', 'ydotool'],
                                    capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def _init_injectors(self):
        """Initialize the appropriate injector for the display server"""
        if self.display_server == 'x11':
            try:
                from .text_injector_x11 import X11TextInjector
            except ImportError:
                from text_injector_x11 import X11TextInjector
            self.x11_injector = X11TextInjector(self.key_delay)

            if self.x11_injector.is_available():
                print("Text injection: X11 XTest (layout-aware)")
            elif self.ydotool_available:
                print("Text injection: ydotool (layout issues possible)")
            else:
                print("Text injection: clipboard fallback")

        elif self.display_server == 'wayland':
            try:
                from .text_injector_wayland import WaylandTextInjector
            except ImportError:
                from text_injector_wayland import WaylandTextInjector
            self.wayland_injector = WaylandTextInjector(self.key_delay)

            if self.wayland_injector.is_available():
                print("Text injection: wtype (layout-aware)")
            elif self.ydotool_available:
                print("Text injection: ydotool (layout issues possible)")
                print("  Tip: install wtype for proper layout support")
            else:
                print("Text injection: clipboard fallback")
        else:
            if self.ydotool_available:
                print("Text injection: ydotool")
            else:
                print("Text injection: clipboard fallback")

    def _get_injector_method(self):
        """Get the best available injection method. Returns (method, name) or (None, None)"""
        if self.display_server == 'x11' and self.x11_injector and self.x11_injector.is_available():
            return (self.x11_injector.type_text, 'X11')
        if self.display_server == 'wayland' and self.wayland_injector and self.wayland_injector.is_available():
            return (self.wayland_injector.type_text, 'wtype')
        if self.ydotool_available:
            return (self._inject_via_ydotool, 'ydotool')
        return (None, None)

    def inject_text(self, text: str) -> bool:
        """
        Inject text into the currently focused application

        Args:
            text: Text to inject

        Returns:
            True if successful, False otherwise
        """
        if not text or text.strip() == "":
            return True

        # Preprocess the text to handle unwanted carriage returns and speech-to-text corrections
        processed = self._preprocess_text(text)

        method, name = self._get_injector_method()

        # No primary method available - use clipboard automatically
        if method is None:
            return self._inject_via_clipboard(processed)

        # Try primary method
        try:
            if method(processed):
                return True
        except Exception as e:
            print(f"Injection via {name} failed: {e}")

        # Primary method failed - use clipboard only if fallback enabled
        if self.use_clipboard_fallback:
            print("Falling back to clipboard method...")
            return self._inject_via_clipboard(processed)

        return False

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text to handle common speech-to-text corrections and remove unwanted line breaks
        """
        # First, convert unwanted carriage returns and newlines to spaces
        # This prevents accidental "Enter" key presses in applications
        processed = text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

        # Apply user-defined word overrides first (before built-in corrections)
        processed = self._apply_word_overrides(processed)

        # Handle common speech-to-text corrections
        replacements = {
            r'\bperiod\b': '.',
            r'\bcomma\b': ',',
            r'\bquestion mark\b': '?',
            r'\bexclamation mark\b': '!',
            r'\bcolon\b': ':',
            r'\bsemicolon\b': ';',
            r'\btux enter\b': '\n',     # Special phrase for new line
            r'\btab\b': '\t',
            r'\bdash\b': '-',
            r'\bunderscore\b': '_',
            r'\bopen paren\b': '(',
            r'\bclose paren\b': ')',
            r'\bopen bracket\b': '[',
            r'\bclose bracket\b': ']',
            r'\bopen brace\b': '{',
            r'\bclose brace\b': '}',
            r'\bat symbol\b': '@',
            r'\bhash\b': '#',
            r'\bdollar sign\b': '$',
            r'\bpercent\b': '%',
            r'\bcaret\b': '^',
            r'\bampersand\b': '&',
            r'\basterisk\b': '*',
            r'\bplus\b': '+',
            r'\bequals\b': '=',
            r'\bless than\b': '<',
            r'\bgreater than\b': '>',
            r'\bslash\b': '/',
            r'\bbackslash\b': r'\\',
            r'\bpipe\b': '|',
            r'\btilde\b': '~',
            r'\bgrave\b': '`',
            r'\bquote\b': '"',
            r'\bapostrophe\b': "'",
        }

        for pattern, replacement in replacements.items():
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Clean up extra spaces but preserve intentional newlines
        processed = re.sub(r'[ \t]+', ' ', processed)  # Multiple spaces/tabs to single space
        processed = re.sub(r' *\n *', '\n', processed)  # Clean spaces around newlines
        processed = processed.strip()

        return processed

    def _apply_word_overrides(self, text: str) -> str:
        """
        Apply user-defined word overrides to the text
        """
        if not self.config_manager:
            return text

        # Get word overrides from configuration
        word_overrides = self.config_manager.get_word_overrides()

        if not word_overrides:
            return text

        processed = text

        # Apply each override using word boundary matching for accuracy
        for original, replacement in word_overrides.items():
            if original and replacement:
                # Use word boundaries to match whole words only
                # This prevents partial word replacements
                pattern = r'\b' + re.escape(original) + r'\b'
                processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        return processed

    def _inject_via_ydotool(self, text: str) -> bool:
        """Inject text using ydotool with configurable --key-delay"""
        try:
            cmd = ['ydotool', 'type', '--key-delay', str(self.key_delay), text]

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True
            else:
                print(f"ERROR: ydotool failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("ERROR: ydotool command timed out")
            return False
        except Exception as e:
            print(f"ERROR: ydotool injection failed: {e}")
            return False

    def _inject_via_clipboard(self, text: str) -> bool:
        """Inject text using clipboard + paste key combination"""
        try:
            # Save current clipboard content
            try:
                original_clipboard = pyperclip.paste()
            except:
                original_clipboard = ""

            # Set new clipboard content
            pyperclip.copy(text)

            # Small delay to ensure clipboard is set
            time.sleep(0.1)

            # Send paste keystroke using available method
            paste_sent = False
            if self.x11_injector and self.x11_injector.is_available():
                # Use X11 to send Ctrl+V
                paste_sent = self.x11_injector.send_ctrl_v()
            elif self.ydotool_available:
                # Use ydotool to send Ctrl+V
                result = subprocess.run(
                    ['ydotool', 'key', '29:1', '47:1', '47:0', '29:0'],
                    capture_output=True,
                    timeout=5
                )
                paste_sent = result.returncode == 0
                if not paste_sent:
                    print(f"ydotool paste command failed: {result.stderr}")

            if not paste_sent:
                print("Text copied to clipboard - paste manually with Ctrl+V")

            # Restore original clipboard after a delay
            def restore_clipboard():
                time.sleep(2.0)  # Wait 2 seconds before restoring
                try:
                    pyperclip.copy(original_clipboard)
                except:
                    pass  # Ignore restore errors

            # Run restore in a separate thread so it doesn't block
            threading.Thread(target=restore_clipboard, daemon=True).start()

            return True

        except Exception as e:
            print(f"ERROR: Clipboard injection failed: {e}")
            return False

    def set_use_clipboard_fallback(self, use_clipboard: bool):
        """Enable or disable clipboard fallback"""
        self.use_clipboard_fallback = use_clipboard
        print(f"Clipboard fallback {'enabled' if use_clipboard else 'disabled'}")

    def get_status(self) -> dict:
        """Get the status of the text injector"""
        return {
            'display_server': self.display_server,
            'x11_available': self.x11_injector.is_available() if self.x11_injector else False,
            'wayland_available': self.wayland_injector.is_available() if self.wayland_injector else False,
            'ydotool_available': self.ydotool_available,
            'key_delay': self.key_delay,
            'use_clipboard_fallback': self.use_clipboard_fallback
        }
