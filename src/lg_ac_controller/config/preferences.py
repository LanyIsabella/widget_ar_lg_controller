"""Persistência local de preferências que não contêm segredos."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lg_ac_controller.config.settings import ControllerSettings


class SettingsPersistenceError(RuntimeError):
    """Indica falha ao ler ou gravar preferências locais."""


_SETTING_FIELDS = frozenset(
    {
        "country",
        "client_id",
        "device_id",
        "sync_interval_seconds",
        "read_retry_attempts",
        "retry_backoff_seconds",
        "theme",
        "always_on_top",
        "start_with_windows",
        "window_geometry",
    }
)


class SettingsStore:
    """Armazena somente preferências explicitamente permitidas."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _default_settings_path()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> ControllerSettings:
        if not self._path.exists():
            return ControllerSettings()

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SettingsPersistenceError(
                "Não foi possível ler as preferências do aplicativo."
            ) from exc

        if not isinstance(raw, Mapping):
            raise SettingsPersistenceError("O arquivo de preferências possui formato inválido.")

        values = {key: raw[key] for key in _SETTING_FIELDS if key in raw}
        try:
            return ControllerSettings(**values)
        except (TypeError, ValueError) as exc:
            raise SettingsPersistenceError(
                "As preferências salvas não atendem às validações do aplicativo."
            ) from exc

    def save(self, settings: ControllerSettings) -> None:
        payload = {
            "country": settings.country,
            "client_id": settings.client_id,
            "device_id": settings.device_id,
            "sync_interval_seconds": settings.sync_interval_seconds,
            "read_retry_attempts": settings.read_retry_attempts,
            "retry_backoff_seconds": settings.retry_backoff_seconds,
            "theme": settings.theme,
            "always_on_top": settings.always_on_top,
            "start_with_windows": settings.start_with_windows,
            "window_geometry": settings.window_geometry,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._path.parent,
                prefix=f".{self._path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self._path)
            temporary_path = None
        except OSError as exc:
            raise SettingsPersistenceError(
                "Não foi possível gravar as preferências do aplicativo."
            ) from exc
        finally:
            if temporary_path:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass


def _default_settings_path() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    base_dir = Path(local_app_data) if local_app_data else Path.cwd() / ".runtime"
    return base_dir / "LGAcController" / "settings.json"
