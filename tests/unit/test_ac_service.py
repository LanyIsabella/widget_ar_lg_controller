import asyncio

import pytest

from lg_ac_controller.domain.models import ControlSubmission, DeviceCapabilities, DeviceState
from lg_ac_controller.services.ac_service import (
    ACService,
    PhysicalControlNotAuthorized,
    UnsupportedControl,
)


class FakeProvider:
    async def list_devices(self):
        return []

    async def get_capabilities(self, device_id):
        return DeviceCapabilities(
            device_id,
            {
                "property": {
                    "operation": {
                        "airConOperationMode": {
                            "mode": ["r", "w"],
                            "value": {"w": ["POWER_ON", "POWER_OFF"]},
                        }
                    },
                    "windDirection": {
                        "rotateUpDown": {
                            "mode": ["r", "w"],
                            "value": {"w": [True, False]},
                        }
                    },
                    "display": {
                        "light": {
                            "mode": ["r", "w"],
                            "value": {"w": ["ON", "OFF"]},
                        }
                    },
                }
            },
        )

    async def get_state(self, device_id):
        return DeviceState(device_id, {})

    async def send_control(self, device_id, payload):
        return ControlSubmission(device_id, dict(payload))


def test_control_requires_explicit_authorization():
    with pytest.raises(PhysicalControlNotAuthorized):
        asyncio.run(
            ACService(FakeProvider()).send_control("ac-1", {"operation": {"x": "y"}})
        )


def test_read_device_returns_capabilities_and_state():
    capabilities, state = asyncio.run(ACService(FakeProvider()).read_device("ac-1"))
    assert capabilities.device_id == "ac-1"
    assert state.device_id == "ac-1"


def test_control_rejects_value_outside_profile():
    with pytest.raises(UnsupportedControl):
        asyncio.run(
            ACService(FakeProvider()).send_control(
                "ac-1",
                {"operation": {"airConOperationMode": "DRY"}},
                authorized=True,
            )
        )


def test_control_accepts_declared_air_direction_and_display_light():
    result = asyncio.run(
        ACService(FakeProvider()).send_control(
            "ac-1",
            {
                "windDirection": {"rotateUpDown": True},
                "display": {"light": "OFF"},
            },
            authorized=True,
        )
    )

    assert result.response["display"]["light"] == "OFF"
