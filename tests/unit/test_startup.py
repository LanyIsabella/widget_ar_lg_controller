import sys

from lg_ac_controller.config.startup import StartupManager
from lg_ac_controller.config.instance import SingleInstanceGuard


def test_startup_command_is_explicit():
    manager = StartupManager(command="python -m lg_ac_controller.main")
    assert manager._command == "python -m lg_ac_controller.main"


def test_single_instance_guard_excludes_second_owner(tmp_path):
    path = tmp_path / "instance.lock"
    first = SingleInstanceGuard(path)
    second = SingleInstanceGuard(path)

    assert first.acquire() is True
    assert second.acquire() is False

    first.release()
    assert second.acquire() is True
    second.release()


def test_startup_command_for_frozen_executable(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Apps\LGAcController.exe")

    assert StartupManager()._command == r'"C:\Apps\LGAcController.exe"'
