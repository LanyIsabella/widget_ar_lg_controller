import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from lg_ac_controller.domain.models import DeviceCapabilities, DeviceState
from lg_ac_controller.services.sync_service import SyncSnapshot
from lg_ac_controller.ui.widget import AirConditionerWidget, _display_value
from lg_ac_controller.config.preferences import SettingsStore
from lg_ac_controller.config.settings import ControllerSettings


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_widget_renders_confirmed_snapshot_and_supported_power_control(qapp):
    widget = AirConditionerWidget()
    snapshot = SyncSnapshot(
        capabilities=DeviceCapabilities(
            "ac-1",
            {
                "property": {
                    "operation": {
                        "airConOperationMode": {
                            "mode": ["r", "w"],
                            "value": {"w": ["POWER_OFF", "POWER_ON"]},
                        }
                    }
                }
            },
        ),
        state=DeviceState(
            "ac-1",
            {
                "operation": {
                    "airConOperationMode": "POWER_ON",
                    "currentJobMode": "COOL",
                    "targetTemperature": 23,
                    "currentTemperature": 27,
                    "windStrength": "AUTO",
                }
            },
        ),
    )

    widget.show()
    qapp.processEvents()
    widget._render_snapshot(snapshot)

    assert "23" in widget._temperature_label.text()
    assert "ligado" in widget._power_label.text()
    assert not widget._power_button.isHidden()
    widget.close()


def test_widget_hides_unsupported_power_control(qapp):
    widget = AirConditionerWidget()
    widget._render_snapshot(
        SyncSnapshot(
            capabilities=DeviceCapabilities("ac-1", {}),
            state=DeviceState("ac-1", {"operation": {"airConOperationMode": "POWER_ON"}}),
        )
    )
    assert widget._power_button.isHidden()
    widget.close()


def test_widget_periodic_sync_uses_configured_interval_and_minimum(qapp, tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save(ControllerSettings(sync_interval_seconds=120))
    widget = AirConditionerWidget(settings_store=store)

    class Controller:
        pass

    widget.set_controller(Controller())
    assert widget._sync_timer.interval() == 120_000
    widget.close()

    store.save(ControllerSettings(sync_interval_seconds=60))
    widget = AirConditionerWidget(settings_store=store)
    widget.set_controller(Controller())
    assert widget._sync_timer.interval() == 60_000
    widget.close()


def test_widget_persists_sync_interval(qapp, tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    widget = AirConditionerWidget(settings_store=store)

    widget._sync_interval_spin.setValue(180)

    assert store.load().sync_interval_seconds == 180
    widget.close()


def test_widget_uses_translated_values_and_keeps_system_preferences_outside_main_view(qapp):
    widget = AirConditionerWidget()
    widget._render_snapshot(
        SyncSnapshot(
            capabilities=DeviceCapabilities(
                "ac-1",
                {
                    "property": {
                        "airConJobMode": {
                            "currentJobMode": {
                                "mode": ["r", "w"],
                                "value": {"w": ["COOL", "AIR_DRY"]},
                            }
                        },
                        "airFlow": {
                            "windStrength": {
                                "mode": ["r", "w"],
                                "value": {"w": ["AUTO", "LOW"]},
                            }
                        },
                    }
                },
            ),
            state=DeviceState(
                "ac-1",
                {
                    "operation": {
                        "airConOperationMode": "POWER_ON",
                        "currentJobMode": "COOL",
                        "windStrength": "AUTO",
                    }
                },
            ),
        )
    )

    assert _display_value("COOL") == "Resfriar"
    assert _display_value("LOW") == "Baixa"
    assert widget._mode_combo.itemText(0) == "Resfriar"
    assert widget._mode_combo.itemData(0) == "COOL"
    assert widget._fan_combo.itemText(0) == "Automático"
    assert not widget._always_on_top.isVisible()
    assert not widget._startup_checkbox.isVisible()
    assert not widget._sync_interval_spin.isVisible()
    widget.close()


def test_widget_renders_confirmed_air_direction_and_display_light(qapp):
    widget = AirConditionerWidget()
    widget.show()
    widget._render_snapshot(
        SyncSnapshot(
            capabilities=DeviceCapabilities(
                "ac-1",
                {
                    "property": {
                        "windDirection": {
                            "rotateUpDown": {
                                "mode": ["r", "w"],
                                "value": {"r": [True, False], "w": [True, False]},
                            }
                        },
                        "display": {
                            "light": {
                                "mode": ["r", "w"],
                                "value": {"r": ["ON", "OFF"], "w": ["ON", "OFF"]},
                            }
                        },
                    }
                },
            ),
            state=DeviceState(
                "ac-1",
                {
                    "windDirection": {"rotateUpDown": True},
                    "display": {"light": "ON"},
                },
            ),
        )
    )
    qapp.processEvents()

    assert not widget._airflow_card.isHidden()
    assert widget._swing_checkbox.isChecked()
    assert widget._swing_state_label.text() == "Ativa"
    assert not widget._display_card.isHidden()
    assert widget._display_light_switch.isChecked()
    assert widget._display_light_state_label.text() == "Ligada"
    assert widget._display_light_switch.isEnabled()
    widget.close()


def test_widget_does_not_guess_unknown_display_state_and_restores_last_value(qapp):
    widget = AirConditionerWidget()
    unknown = SyncSnapshot(
        capabilities=DeviceCapabilities(
            "ac-1",
            {
                "property": {
                    "display": {
                        "light": {
                            "mode": ["r", "w"],
                            "value": {"r": ["ON", "OFF"], "w": ["ON", "OFF"]},
                        }
                    }
                }
            },
        ),
        state=DeviceState("ac-1", {}),
    )
    widget._render_snapshot(unknown)
    assert not widget._display_light_switch.isEnabled()
    assert widget._display_light_state_label.text() == "Indisponível"

    confirmed = SyncSnapshot(
        capabilities=DeviceCapabilities(
            "ac-1",
            {
                "property": {
                    "display": {
                        "light": {
                            "mode": ["r", "w"],
                            "value": {"r": ["ON", "OFF"], "w": ["ON", "OFF"]},
                        }
                    }
                }
            },
        ),
        state=DeviceState("ac-1", {"display": {"light": "ON"}}),
    )
    widget._render_snapshot(confirmed)
    widget._display_light_switch.setChecked(False)
    widget._render_error("timeout")

    assert widget._display_light_switch.isChecked()
    assert widget._connection_indicator.property("state") == "error"
    widget.close()
