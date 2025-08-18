"""
Text injector for WhisperTux
Handles injecting transcribed text into other applications using ydotool
"""

import os
import shutil
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
            # Optional knobs (safe if missing)
            self.inject_strategy = self.config_manager.get_setting('inject_strategy', 'type')  # 'type' or 'paste'
            self.clipboard_clear_delay = self.config_manager.get_setting('clipboard_clear_delay', 2.0)  # seconds
        else:
            self.typing_speed = 150  # Default WPM/CPM (see _compute_key_delay_ms)
            self.use_clipboard_fallback = False
            self.inject_strategy = 'type'
            self.clipboard_clear_delay = 2.0  # Default 2 seconds

        # Validate clipboard clear delay
        self.clipboard_clear_delay = self._validate_clipboard_clear_delay(self.clipboard_clear_delay)

        # Detect available injectors
        self.ydotool_available = self._check_ydotool()

        if not self.ydotool_available:
            print("⚠️  No typing backend found (ydotool). Will use clipboard fallback.")

    def _check_ydotool(self) -> bool:
        """Check if ydotool is available on the system"""
        try:
            result = subprocess.run(['which', 'ydotool'], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    # ------------------------ Public API ------------------------

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

        # Preprocess; also trim trailing newlines (avoid unwanted Enter)
        processed_text = self._preprocess_text(text).rstrip("\r\n")

        try:
            # Use strategy-based injection
            if self.inject_strategy == "paste":
                if self.ydotool_available:
                    return self._inject_via_clipboard_and_hotkey(processed_text)
                else:
                    return self._inject_via_clipboard(processed_text)
            else:  # "type" strategy
                if self.ydotool_available:
                    return self._inject_via_ydotool(processed_text)
                else:
                    return self._inject_via_clipboard(processed_text)

        except Exception as e:
            print(f"Primary injection method failed: {e}")

            if self.use_clipboard_fallback:
                print("Falling back to clipboard method...")
                try:
                    return self._inject_via_clipboard(processed_text)
                except Exception as e2:
                    print(f"Clipboard fallback also failed: {e2}")

            return False

    # ------------------------ Helpers ------------------------

    def _compute_key_delay_ms(self) -> int:
        """
        Convert configured typing speed to per-key delay for ydotool.
        If value <= 500, treat as WPM (≈5 chars/word). Otherwise treat as CPM.
        Clamp to [0, 1000] ms and round to int.
        """
        try:
            speed = int(self.typing_speed)
        except Exception:
            speed = 150
        speed = max(10, min(speed, 2000))
        if speed <= 500:
            cpm = speed * 5
        else:
            cpm = speed
        delay = 60000 / max(1, cpm)  # ms per character
        delay = int(round(delay))
        return max(0, min(delay, 1000))

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text to handle common speech-to-text corrections and remove unwanted line breaks
        """
        import re

        # Normalize line breaks to spaces to avoid unintended "Enter"
        processed = text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

        # Apply user-defined overrides first
        processed = self._apply_word_overrides(processed)

        # Built-in speech-to-text replacements
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

        # Collapse runs of whitespace, preserve intentional newlines
        processed = re.sub(r'[ \t]+', ' ', processed)
        processed = re.sub(r' *\n *', '\n', processed)
        processed = processed.strip()

        return processed

    def _apply_word_overrides(self, text: str) -> str:
        """Apply user-defined word overrides to the text"""
        import re

        if not self.config_manager:
            return text

        word_overrides = self.config_manager.get_word_overrides()
        if not word_overrides:
            return text

        processed = text
        for original, replacement in word_overrides.items():
            if original and replacement:
                pattern = r'\b' + re.escape(original) + r'\b'
                processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

        return processed

    # ------------------------ Backends ------------------------

    def _inject_via_ydotool(self, text: str) -> bool:
        """
        Inject using ydotool.
        - For 'paste' strategy: use clipboard then Ctrl+V keystroke (fast).
        - For 'type' strategy: stream text via stdin with --key-delay.
        """
        if self.inject_strategy == "paste":
            return self._inject_via_clipboard_and_hotkey(text)

        try:
            delay = self._compute_key_delay_ms()
            cmd = ['ydotool', 'type', '--key-delay', str(delay), '--file', '-']

            # Respect YDOTOOL_SOCKET; default to $XDG_RUNTIME_DIR/.ydotool_socket
            env = os.environ.copy()
            if "YDOTOOL_SOCKET" not in env:
                xdg = env.get("XDG_RUNTIME_DIR")
                if xdg:
                    env["YDOTOOL_SOCKET"] = os.path.join(xdg, ".ydotool_socket")

            print(f"Injecting text with ydotool: type (delay={delay}ms) via {env.get('YDOTOOL_SOCKET','<default>')}")
            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                text=False,
                timeout=60,
                env=env,
            )

            if result.returncode == 0:
                return True
            else:
                stderr = (result.stderr or b"").decode("utf-8", "ignore")
                print(f"ERROR: ydotool failed: {stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("ERROR: ydotool command timed out")
            return False
        except Exception as e:
            print(f"ERROR: ydotool injection failed: {e}")
            return False

    # ------------------------ Clipboard paths ------------------------

    def _inject_via_clipboard_and_hotkey(self, text: str) -> bool:
        """Fast path: copy to clipboard, then press Ctrl+V via ydotool."""
        try:
            # 1) Set clipboard (prefer wl-copy on Wayland)
            if shutil.which("wl-copy"):
                subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
            else:
                pyperclip.copy(text)

            time.sleep(0.12)  # settle so the target app sees the new clipboard

            # 2) Press Ctrl+V
            if self.ydotool_available:
                # Linux evdev codes: 29 = LeftCtrl, 47 = 'V'
                result = subprocess.run(['ydotool', 'key', '29:1', '47:1', '47:0', '29:0'], capture_output=True, timeout=5)
                if result.returncode != 0:
                    stderr = (result.stderr or b"").decode("utf-8", "ignore")
                    print(f"  ydotool paste command failed: {stderr}")
                    return False
                return True

            print("No key-injection tool available; text is on the clipboard.")
            return True

        except Exception as e:
            print(f"Clipboard+hotkey injection failed: {e}")
            return False

        finally:
            # Clear clipboard after specified delay (non-blocking)
            self._schedule_clipboard_clear()

    def _inject_via_clipboard(self, text: str) -> bool:
        """Copy text to clipboard and (optionally) send paste; restore previous clipboard later."""
        try:
            # Save current clipboard content
            try:
                original_clipboard = pyperclip.paste()
            except Exception:
                original_clipboard = ""

            # Set new clipboard content
            if shutil.which("wl-copy"):
                subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
            else:
                pyperclip.copy(text)

            # Optional: auto-paste if ydotool present
            pasted = False
            if self.ydotool_available:
                r = subprocess.run(['ydotool', 'key', '29:1', '47:1', '47:0', '29:0'], capture_output=True, timeout=5)
                pasted = (r.returncode == 0)

            # Restore original clipboard after a delay (non-blocking)
            def restore_clipboard():
                time.sleep(2.0)
                try:
                    if shutil.which("wl-copy"):
                        subprocess.run(["wl-copy"], input=original_clipboard.encode("utf-8"), check=True)
                    else:
                        pyperclip.copy(original_clipboard)
                except Exception:
                    pass  # Ignore restore errors

            import threading
            threading.Thread(target=restore_clipboard, daemon=True).start()

            print("Text copied to clipboard" + (" and paste command sent" if pasted else ""))
            return True

        except Exception as e:
            print(f"ERROR: Clipboard injection failed: {e}")
            return False

        finally:
            # Clear clipboard after specified delay (non-blocking)
            self._schedule_clipboard_clear()

    def _schedule_clipboard_clear(self):
        """Schedule clipboard clearing after the configured delay"""
        def clear_clipboard():
            time.sleep(self.clipboard_clear_delay)
            try:
                if shutil.which("wl-copy"):
                    subprocess.run(["wl-copy"], input=b"", check=True)
                else:
                    pyperclip.copy("")
                print(f"Clipboard cleared after {self.clipboard_clear_delay}s delay")
            except Exception as e:
                print(f"Failed to clear clipboard: {e}")

        import threading
        threading.Thread(target=clear_clipboard, daemon=True).start()

    def _validate_clipboard_clear_delay(self, delay: float) -> float:
        """Validate and clamp clipboard clear delay to reasonable bounds"""
        try:
            delay = float(delay)
        except (ValueError, TypeError):
            delay = 2.0
        
        # Clamp between 100ms and 5 seconds
        delay = max(0.1, min(delay, 5.0))
        return delay

    # ------------------------ Settings API ------------------------

    def set_typing_speed(self, cpm: int):
        """Applies the typing speed CPM (or WPM if <= 500; see _compute_key_delay_ms)"""
        self.typing_speed = cpm
        print(f"Typing speed set to {self.typing_speed}")

    def validate_typing_speed(self, cpm: int):
        """Validates a desired CPM value and returns a clamped value"""
        max_speed = 2000
        min_speed = 10
        return max(min_speed, min(cpm, max_speed))

    def set_use_clipboard_fallback(self, use_clipboard: bool):
        """Enable or disable clipboard fallback"""
        self.use_clipboard_fallback = use_clipboard
        print(f"Clipboard fallback {'enabled' if use_clipboard else 'disabled'}")

    def set_clipboard_clear_delay(self, delay_seconds: float):
        """Set the clipboard clear delay in seconds (0.1 to 5.0)"""
        self.clipboard_clear_delay = self._validate_clipboard_clear_delay(delay_seconds)
        print(f"Clipboard clear delay set to {self.clipboard_clear_delay}s")

    def get_status(self) -> dict:
        """Get the status of the text injector"""
        return {
            'ydotool_available': self.ydotool_available,
            'typing_speed': self.typing_speed,
            'use_clipboard_fallback': self.use_clipboard_fallback,
            'inject_strategy': self.inject_strategy,
            'clipboard_clear_delay': self.clipboard_clear_delay,
        }

