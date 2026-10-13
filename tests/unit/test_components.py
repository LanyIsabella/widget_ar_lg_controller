import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from lg_ac_controller.ui.components import (
    AirConditionerGlyph,
    ConnectionIndicator,
    ModernSwitch,
    SegmentedSelector,
    TemperatureControl,
)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_temperature_control_respects_real_range_and_step(qapp):
    control = TemperatureControl()
    control.configure(18, 30, 0.5)
    control.set_value(23)

    control._plus_button.click()
    qapp.processEvents()

    assert control.value() == 23.5
    assert control._value_label.text() == "23.5 °C"
    control.set_value(30)
    assert not control._plus_button.isEnabled()


def test_segmented_selector_translates_labels_but_emits_raw_value(qapp):
    selector = SegmentedSelector()
    emitted = []
    selector.valueChanged.connect(emitted.append)
    selector.set_options(("COOL", "FAN"), "COOL")

    assert selector.itemText(0) == "Resfriar"
    assert selector.itemData(0) == "COOL"
    selector._buttons[1].click()
    qapp.processEvents()

    assert emitted == ["FAN"]
    assert selector.currentData() == "FAN"


def test_switch_and_glyph_have_stateful_visual_components(qapp):
    switch = ModernSwitch()
    switch.click()
    assert switch.isChecked()

    glyph = AirConditionerGlyph()
    glyph.set_status("POWER_ON", "COOL", "AUTO", False)
    glyph.show()
    qapp.processEvents()
    assert glyph._animation_timer.isActive()
    glyph.hide()
    assert not glyph._animation_timer.isActive()


def test_connection_indicator_pulses_only_while_syncing(qapp):
    indicator = ConnectionIndicator()
    indicator.set_state("syncing", "Sincronizando")
    assert indicator._pulse_timer.isActive()
    indicator.set_state("connected", "Online")
    assert not indicator._pulse_timer.isActive()
