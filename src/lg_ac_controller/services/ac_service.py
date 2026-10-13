"""Serviço de aplicação para leitura e controle conservador do aparelho."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from lg_ac_controller.domain.models import (
    ControlSubmission,
    DeviceCapabilities,
    DeviceState,
    DeviceSummary,
)
from lg_ac_controller.domain.capabilities import writable_range
from lg_ac_controller.integrations.base import ACProvider


class PhysicalControlNotAuthorized(PermissionError):
    """Impedes envio acidental de comandos durante diagnóstico/desenvolvimento."""


class UnsupportedControl(ValueError):
    """Indica que o perfil do modelo não autoriza uma operação solicitada."""


class ACService:
    def __init__(self, provider: ACProvider) -> None:
        self._provider = provider

    async def list_devices(self) -> Sequence[DeviceSummary]:
        return await self._provider.list_devices()

    async def read_device(
        self, device_id: str
    ) -> tuple[DeviceCapabilities, DeviceState]:
        capabilities = await self._provider.get_capabilities(device_id)
        state = await self._provider.get_state(device_id)
        return capabilities, state

    async def send_control(
        self,
        device_id: str,
        payload: Mapping[str, Any],
        *,
        authorized: bool = False,
    ) -> ControlSubmission:
        if not authorized:
            raise PhysicalControlNotAuthorized(
                "Controle físico exige autorização explícita para esta operação."
            )

        if not payload:
            raise UnsupportedControl("O payload de controle não pode ser vazio.")

        capabilities = await self._provider.get_capabilities(device_id)
        _validate_writable_payload(capabilities.profile, payload)
        return await self._provider.send_control(device_id, payload)


def _validate_writable_payload(profile: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    """Validate only capabilities explicitly exposed as writable by the profile."""

    roots: list[Mapping[str, Any]] = [profile]
    property_root = profile.get("property")
    if isinstance(property_root, Mapping):
        roots.insert(0, property_root)

    for resource, properties in payload.items():
        if not isinstance(properties, Mapping):
            raise UnsupportedControl(f"O recurso {resource!r} possui formato inválido.")

        resource_data = next(
            (
                root.get(resource)
                for root in roots
                if isinstance(root.get(resource), Mapping)
            ),
            None,
        )
        if not isinstance(resource_data, Mapping):
            raise UnsupportedControl(
                f"O perfil não declara o recurso gravável {resource!r}."
            )

        for property_name, requested_value in properties.items():
            property_data = resource_data.get(property_name)
            if not isinstance(property_data, Mapping):
                raise UnsupportedControl(
                    f"O perfil não declara a propriedade {resource}.{property_name}."
                )

            modes = property_data.get("mode")
            if not isinstance(modes, list) or "w" not in modes:
                raise UnsupportedControl(
                    f"A propriedade {resource}.{property_name} não é gravável."
                )

            value_data = property_data.get("value")
            writable_values = value_data.get("w") if isinstance(value_data, Mapping) else None
            if isinstance(writable_values, list) and writable_values:
                if requested_value not in writable_values:
                    raise UnsupportedControl(
                        f"Valor {requested_value!r} não permitido para "
                        f"{resource}.{property_name}."
                    )
            elif isinstance(writable_values, Mapping):
                allowed_range = writable_range(profile, resource, property_name)
                if allowed_range is None or not isinstance(requested_value, (int, float)):
                    raise UnsupportedControl(
                        f"Valor {requested_value!r} não atende à faixa de "
                        f"{resource}.{property_name}."
                    )
                minimum, maximum, step = allowed_range
                if not minimum <= float(requested_value) <= maximum:
                    raise UnsupportedControl(
                        f"Valor {requested_value!r} fora da faixa de "
                        f"{resource}.{property_name}."
                    )
                offset = (float(requested_value) - minimum) / step
                if abs(offset - round(offset)) > 1e-6:
                    raise UnsupportedControl(
                        f"Valor {requested_value!r} não respeita o passo de "
                        f"{resource}.{property_name}."
                    )
