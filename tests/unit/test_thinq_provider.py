import asyncio

import pytest

from lg_ac_controller.integrations.thinq_provider import ThinQProvider
from lg_ac_controller.integrations.errors import (
    ProviderAuthenticationError,
    ProviderErrorKind,
    ProviderTimeoutError,
)


class FakeThinQApi:
    async def async_get_device_list(self, timeout):
        return [
            {
                "deviceId": "ac-1",
                "deviceInfo": {
                    "deviceType": "DEVICE_AIR_CONDITIONER",
                    "modelName": "RAC_056905_WW",
                    "alias": "Ar-condicionado",
                },
            }
        ]

    async def async_get_device_profile(self, device_id, timeout):
        return {"property": {"operation": {"airConOperationMode": {"mode": ["r", "w"]}}}}

    async def async_get_device_status(self, device_id, timeout):
        return {"operation": {"airConOperationMode": "POWER_OFF"}}

    async def async_post_device_control(self, device_id, payload, timeout):
        return {"accepted": True}


def test_provider_maps_nested_real_device_response():
    provider = ThinQProvider(FakeThinQApi())
    devices = asyncio.run(provider.list_devices())
    assert devices[0].device_id == "ac-1"
    assert devices[0].device_type == "DEVICE_AIR_CONDITIONER"
    assert devices[0].model_name == "RAC_056905_WW"


def test_provider_accepts_wrapped_device_list_response():
    api = FakeThinQApi()
    api.async_get_device_list = lambda timeout: _wrapped_devices()
    provider = ThinQProvider(api)
    devices = asyncio.run(provider.list_devices())
    assert devices[0].device_id == "ac-1"


async def _wrapped_devices():
    return {"deviceList": await FakeThinQApi().async_get_device_list(timeout=15)}


def test_provider_maps_profile_state_and_control():
    provider = ThinQProvider(FakeThinQApi())
    capabilities = asyncio.run(provider.get_capabilities("ac-1"))
    state = asyncio.run(provider.get_state("ac-1"))
    submission = asyncio.run(
        provider.send_control(
            "ac-1", {"operation": {"airConOperationMode": "POWER_OFF"}}
        )
    )
    assert "property" in capabilities.profile
    assert state.state["operation"]["airConOperationMode"] == "POWER_OFF"
    assert submission.response["accepted"] is True


def test_provider_classifies_timeout_without_exposing_raw_error():
    class TimeoutApi(FakeThinQApi):
        async def async_get_device_list(self, timeout):
            raise TimeoutError("PAT=secret")

    with pytest.raises(ProviderTimeoutError) as exc_info:
        asyncio.run(ThinQProvider(TimeoutApi()).list_devices())
    assert "secret" not in str(exc_info.value)
    assert exc_info.value.kind is ProviderErrorKind.TIMEOUT


def test_provider_classifies_observed_authentication_code():
    class AuthApi(FakeThinQApi):
        async def async_get_device_list(self, timeout):
            error = RuntimeError("not printed")
            error.code = 1309
            raise error

    with pytest.raises(ProviderAuthenticationError):
        asyncio.run(ThinQProvider(AuthApi()).list_devices())


def test_provider_retries_read_but_not_control():
    class FlakyApi(FakeThinQApi):
        def __init__(self):
            self.read_calls = 0
            self.control_calls = 0

        async def async_get_device_list(self, timeout):
            self.read_calls += 1
            if self.read_calls == 1:
                raise TimeoutError("temporary")
            return await FakeThinQApi().async_get_device_list(timeout)

        async def async_post_device_control(self, device_id, payload, timeout):
            self.control_calls += 1
            raise TimeoutError("control failure")

    api = FlakyApi()
    provider = ThinQProvider(api, read_attempts=2, retry_backoff_seconds=0)
    devices = asyncio.run(provider.list_devices())
    assert devices[0].device_id == "ac-1"
    assert api.read_calls == 2

    with pytest.raises(ProviderTimeoutError):
        asyncio.run(provider.send_control("ac-1", {"operation": {"x": "y"}}))
    assert api.control_calls == 1
