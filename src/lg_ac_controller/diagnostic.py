"""Funções puras usadas pela prova de conceito ThinQ Connect.

Este módulo não faz chamadas de rede. A separação permite testar a seleção do
dispositivo e a redação do relatório sem conta LG ou hardware real.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from lg_ac_controller.domain.capabilities import (
    profile_supports_writable_enum as _profile_supports_writable_enum,
)

AIR_CONDITIONER_TYPE = "DEVICE_AIR_CONDITIONER"

_SENSITIVE_KEYS = {
    "accesstoken",
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "clientsecret",
    "password",
    "pat",
    "refreshtoken",
    "refresh_token",
    "token",
    "x-api-key",
    "xapikey",
}

_OBSERVED_KEYS = {
    "airConOperationMode",
    "currentJobMode",
    "currentTemperature",
    "currentTemperatureC",
    "currentTemperatureF",
    "targetTemperature",
    "targetTemperatureC",
    "targetTemperatureF",
    "temperatureUnit",
    "unit",
    "windStrength",
    "windStrengthDetail",
    "rotateUpDown",
    "light",
}


def device_field(device: Mapping[str, Any], field: str) -> Any:
    """Read a device field from flat and current nested API response shapes."""

    if field in device:
        return device[field]
    device_info = device.get("deviceInfo")
    if isinstance(device_info, Mapping):
        return device_info.get(field)
    return None


def summarize_device(
    device: Mapping[str, Any], *, reveal_device_id: bool = True
) -> dict[str, Any]:
    """Return only fields needed to identify a device in the diagnostic."""

    return {
        "device_id": device_field(device, "deviceId")
        if reveal_device_id
        else "[REDACTED]",
        "device_type": device_field(device, "deviceType"),
        "model_name": device_field(device, "modelName"),
        "alias": device_field(device, "alias"),
        "reportable": device_field(device, "reportable"),
        "group_id": device_field(device, "groupId"),
        "returned_keys": sorted(str(key) for key in device),
    }


def normalize_device_list(response: Any) -> list[Mapping[str, Any]]:
    """Normalize the SDK response while preserving unknown payloads for errors."""

    if isinstance(response, list):
        return [item for item in response if isinstance(item, Mapping)]

    if isinstance(response, Mapping):
        for key in ("devices", "deviceList", "list", "data"):
            value = response.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, Mapping)]

    raise ValueError("A resposta da API não contém uma lista de dispositivos reconhecível.")


def select_air_conditioner(
    devices: Sequence[Mapping[str, Any]],
    *,
    device_id: str | None = None,
    alias: str | None = None,
    index: int | None = None,
) -> Mapping[str, Any]:
    """Select an AC without guessing when more than one candidate exists."""

    candidates = [
        device
        for device in devices
        if device_field(device, "deviceType") == AIR_CONDITIONER_TYPE
    ]
    if not candidates:
        raise ValueError("Nenhum dispositivo do tipo ar-condicionado foi encontrado.")

    if device_id:
        matches = [
            device for device in candidates if device_field(device, "deviceId") == device_id
        ]
    elif alias:
        wanted = alias.casefold()
        matches = [
            device
            for device in candidates
            if str(device_field(device, "alias") or "").casefold() == wanted
        ]
    elif index is not None:
        if index < 1 or index > len(candidates):
            raise ValueError(f"--device-index deve estar entre 1 e {len(candidates)}.")
        matches = [candidates[index - 1]]
    elif len(candidates) == 1:
        matches = candidates
    else:
        available = ", ".join(
            f"{position}: {device_field(device, 'alias') or device_field(device, 'modelName') or 'sem alias'}"
            for position, device in enumerate(candidates, start=1)
        )
        raise ValueError(
            "Mais de um ar-condicionado foi encontrado; escolha --device-id, "
            f"--device-alias ou --device-index. Disponíveis: {available}"
        )

    if len(matches) != 1:
        selector = device_id or alias or "o seletor informado"
        raise ValueError(f"Nenhum ar-condicionado corresponde a {selector!r}.")
    return matches[0]


def redact_payload(value: Any, *, reveal_device_ids: bool = True) -> Any:
    """Redact token-like fields recursively before a report is printed."""

    sensitive_keys = {
        key.casefold().replace("-", "").replace("_", "")
        for key in _SENSITIVE_KEYS
    }
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = (
                str(key).casefold().replace("-", "").replace("_", "")
            )
            if normalized_key in sensitive_keys:
                redacted[str(key)] = "[REDACTED]"
            elif not reveal_device_ids and normalized_key == "deviceid":
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = redact_payload(
                    item, reveal_device_ids=reveal_device_ids
                )
        return redacted
    if isinstance(value, list):
        return [redact_payload(item, reveal_device_ids=reveal_device_ids) for item in value]
    if isinstance(value, tuple):
        return [redact_payload(item, reveal_device_ids=reveal_device_ids) for item in value]
    return value


def observed_attributes(value: Any) -> dict[str, Any]:
    """Extract known AC state keys without assuming a particular response shape."""

    found: dict[str, Any] = {}

    def visit(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if str(key) in _OBSERVED_KEYS and str(key) not in found:
                    found[str(key)] = child
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return found


def profile_supports_writable_enum(
    profile: Any, resource: str, property_name: str, value: str
) -> bool:
    """Compatibility wrapper used by the diagnostic CLI and its tests."""

    return isinstance(profile, Mapping) and _profile_supports_writable_enum(
        profile, resource, property_name, value
    )
