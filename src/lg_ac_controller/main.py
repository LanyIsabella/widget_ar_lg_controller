"""Ponto de entrada do widget desktop PySide6."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QApplication

from lg_ac_controller.config.credentials import WindowsCredentialStore
from lg_ac_controller.config.identity import get_or_create_client_id
from lg_ac_controller.config.instance import SingleInstanceGuard
from lg_ac_controller.config.preferences import SettingsStore
from lg_ac_controller.config.startup import StartupManager
from lg_ac_controller.services.application_controller import ApplicationController
from lg_ac_controller.services.controller_session import ControllerSession
from lg_ac_controller.ui.async_executor import AsyncExecutor
from lg_ac_controller.ui.tray import SystemTrayController
from lg_ac_controller.ui.widget import AirConditionerWidget


async def create_controller(settings, settings_store) -> ApplicationController:
    if not settings.client_id:
        settings = replace(
            settings,
            client_id=get_or_create_client_id(),
        )
        settings_store.save(settings)
    session = await ControllerSession.create(settings, WindowsCredentialStore())
    return ApplicationController(session, settings, settings_store)


def main() -> int:
    app = QApplication.instance() or QApplication([])
    instance_guard = SingleInstanceGuard()
    if not instance_guard.acquire():
        return 0
    try:
        executor = AsyncExecutor()
        settings_store = SettingsStore()
        settings = settings_store.load()
        if not settings.client_id:
            settings = replace(
                settings,
                client_id=get_or_create_client_id(),
            )
            settings_store.save(settings)
        startup_manager = StartupManager()
        if settings.start_with_windows and not startup_manager.is_enabled():
            startup_manager.set_enabled(True)
        widget = AirConditionerWidget(
            executor=executor,
            settings_store=settings_store,
            startup_manager=startup_manager,
        )
        tray = SystemTrayController(widget)
        tray.show()
        widget.initialize(lambda: create_controller(settings, settings_store))
        widget.show()
        return app.exec()
    finally:
        instance_guard.release()


if __name__ == "__main__":
    raise SystemExit(main())
