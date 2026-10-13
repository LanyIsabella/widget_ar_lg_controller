"""Fachada de aplicação usada pela apresentação desktop."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from collections.abc import Mapping, Sequence
from typing import Any

from lg_ac_controller.config.preferences import SettingsStore
from lg_ac_controller.config.settings import ControllerSettings
from lg_ac_controller.domain.models import DeviceSummary
from lg_ac_controller.services.ac_service import ACService
from lg_ac_controller.services.controller_session import ControllerSession
from lg_ac_controller.services.sync_service import SyncService, SyncSnapshot


AIR_CONDITIONER_TYPE = "DEVICE_AIR_CONDITIONER"


class DeviceSelectionError(ValueError):
    """Indica que o dispositivo solicitado não está disponível para seleção."""


class DeviceNotSelected(RuntimeError):
    """Indica que uma operação exige um dispositivo previamente selecionado."""


@dataclass(slots=True)
class ApplicationController:
    """Coordinates discovery, selected device state and command confirmation."""

    session: ControllerSession
    settings: ControllerSettings
    settings_store: SettingsStore | None = None
    _devices: tuple[DeviceSummary, ...] = field(init=False, default=())
    _sync: SyncService | None = field(init=False, default=None, repr=False)

    @property
    def devices(self) -> Sequence[DeviceSummary]:
        return self._devices

    @property
    def selected_device_id(self) -> str | None:
        return self.settings.device_id if self._sync is not None else None

    @property
    def sync_snapshot(self) -> SyncSnapshot:
        if self._sync is None:
            return SyncSnapshot(error="Nenhum ar-condicionado foi selecionado.")
        return self._sync.snapshot

    async def discover_devices(self) -> Sequence[DeviceSummary]:
        devices = await self.session.ac_service.list_devices()
        self._devices = tuple(
            device for device in devices if device.device_type == AIR_CONDITIONER_TYPE
        )

        if self.settings.device_id and any(
            device.device_id == self.settings.device_id for device in self._devices
        ):
            if self._sync is None:
                self._sync = SyncService(
                    self.session.ac_service, self.settings.device_id
                )
        return self._devices

    async def select_device(self, device_id: str) -> DeviceSummary:
        if not self._devices:
            await self.discover_devices()
        selected = next(
            (device for device in self._devices if device.device_id == device_id),
            None,
        )
        if selected is None:
            raise DeviceSelectionError(
                "O dispositivo informado não está entre os ar-condicionados disponíveis."
            )

        self.settings = replace(self.settings, device_id=device_id)
        if self.settings_store is not None:
            self.settings_store.save(self.settings)
        self._sync = SyncService(self.session.ac_service, device_id)
        return selected

    async def refresh(self) -> SyncSnapshot:
        return await self._require_sync().refresh()

    async def send_and_confirm(
        self,
        payload: Mapping[str, Any],
        *,
        command_name: str,
        authorized: bool = False,
        attempts: int = 3,
        delay_seconds: float = 2.0,
    ) -> SyncSnapshot:
        return await self._require_sync().send_and_confirm(
            dict(payload),
            command_name=command_name,
            authorized=authorized,
            attempts=attempts,
            delay_seconds=delay_seconds,
        )

    async def close(self) -> None:
        await self.session.close()

    def _require_sync(self) -> SyncService:
        if self._sync is None:
            raise DeviceNotSelected(
                "Selecione um ar-condicionado antes de consultar ou controlar o estado."
            )
        return self._sync
