import asyncio

import pytest

from lg_ac_controller.config.settings import ControllerSettings
from lg_ac_controller.config.preferences import SettingsPersistenceError, SettingsStore
from lg_ac_controller.config.identity import get_or_create_client_id
from lg_ac_controller.domain.models import ControlSubmission, DeviceCapabilities, DeviceState
from lg_ac_controller.services.ac_service import ACService
from lg_ac_controller.services.sync_service import SyncService


class FakeProvider:
    def __init__(self):
        self.state = {"operation": {"airConOperationMode": "POWER_ON"}}
        self.confirm_control = True

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
                    }
                }
            },
        )

    async def get_state(self, device_id):
        return DeviceState(device_id, self.state)

    async def send_control(self, device_id, payload):
        if self.confirm_control:
            self.state = {"operation": {"airConOperationMode": "POWER_OFF"}}
        return ControlSubmission(device_id, {})


def test_settings_rejects_aggressive_polling():
    with pytest.raises(ValueError):
        ControllerSettings(sync_interval_seconds=30)


def test_settings_rejects_unbounded_read_retries():
    with pytest.raises(ValueError):
        ControllerSettings(read_retry_attempts=4)


def test_settings_store_round_trip_excludes_pat(tmp_path):
    path = tmp_path / "settings.json"
    settings = ControllerSettings(
        country="br",
        client_id="client-1",
        device_id="device-1",
        sync_interval_seconds=120,
        read_retry_attempts=3,
        retry_backoff_seconds=1.25,
        theme="dark",
        always_on_top=True,
        start_with_windows=True,
        window_geometry="AQID",
    )

    SettingsStore(path).save(settings)
    restored = SettingsStore(path).load()

    assert restored == settings
    assert "PAT" not in path.read_text(encoding="utf-8").upper()


def test_settings_store_rejects_invalid_saved_values(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"sync_interval_seconds": 10}', encoding="utf-8")

    with pytest.raises(SettingsPersistenceError):
        SettingsStore(path).load()


def test_client_identity_is_reused(tmp_path):
    path = tmp_path / "client_id"
    first = get_or_create_client_id(path)
    second = get_or_create_client_id(path)

    assert first == second
    assert len(first) == 36


def test_sync_confirms_state_after_one_command():
    service = ACService(FakeProvider())
    sync = SyncService(service, "ac-1")
    snapshot = asyncio.run(
        sync.send_and_confirm(
            {"operation": {"airConOperationMode": "POWER_OFF"}},
            command_name="POWER_OFF",
            authorized=True,
            attempts=1,
        )
    )
    assert snapshot.error is None
    assert snapshot.pending_command is None
    assert snapshot.state is not None


def test_sync_clears_pending_command_when_confirmation_expires():
    provider = FakeProvider()
    provider.state = {"operation": {"airConOperationMode": "POWER_ON"}}
    provider.confirm_control = False
    service = ACService(provider)
    sync = SyncService(service, "ac-1")

    snapshot = asyncio.run(
        sync.send_and_confirm(
            {"operation": {"airConOperationMode": "POWER_OFF"}},
            command_name="POWER_OFF",
            authorized=True,
            attempts=1,
        )
    )

    assert snapshot.pending_command is None
    assert snapshot.error is not None


def test_sync_confirms_display_light_change():
    class DisplayProvider:
        def __init__(self):
            self.state = {"display": {"light": "ON"}}

        async def get_capabilities(self, device_id):
            return DeviceCapabilities(
                device_id,
                {
                    "property": {
                        "display": {
                            "light": {
                                "mode": ["r", "w"],
                                "value": {"w": ["ON", "OFF"]},
                            }
                        }
                    }
                },
            )

        async def get_state(self, device_id):
            return DeviceState(device_id, self.state)

        async def send_control(self, device_id, payload):
            self.state = payload
            return ControlSubmission(device_id, {"accepted": True})

    snapshot = asyncio.run(
        SyncService(ACService(DisplayProvider()), "ac-1").send_and_confirm(
            {"display": {"light": "OFF"}},
            command_name="light",
            authorized=True,
            attempts=1,
        )
    )

    assert snapshot.error is None
    assert snapshot.state is not None
    assert snapshot.state.state["display"]["light"] == "OFF"
