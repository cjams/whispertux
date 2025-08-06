"""
Text injector for WhisperTux
Handles injecting transcribed text into other applications using ydotool
"""

import subprocess
import time
import pyperclip
from typing import Optional


class TextInjector:
    """Handles injecting text into focused applications"""

    def __init__(self, config_manager=None):
        # Configuration
        self.config_manager = config_manager

        # Initialize settings from config if available
        if self.config_manager:
            self.typing_speed = self.config_manager.get_setting('typing_speed', 150)
            self.use_clipboard_fallback = self.config_manager.get_setting('use_clipboard', False)
        else:
            self.typing_speed = 150  # Default WPM
            self.use_clipboard_fallback = False

        # Check if ydotool is available
        self.ydotool_available = self._check_ydotool()

        if not self.ydotool_available:
            print("⚠️  ydotool not found - text injection will use clipboard fallback")

    def _check_ydotool(self) -> bool:
        """Check if ydotool is available on the system"""
        try:
            result = subprocess.run(['which', 'ydotool'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False

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

        # Preprocess the text to handle common speech-to-text corrections
        processed_text = self._preprocess_text(text)

        print(f"Injecting text: '{processed_text}'")

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
        Preprocess text to handle common speech-to-text corrections
        """
        # Handle common speech-to-text corrections
        processed = text

        # Punctuation commands
        replacements = {
            r'\bperiod\b': '.',
            r'\bcomma\b': ',',
            r'\bquestion mark\b': '?',
            r'\bexclamation mark\b': '!',
            r'\bcolon\b': ':',
            r'\bsemicolon\b': ';',
            r'\bnew line\b': '\n',
            r'\btab\b': '\t',
            r'\bdash\b': '-',
            r'\bunderscore\b': '_',
            r'\bopen paren\b': '(',
            r'\bclose paren\b': ')',
            r'\bopen bracket\b': '[',
            r'\bclose bracket\b': ']',
            r'\bopen brace\b': '{',
            r'\bclose brace\b': '}',
            r'\bspace\b': ' ',
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

        import re
        for pattern, replacement in replacements.items():
            processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        # Clean up extra spaces
        processed = re.sub(r'\s+', ' ', processed).strip()

        return processed

    def _inject_via_ydotool(self, text: str) -> bool:
        """Inject text using ydotool"""
        try:
            # Escape text for shell command - handle single quotes properly
            escaped_text = text.replace("'", "'\"'\"'")

            # Use -- to separate options from text (handles text starting with dashes)
            cmd = ['ydotool', 'type', '--', escaped_text]

            print(f"Running ydotool command: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✓ ydotool injection successful")
                return True
            else:
                print(f"✗ ydotool failed with return code {result.returncode}")
                print(f"stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("✗ ydotool command timed out")
            return False
        except Exception as e:
            print(f"✗ ydotool injection failed: {e}")
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
                    timeout=5
                )

                if result.returncode != 0:
                    print(f"⚠️  ydotool paste command failed: {result.stderr}")
            else:
                print("⚠️  No method available to send paste command")
                print("    Text has been copied to clipboard - paste manually with Ctrl+V")

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

            print("✓ Text copied to clipboard and paste command sent")
            return True

        except Exception as e:
            print(f"✗ Clipboard injection failed: {e}")
            return False

    def set_typing_speed(self, wpm: int):
        """Set the typing speed in words per minute (10-200 WPM)"""
        self.typing_speed = max(10, min(200, wpm))
        print(f"Typing speed set to {self.typing_speed} WPM")

    def set_use_clipboard_fallback(self, use_clipboard: bool):
        """Enable or disable clipboard fallback"""
        self.use_clipboard_fallback = use_clipboard
        print(f"Clipboard fallback {'enabled' if use_clipboard else 'disabled'}")

    def test_injection(self) -> bool:
        """Test text injection with a simple test string"""
        test_text = "WhisperTux test injection"
        print(f"Testing text injection with: '{test_text}'")
        return self.inject_text(test_text)

    def get_status(self) -> dict:
        """Get the status of the text injector"""
        return {
            'ydotool_available': self.ydotool_available,
            'typing_speed': self.typing_speed,
            'use_clipboard_fallback': self.use_clipboard_fallback
        }
