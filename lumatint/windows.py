"""Windows-only gamma ramp and user-approved startup integration."""

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_VALUE = "LumaTint"


class DisplayError(RuntimeError):
    pass


class WindowsGamma:
    """Capture and restore original gamma for the primary display."""

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise DisplayError("LumaTint's display controls require Windows 10 or 11.")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        self.user32.GetDC.argtypes = [wintypes.HWND]
        self.user32.GetDC.restype = wintypes.HDC
        self.user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        self.user32.ReleaseDC.restype = ctypes.c_int
        self.gdi32.GetDeviceGammaRamp.argtypes = [wintypes.HDC, ctypes.c_void_p]
        self.gdi32.GetDeviceGammaRamp.restype = wintypes.BOOL
        self.gdi32.SetDeviceGammaRamp.argtypes = [wintypes.HDC, ctypes.c_void_p]
        self.gdi32.SetDeviceGammaRamp.restype = wintypes.BOOL
        self.original = self._read()
        self.changed = False

    def _with_dc(self, func, ramp):
        dc = self.user32.GetDC(None)
        if not dc:
            raise DisplayError("Could not access the primary display.")
        try:
            return bool(func(dc, ctypes.byref(ramp)))
        finally:
            self.user32.ReleaseDC(None, dc)

    def _read(self) -> list[list[int]]:
        arr = ((ctypes.c_ushort * 256) * 3)()
        if not self._with_dc(self.gdi32.GetDeviceGammaRamp, arr):
            raise DisplayError("The display driver does not support reading gamma settings.")
        return [[int(arr[c][i]) for i in range(256)] for c in range(3)]

    def _write(self, ramp: list[list[int]]) -> None:
        arr = ((ctypes.c_ushort * 256) * 3)()
        for c in range(3):
            for i in range(256):
                arr[c][i] = ramp[c][i]
        if not self._with_dc(self.gdi32.SetDeviceGammaRamp, arr):
            raise DisplayError("The display driver rejected the color adjustment.")
        # The API may return success without setting a requested ramp.
        # Check for a visible difference if the requested ramp is different.
        current = self._read()
        if current == self.original and ramp != self.original:
            raise DisplayError("The driver ignored the color adjustment. Try disabling HDR or Night light.")

    def apply(self, ramp: list[list[int]]) -> None:
        self._write(ramp)
        self.changed = True

    def restore(self) -> None:
        if self.changed:
            self._write(self.original)
            self.changed = False


def is_startup_enabled() -> bool:
    if sys.platform != "win32":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY) as key:
            winreg.QueryValueEx(key, STARTUP_VALUE)
            return True
    except FileNotFoundError:
        return False


def set_startup(enabled: bool) -> None:
    """Only modify LumaTint's own value under HKCU Run.

    Only allows the packaged EXE to register itself. No admin rights needed.
    """
    if sys.platform != "win32":
        raise OSError("Automatic startup is available on Windows only.")
    if not getattr(sys, "frozen", False):
        raise OSError("Build LumaTint.exe before enabling Windows startup.")
    import winreg
    if enabled:
        executable = Path(sys.executable).resolve()
        command = f'"{executable}" --minimized'
        if len(command) > 260:
            raise OSError("Move LumaTint.exe to a shorter path, then try again.")
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, STARTUP_VALUE, 0, winreg.REG_SZ, command)
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, STARTUP_VALUE)
        except FileNotFoundError:
            pass
