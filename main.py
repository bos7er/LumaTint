"""LumaTint app entry point."""

import ctypes
import sys
from tkinter import messagebox


def main() -> None:
    if sys.platform != "win32":
        print("LumaTint runs on Windows 10/11.")
        return
    # Avoid two copies competing to change the same display gamma ramp.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    mutex = kernel32.CreateMutexW(None, False, "Local\\LumaTint-Desktop-App")
    if mutex and ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        messagebox.showinfo("LumaTint", "LumaTint is already running. Check the system tray.")
        kernel32.CloseHandle(mutex)
        return
    try:
        from lumatint.app import LumaTintApp
        app = LumaTintApp(start_minimized="--minimized" in sys.argv)
        app.mainloop()
    finally:
        if mutex:
            kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
