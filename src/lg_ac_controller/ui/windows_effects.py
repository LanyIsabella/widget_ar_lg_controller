"""Efeitos opcionais do compositor do Windows para a janela translúcida."""

from __future__ import annotations

import ctypes
import sys
from typing import Any


def apply_backdrop(widget: Any, dark: bool) -> bool:
    """Tenta aplicar Acrylic no Windows 10/11, mantendo fallback Qt seguro."""

    if sys.platform != "win32":
        return False
    try:
        hwnd = int(widget.winId())
        dwmapi = ctypes.windll.dwmapi
        use_dark_mode = ctypes.c_int(1 if dark else 0)
        backdrop = ctypes.c_int(3)  # DWMSBT_TRANSIENTWINDOW / Acrylic-like backdrop
        dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(20),
            ctypes.byref(use_dark_mode),
            ctypes.sizeof(use_dark_mode),
        )
        result = dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(38),
            ctypes.byref(backdrop),
            ctypes.sizeof(backdrop),
        )
        return result == 0
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def prefers_reduced_motion() -> bool:
    """Read the Windows client-area animation preference when available."""

    if sys.platform != "win32":
        return False
    try:
        value = ctypes.c_int()
        # SPI_GETCLIENTAREAANIMATION = 0x1042; zero means animations disabled.
        success = ctypes.windll.user32.SystemParametersInfoW(
            ctypes.c_uint(0x1042),
            ctypes.c_uint(0),
            ctypes.byref(value),
            ctypes.c_uint(0),
        )
        return bool(success and not value.value)
    except (AttributeError, OSError, TypeError, ValueError):
        return False
