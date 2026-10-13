import asyncio

import pytest

from lg_ac_controller.config.preferences import SettingsStore
from lg_ac_controller.config.settings import ControllerSettings
from lg_ac_controller.domain.models import (
    ControlSubmission,
    DeviceCapabilities,
    DeviceState,
    DeviceSummary,
)
from lg_ac_controller.services.ac_service import ACService
from lg_ac_controller.services.application_controller import (
    ApplicationController,
    DeviceNotSelected,
    DeviceSelectionError,
)


class FakeProvider:
    def __init__(self):
        self.sent = 0
        self.state = {"operation": {"airConOperationMode": "POWER_ON"}}

    async def list_devices(self):
        return [
            DeviceSummary("ac-1", "DEVICE_AIR_CONDITIONER", "model", "Sala"),
            DeviceSummary("plug-1", "DEVICE_SMART_PLUG", "plug", "Tomada"),
        ]

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
                    }
                }
            },
        )

    async def get_state(self, device_id):
        return DeviceState(device_id, self.state)

    async def send_control(self, device_id, payload):
        self.sent += 1
        self.state = {"operation": {"airConOperationMode": "POWER_OFF"}}
        return ControlSubmission(device_id, {"accepted": True})


class FakeSession:
    def __init__(self, provider):
        self.provider = provider
        self.ac_service = ACService(provider)
        self.closed = False

    async def close(self):
        self.closed = True


def make_controller(tmp_path):
    provider = FakeProvider()
    session = FakeSession(provider)
    controller = ApplicationController(
        session,
        ControllerSettings(client_id="client-1"),
        SettingsStore(tmp_path / "settings.json"),
    )
    return controller, provider


def test_controller_discovers_only_air_conditioners_and_persists_selection(tmp_path):
    controller, _ = make_controller(tmp_path)
    devices = asyncio.run(controller.discover_devices())
    selected = asyncio.run(controller.select_device("ac-1"))

    assert [device.device_id for device in devices] == ["ac-1"]
    assert selected.alias == "Sala"
    assert SettingsStore(tmp_path / "settings.json").load().device_id == "ac-1"


def test_controller_requires_selection_and_rejects_unknown_device(tmp_path):
    controller, _ = make_controller(tmp_path)
    with pytest.raises(DeviceNotSelected):
        asyncio.run(controller.refresh())

    asyncio.run(controller.discover_devices())
    with pytest.raises(DeviceSelectionError):
        asyncio.run(controller.select_device("unknown"))


def test_controller_confirms_authorized_command_once(tmp_path):
    controller, provider = make_controller(tmp_path)
    asyncio.run(controller.select_device("ac-1"))

    snapshot = asyncio.run(
        controller.send_and_confirm(
            {"operation": {"airConOperationMode": "POWER_OFF"}},
            command_name="POWER_OFF",
            authorized=True,
            attempts=1,
        )
    )

    assert snapshot.error is None
    assert provider.sent == 1
