"""Sincronização e confirmação de estado sem comandos repetidos."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from lg_ac_controller.domain.models import DeviceCapabilities, DeviceState
from lg_ac_controller.services.ac_service import ACService


@dataclass(frozen=True, slots=True)
class SyncSnapshot:
    capabilities: DeviceCapabilities | None = None
    state: DeviceState | None = None
    last_success_at: datetime | None = None
    pending_command: str | None = None
    error: str | None = None


class SyncService:
    def __init__(self, ac_service: ACService, device_id: str) -> None:
        self._ac_service = ac_service
        self._device_id = device_id
        self._snapshot = SyncSnapshot()

    @property
    def snapshot(self) -> SyncSnapshot:
        return self._snapshot

    async def refresh(self) -> SyncSnapshot:
        try:
            capabilities, state = await self._ac_service.read_device(self._device_id)
        except Exception as exc:  # noqa: BLE001 - service boundary stores safe message
            self._snapshot = SyncSnapshot(
                capabilities=self._snapshot.capabilities,
                state=self._snapshot.state,
                last_success_at=self._snapshot.last_success_at,
                pending_command=self._snapshot.pending_command,
                error=str(exc),
            )
            return self._snapshot

        self._snapshot = SyncSnapshot(
            capabilities=capabilities,
            state=state,
            last_success_at=datetime.now(timezone.utc),
            pending_command=None,
            error=None,
        )
        return self._snapshot

    async def send_and_confirm(
        self,
        payload: dict[str, Any],
        *,
        command_name: str,
        authorized: bool = False,
        attempts: int = 3,
        delay_seconds: float = 2.0,
    ) -> SyncSnapshot:
        if attempts < 1:
            raise ValueError("attempts deve ser pelo menos 1.")
        if delay_seconds < 0:
            raise ValueError("delay_seconds não pode ser negativo.")

        self._snapshot = SyncSnapshot(
            capabilities=self._snapshot.capabilities,
            state=self._snapshot.state,
            last_success_at=self._snapshot.last_success_at,
            pending_command=command_name,
            error=None,
        )
        try:
            await self._ac_service.send_control(
                self._device_id, payload, authorized=authorized
            )
        except Exception as exc:  # noqa: BLE001 - service boundary stores safe message
            self._snapshot = SyncSnapshot(
                capabilities=self._snapshot.capabilities,
                state=self._snapshot.state,
                last_success_at=self._snapshot.last_success_at,
                pending_command=None,
                error=str(exc),
            )
            return self._snapshot

        for attempt in range(attempts):
            if attempt:
                await asyncio.sleep(delay_seconds)
            snapshot = await self.refresh()
            if snapshot.error:
                return snapshot
            if _state_contains_command(snapshot.state, payload):
                return snapshot

        self._snapshot = SyncSnapshot(
            capabilities=self._snapshot.capabilities,
            state=self._snapshot.state,
            last_success_at=self._snapshot.last_success_at,
            pending_command=None,
            error=(
                f"O comando {command_name!r} não foi confirmado após "
                f"{attempts} leitura(s)."
            ),
        )
        return self._snapshot


def _state_contains_command(state: DeviceState | None, payload: dict[str, Any]) -> bool:
    if state is None:
        return False

    def find(mapping: Any, key: str) -> Any:
        if isinstance(mapping, dict):
            if key in mapping:
                return mapping[key]
            for child in mapping.values():
                result = find(child, key)
                if result is not None:
                    return result
        elif isinstance(mapping, list):
            for child in mapping:
                result = find(child, key)
                if result is not None:
                    return result
        return None

    for resource, properties in payload.items():
        if not isinstance(properties, dict):
            return False
        for property_name, expected in properties.items():
            if find(state.state, property_name) != expected:
                return False
    return True
