import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from lg_ac_controller.ui.tray import SystemTrayController
from lg_ac_controller.ui.widget import AirConditionerWidget


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_tray_keeps_hide_explicit_and_supports_quit(qapp):
    widget = AirConditionerWidget()
    tray = SystemTrayController(widget)

    tray.hide_widget()
    tray.show_widget()
    widget.request_quit()
    widget.close()
