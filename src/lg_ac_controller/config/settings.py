"""Configuração não sensível e validações básicas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ControllerSettings:
    country: str = "BR"
    client_id: str = ""
    device_id: str = ""
    sync_interval_seconds: int = 300
    read_retry_attempts: int = 2
    retry_backoff_seconds: float = 0.5
    theme: str = "light"
    always_on_top: bool = False
    start_with_windows: bool = False
    window_geometry: str = ""

    def __post_init__(self) -> None:
        country = self.country.strip().upper()
        if len(country) != 2 or not country.isalpha():
            raise ValueError("country deve ser um código ISO de dois caracteres.")
        if self.sync_interval_seconds < 60:
            raise ValueError("sync_interval_seconds não pode ser menor que 60 segundos.")
        if self.read_retry_attempts < 1 or self.read_retry_attempts > 3:
            raise ValueError("read_retry_attempts deve estar entre 1 e 3.")
        if self.retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds não pode ser negativo.")
        theme = self.theme.strip().casefold()
        if theme not in {"light", "dark"}:
            raise ValueError("theme deve ser 'light' ou 'dark'.")
        object.__setattr__(self, "country", country)
        object.__setattr__(self, "theme", theme)
