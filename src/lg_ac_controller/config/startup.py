"""Integração opcional com a inicialização do Windows."""

from __future__ import annotations

import sys


class StartupManager:
    """Manages only the current user's Run entry; disabled by default."""

    _RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    _APP_NAME = "LGAcController"

    def __init__(self, command: str | None = None) -> None:
        self._command = command or _default_command()

    def is_enabled(self) -> bool:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._RUN_KEY) as key:
                value, _ = winreg.QueryValueEx(key, self._APP_NAME)
        except FileNotFoundError:
            return False
        return value == self._command

    def set_enabled(self, enabled: bool) -> None:
        import winreg

        if enabled:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self._RUN_KEY) as key:
                winreg.SetValueEx(key, self._APP_NAME, 0, winreg.REG_SZ, self._command)
            return

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, self._RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, self._APP_NAME)
        except FileNotFoundError:
            pass


def _default_command() -> str:
    """Return a Run command for source execution or a frozen executable."""

    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    return f'"{sys.executable}" -m lg_ac_controller.main'
