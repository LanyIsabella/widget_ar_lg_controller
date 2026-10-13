"""Ícone e menu da bandeja do sistema Windows."""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from lg_ac_controller.ui.widget import AirConditionerWidget


class SystemTrayController(QObject):
    """Provides explicit hide/show actions and process termination."""

    def __init__(self, widget: AirConditionerWidget, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._widget = widget
        self._tray = QSystemTrayIcon(self._icon(), self)
        self._menu = QMenu()
        self._show_action = QAction("Mostrar", self._menu)
        self._show_action.triggered.connect(self.show_widget)
        self._menu.addAction(self._show_action)
        self._hide_action = QAction("Ocultar", self._menu)
        self._hide_action.triggered.connect(self.hide_widget)
        self._menu.addAction(self._hide_action)
        self._menu.addSeparator()
        quit_action = QAction("Encerrar", self._menu)
        quit_action.triggered.connect(self.quit_application)
        self._menu.addAction(quit_action)
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._activated)

    def show(self) -> None:
        self._tray.show()

    def show_widget(self) -> None:
        self._widget.showNormal()
        self._widget.activateWindow()
        self._widget.raise_()

    def hide_widget(self) -> None:
        self._widget.hide()

    def quit_application(self) -> None:
        self._tray.hide()
        self._widget.request_quit()
        QApplication.instance().quit()

    def _activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            if self._widget.isVisible():
                self.hide_widget()
            else:
                self.show_widget()

    @staticmethod
    def _icon() -> QIcon:
        application = QApplication.instance()
        if application is None:
            return QIcon()
        return application.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
