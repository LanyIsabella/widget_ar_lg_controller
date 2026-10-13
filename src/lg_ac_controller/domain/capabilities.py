"""Consultas seguras sobre capacidades publicadas pelo perfil do modelo."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def profile_property(
    profile: Mapping[str, Any], resource: str, property_name: str
) -> Mapping[str, Any] | None:
    roots: list[Mapping[str, Any]] = [profile]
    property_root = profile.get("property")
    if isinstance(property_root, Mapping):
        roots.insert(0, property_root)
    for root in roots:
        resource_data = root.get(resource)
        if isinstance(resource_data, Mapping):
            property_data = resource_data.get(property_name)
            if isinstance(property_data, Mapping):
                return property_data
    return None


def writable_enum_values(
    profile: Mapping[str, Any], resource: str, property_name: str
) -> tuple[Any, ...]:
    property_data = profile_property(profile, resource, property_name)
    if property_data is None or "w" not in property_data.get("mode", []):
        return ()
    value_data = property_data.get("value")
    values = value_data.get("w") if isinstance(value_data, Mapping) else None
    return tuple(values) if isinstance(values, list) else ()


def writable_range(
    profile: Mapping[str, Any], resource: str, property_name: str
) -> tuple[float, float, float] | None:
    property_data = profile_property(profile, resource, property_name)
    if property_data is None or "w" not in property_data.get("mode", []):
        return None
    value_data = property_data.get("value")
    range_data = value_data.get("w") if isinstance(value_data, Mapping) else None
    if not isinstance(range_data, Mapping):
        return None
    try:
        minimum = float(range_data["min"])
        maximum = float(range_data["max"])
        step = float(range_data["step"])
    except (KeyError, TypeError, ValueError):
        return None
    return (minimum, maximum, step) if minimum <= maximum and step > 0 else None


def profile_supports_writable_enum(
    profile: Mapping[str, Any], resource: str, property_name: str, value: str
) -> bool:
    """Return true only when the profile explicitly exposes a writable value."""

    return value in writable_enum_values(profile, resource, property_name)
