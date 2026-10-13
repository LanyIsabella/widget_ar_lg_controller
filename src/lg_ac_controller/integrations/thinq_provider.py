"""Adaptador do SDK oficial ThinQ Connect para o contrato do domínio."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from lg_ac_controller.domain.models import (
    ControlSubmission,
    DeviceCapabilities,
    DeviceState,
    DeviceSummary,
    device_field,
)
from lg_ac_controller.integrations.base import ACProvider
from lg_ac_controller.integrations.errors import invoke_provider


class ThinQProvider(ACProvider):
    """Converte respostas do SDK sem colocar detalhes do SDK na UI."""

    def __init__(
        self,
        api: Any,
        *,
        timeout: float = 15.0,
        read_attempts: int = 2,
        retry_backoff_seconds: float = 0.5,
        session: Any | None = None,
    ) -> None:
        self._api = api
        self._timeout = timeout
        self._read_attempts = read_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._session = session

    @classmethod
    async def create(
        cls,
        *,
        access_token: str,
        country_code: str,
        client_id: str,
        timeout: float = 15.0,
        read_attempts: int = 2,
        retry_backoff_seconds: float = 0.5,
    ) -> "ThinQProvider":
        """Create a provider and own the SDK HTTP session lifecycle."""

        from aiohttp import ClientSession
        from thinqconnect.thinq_api import ThinQApi

        session = ClientSession()
        try:
            api = ThinQApi(
                session=session,
                access_token=access_token,
                country_code=country_code,
                client_id=client_id,
            )
        except Exception:
            await session.close()
            raise
        return cls(
            api,
            timeout=timeout,
            read_attempts=read_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
            session=session,
        )

    async def close(self) -> None:
        """Close the HTTP session created by :meth:`create`, if any."""

        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "ThinQProvider":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        await self.close()

    async def list_devices(self) -> Sequence[DeviceSummary]:
        response = await invoke_provider(
            "list_devices",
            lambda: self._api.async_get_device_list(timeout=self._timeout),
            attempts=self._read_attempts,
            backoff_seconds=self._retry_backoff_seconds,
        )
        if isinstance(response, list):
            raw_devices = response
        elif isinstance(response, Mapping):
            raw_devices = next(
                (
                    value
                    for key in ("devices", "deviceList", "list", "data")
                    if isinstance((value := response.get(key)), list)
                ),
                None,
            )
        else:
            raw_devices = None
        if raw_devices is None:
            raise ValueError("A API ThinQ retornou uma lista de dispositivos inválida.")
        return [
            DeviceSummary(
                device_id=str(device_field(device, "deviceId")),
                device_type=device_field(device, "deviceType"),
                model_name=device_field(device, "modelName"),
                alias=device_field(device, "alias"),
                reportable=device_field(device, "reportable"),
                group_id=device_field(device, "groupId"),
            )
            for device in raw_devices
            if isinstance(device, Mapping) and device_field(device, "deviceId")
        ]

    async def get_capabilities(self, device_id: str) -> DeviceCapabilities:
        profile = await invoke_provider(
            "get_capabilities",
            lambda: self._api.async_get_device_profile(
                device_id=device_id, timeout=self._timeout
            ),
            attempts=self._read_attempts,
            backoff_seconds=self._retry_backoff_seconds,
        )
        return DeviceCapabilities(device_id=device_id, profile=_as_dict(profile))

    async def get_state(self, device_id: str) -> DeviceState:
        state = await invoke_provider(
            "get_state",
            lambda: self._api.async_get_device_status(
                device_id=device_id, timeout=self._timeout
            ),
            attempts=self._read_attempts,
            backoff_seconds=self._retry_backoff_seconds,
        )
        return DeviceState(device_id=device_id, state=_as_dict(state))

    async def send_control(
        self, device_id: str, payload: Mapping[str, Any]
    ) -> ControlSubmission:
        response = await invoke_provider(
            "send_control",
            lambda: self._api.async_post_device_control(
                device_id=device_id,
                payload=dict(payload),
                timeout=self._timeout,
            ),
        )
        return ControlSubmission(device_id=device_id, response=_as_dict(response))


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, Mapping):
        return dict(value)
    return {}
