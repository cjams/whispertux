"""
Text injector for WhisperTux
Handles injecting transcribed text into other applications using ydotool
"""

import subprocess
import time
import pyperclip
import os
from pathlib import Path
from typing import Optional


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

        # Check if ydotool is available
        self.ydotool_available = self._check_ydotool()
        self.ydotool_socket = self._detect_ydotool_socket()

        if not self.ydotool_available:
            print("⚠️  ydotool not found - text injection will use clipboard fallback")
        elif self.ydotool_socket:
            print(f"Using ydotool socket: {self.ydotool_socket}")

    def _check_ydotool(self) -> bool:
        """Check if ydotool is available on the atiystem"""
        try:
            result = subprocess.run(['which', 'ydotool'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0


        except:
            return False

    def _detect_ydotool_socket(self) -> Optional[str]:
        """Find the ydotoold socket used by common package/service setups."""
        candidates = []

        configured_socket = os.environ.get('YDOTOOL_SOCKET')
        if configured_socket:
            candidates.append(configured_socket)

        runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
        if runtime_dir:
            candidates.append(str(Path(runtime_dir) / '.ydotool_socket'))

        candidates.append('/tmp/.ydotool_socket')

        for socket_path in candidates:
            if socket_path and Path(socket_path).exists():
                return socket_path

        return None

    def _get_ydotool_env(self) -> dict:
        """Build an environment that points ydotool at the detected daemon socket."""
        env = os.environ.copy()
        if self.ydotool_socket and not env.get('YDOTOOL_SOCKET'):
            env['YDOTOOL_SOCKET'] = self.ydotool_socket
        return env

    def _log_ydotool_failure(self, result: subprocess.CompletedProcess):
        """Log enough detail to diagnose ydotool daemon/socket failures."""
        print(f"ERROR: ydotool failed with exit code {result.returncode}")

        stdout = (result.stdout or '').strip()
        stderr = (result.stderr or '').strip()
        if stdout:
            print(f"ydotool stdout: {stdout}")
        if stderr:
            print(f"ydotool stderr: {stderr}")
        if not stdout and not stderr:
            print("ydotool did not print any error output")

        socket_path = self.ydotool_socket or os.environ.get('YDOTOOL_SOCKET')
        if socket_path:
            socket_file = Path(socket_path)
            print(f"ydotool socket: {socket_path}")
            if socket_file.exists():
                socket_readable = os.access(socket_path, os.R_OK)
                socket_writable = os.access(socket_path, os.W_OK)
                print(f"ydotool socket readable={socket_readable} writable={socket_writable}")
                if not socket_readable or not socket_writable:
                    print("ydotool socket is not accessible by the current user.")
                    print("Run: ./scripts/setup-ydotoold-service.sh")
            else:
                print("ydotool socket does not exist")

    def inject_text(self, text: str) -> bool:
        """
        Inject text into the currently focused application

        Args:
            text: Text to inject

        Returns:
            True if successful, False otherwise
        """
        if not text or text.strip() == "":
            print("No text to inject (empty or whitespace)")
            return True

        # Preprocess the text to handle unwanted carriage returns and speech-to-text corrections
        processed_text = self._preprocess_text(text)
        
        try:
            # Try ydotool first if available
            if self.ydotool_available:
                return self._inject_via_ydotool(processed_text)
            else:
                # Fall back to clipboard method
                return self._inject_via_clipboard(processed_text)

        except Exception as e:
            print(f"Primary injection method failed: {e}")

            # Try clipboard fallback if ydotool failed
            if self.ydotool_available and self.use_clipboard_fallback:
                print("Falling back to clipboard method...")
                try:
                    return self._inject_via_clipboard(processed_text)
                except Exception as e2:
                    print(f"Clipboard fallback also failed: {e2}")

            return False

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text to handle common speech-to-text corrections and remove unwanted line breaks
        """
        import re
        
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
        import re
        
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
        """Inject text using ydotool with configurable --key-delay and raw text (no escaping)"""
        try:
            cmd = ['ydotool', 'type', '--key-delay', str(self.key_delay), text]
            
            print(f"Injecting text with ydotool: ydotool type --key-delay {self.key_delay} [text]")

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                env=self._get_ydotool_env()
            )

            if result.returncode == 0:
                return True
            else:
                self._log_ydotool_failure(result)
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

            # Paste using ydotool Ctrl+V (if ydotool is available)
            if self.ydotool_available:
                # Use ydotool to send Ctrl+V
                result = subprocess.run(
                    ['ydotool', 'key', '29:1', '47:1', '47:0', '29:0'],
                    capture_output=True,
                    timeout=5,
                    env=self._get_ydotool_env()
                )

                if result.returncode != 0:
                    self._log_ydotool_failure(result)
            else:
                print("No method available to send paste command")
                print("   Text has been copied to clipboard - paste manually with Ctrl+V")

            # Restore original clipboard after a delay
            def restore_clipboard():
                time.sleep(2.0)  # Wait 2 seconds before restoring
                try:
                    pyperclip.copy(original_clipboard)
                except:
                    pass  # Ignore restore errors

            # Run restore in a separate thread so it doesn't block
            import threading
            restore_thread = threading.Thread(target=restore_clipboard, daemon=True)
            restore_thread.start()

            print("Text copied to clipboard and paste command sent")
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
            'ydotool_available': self.ydotool_available,
            'key_delay': self.key_delay,
            'use_clipboard_fallback': self.use_clipboard_fallback
        }
