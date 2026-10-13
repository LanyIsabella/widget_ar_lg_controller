"""Controle de instância única do aplicativo desktop."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QLockFile


def default_lock_path() -> Path:
    """Return a per-user lock path without storing credentials."""

    local_app_data = os.getenv("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".local"
    return base / "LGAcController" / "instance.lock"


class SingleInstanceGuard:
    """Owns a lock while the desktop application is running."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_lock_path()
        self._lock = QLockFile(str(self.path))
        self._lock.setStaleLockTime(30_000)

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return self._lock.tryLock(100)

    def release(self) -> None:
        if self._lock.isLocked():
            self._lock.unlock()
