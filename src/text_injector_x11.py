"""
X11 text injection using XTest extension
Layout-aware via XKeysymToKeycode
"""

import time
import ctypes
from ctypes import c_int, c_uint, c_ulong, c_char_p, c_bool, POINTER


class X11TextInjector:
    """Handles text injection on X11 using XTest extension"""

    XK_Shift_L = 0xffe1
    XK_Control_L = 0xffe3
    XK_Return = 0xff0d
    XK_Tab = 0xff09

    def __init__(self, key_delay_ms: int = 12):
        self.key_delay = key_delay_ms / 1000.0
        self.X11 = None
        self.Xtst = None
        self._initialized = False
        self._init_x11()

    def _init_x11(self):
        """Initialize X11 and XTest libraries via ctypes"""
        try:
            self.X11 = ctypes.CDLL("libX11.so.6")
            self.Xtst = ctypes.CDLL("libXtst.so.6")

            self.X11.XOpenDisplay.restype = POINTER(c_ulong)
            self.X11.XOpenDisplay.argtypes = [c_char_p]
            self.X11.XCloseDisplay.argtypes = [POINTER(c_ulong)]
            self.X11.XKeysymToKeycode.restype = c_int
            self.X11.XKeysymToKeycode.argtypes = [POINTER(c_ulong), c_ulong]
            self.X11.XFlush.argtypes = [POINTER(c_ulong)]
            self.X11.XSync.argtypes = [POINTER(c_ulong), c_bool]

            self.Xtst.XTestFakeKeyEvent.argtypes = [POINTER(c_ulong), c_uint, c_bool, c_ulong]
            self.Xtst.XTestFakeKeyEvent.restype = c_int

            self._initialized = True
        except OSError:
            pass

    def is_available(self) -> bool:
        """Check if X11 injection is available"""
        if not self._initialized:
            return False
        display = self.X11.XOpenDisplay(None)
        if display:
            self.X11.XCloseDisplay(display)
            return True
        return False

    def _char_to_keysym(self, char: str) -> tuple:
        """Convert character to X11 keysym. Returns (keysym, needs_shift)"""
        if len(char) != 1:
            return (0, False)

        if char == '\n':
            return (self.XK_Return, False)
        if char == '\t':
            return (self.XK_Tab, False)

        code = ord(char)
        needs_shift = char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?'
        return (code, needs_shift)

    def type_text(self, text: str) -> bool:
        """Type text using XTest fake key events"""
        if not self._initialized:
            return False

        display = self.X11.XOpenDisplay(None)
        if not display:
            return False

        try:
            shift_keycode = self.X11.XKeysymToKeycode(display, self.XK_Shift_L)

            for char in text:
                keysym, needs_shift = self._char_to_keysym(char)
                if keysym == 0:
                    continue

                keycode = self.X11.XKeysymToKeycode(display, keysym)
                if keycode == 0 and char.isupper():
                    keycode = self.X11.XKeysymToKeycode(display, ord(char.lower()))
                    needs_shift = True
                if keycode == 0:
                    continue

                if needs_shift:
                    self.Xtst.XTestFakeKeyEvent(display, shift_keycode, True, 0)

                self.Xtst.XTestFakeKeyEvent(display, keycode, True, 0)
                self.Xtst.XTestFakeKeyEvent(display, keycode, False, 0)

                if needs_shift:
                    self.Xtst.XTestFakeKeyEvent(display, shift_keycode, False, 0)

                self.X11.XFlush(display)

                if self.key_delay > 0:
                    time.sleep(self.key_delay)

            self.X11.XSync(display, False)
            return True
        except Exception:
            return False
        finally:
            self.X11.XCloseDisplay(display)

    def send_ctrl_v(self) -> bool:
        """Send Ctrl+V keystroke"""
        if not self._initialized:
            return False

        display = self.X11.XOpenDisplay(None)
        if not display:
            return False

        try:
            ctrl = self.X11.XKeysymToKeycode(display, self.XK_Control_L)
            v = self.X11.XKeysymToKeycode(display, ord('v'))

            self.Xtst.XTestFakeKeyEvent(display, ctrl, True, 0)
            self.Xtst.XTestFakeKeyEvent(display, v, True, 0)
            self.Xtst.XTestFakeKeyEvent(display, v, False, 0)
            self.Xtst.XTestFakeKeyEvent(display, ctrl, False, 0)
            self.X11.XFlush(display)
            return True
        except Exception:
            return False
        finally:
            self.X11.XCloseDisplay(display)
