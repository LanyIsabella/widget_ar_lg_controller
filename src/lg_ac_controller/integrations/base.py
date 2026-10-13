"""Contrato agnóstico de provedor para o controlador."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from lg_ac_controller.domain.models import (
    ControlSubmission,
    DeviceCapabilities,
    DeviceState,
    DeviceSummary,
)


class ACProvider(ABC):
    """Operações de leitura e controle disponíveis para a camada de serviço."""

    @abstractmethod
    async def list_devices(self) -> Sequence[DeviceSummary]:
        raise NotImplementedError

    @abstractmethod
    async def get_capabilities(self, device_id: str) -> DeviceCapabilities:
        raise NotImplementedError

    @abstractmethod
    async def get_state(self, device_id: str) -> DeviceState:
        raise NotImplementedError

    @abstractmethod
    async def send_control(
        self, device_id: str, payload: Mapping[str, Any]
    ) -> ControlSubmission:
        raise NotImplementedError
