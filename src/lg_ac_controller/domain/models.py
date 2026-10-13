"""Modelos de domínio usados entre o provedor e a futura UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any


@dataclass(frozen=True, slots=True)
class DeviceSummary:
    device_id: str
    device_type: str | None
    model_name: str | None
    alias: str | None
    reportable: bool | None = None
    group_id: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceCapabilities:
    device_id: str
    profile: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DeviceState:
    device_id: str
    state: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ControlSubmission:
    """Resultado de envio, sem afirmar que o aparelho confirmou a mudança."""

    device_id: str
    response: dict[str, Any]
    confirmed: bool = field(default=False)


def device_field(device: Mapping[str, Any], field_name: str) -> Any:
    """Read flat and nested device list response formats."""

    if field_name in device:
        return device[field_name]
    info = device.get("deviceInfo")
    if isinstance(info, Mapping):
        return info.get(field_name)
    return None
