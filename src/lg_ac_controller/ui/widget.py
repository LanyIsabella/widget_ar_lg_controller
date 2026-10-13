"""Janela compacta da Etapa 3, sem acesso direto ao SDK ThinQ."""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Any

from PySide6.QtCore import QByteArray, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from lg_ac_controller.domain.capabilities import writable_enum_values, writable_range
from lg_ac_controller.domain.models import DeviceSummary
from lg_ac_controller.diagnostic import observed_attributes
from lg_ac_controller.config.preferences import SettingsStore
from lg_ac_controller.config.startup import StartupManager
from lg_ac_controller.services.application_controller import ApplicationController
from lg_ac_controller.services.sync_service import SyncSnapshot
from lg_ac_controller.ui.async_executor import AsyncExecutor
from lg_ac_controller.ui.components import (
    AirConditionerGlyph as AnimatedAirConditionerGlyph,
    ConnectionIndicator,
    DragBar as ModernDragBar,
    ModernSwitch,
    PowerButton,
    SegmentedSelector,
    TemperatureControl,
)
from lg_ac_controller.ui.windows_effects import apply_backdrop, prefers_reduced_motion


LIGHT_STYLE = """
QWidget#root { background: transparent; color: #18212b; font-family: 'Segoe UI'; }
QFrame#surface { background: rgba(248, 251, 255, 218); border: 1px solid rgba(255,255,255,190); border-radius: 26px; }
QFrame#section { background: rgba(255,255,255,155); border: 1px solid rgba(208,219,232,150); border-radius: 18px; }
QFrame#connectionIndicator { background: rgba(222,243,247,180); border-radius: 9px; }
QLabel#connectionText { color: #4a7180; font-size: 8pt; font-weight: 600; }
QLabel#connectionDot[state='connected'] { color: #22ad8f; }
QLabel#connectionDot[state='syncing'] { color: #e1a14f; }
QLabel#connectionDot[state='error'] { color: #d95e68; }
QLabel#connectionDot[state='idle'] { color: #9aabb9; }
QDialog#preferencesDialog { background: #f8fbff; color: #18212b; }
QLabel#dialogSubtitle { color: #728196; }
QLabel#fieldLabel { color: #526277; font-size: 9pt; font-weight: 600; }
QLabel#brand { color: #8795a6; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
QLabel#eyebrow { color: #7b8b9e; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #18212b; font-size: 14pt; font-weight: 700; }
QLabel#subtitle, QLabel#status { color: #728196; }
QLabel#temperature { color: #18212b; font-size: 30pt; font-weight: 700; }
QLabel#metric { color: #526277; font-size: 9pt; font-weight: 600; }
QLabel#metricValue { color: #18212b; font-size: 10pt; font-weight: 700; }
QLabel#switchState { color: #7b8b9e; font-size: 8pt; font-weight: 600; }
QPushButton { min-height: 30px; padding: 0 12px; border: 1px solid rgba(187,201,218,170); border-radius: 10px; background: rgba(255,255,255,210); color: #243244; font-weight: 600; }
QPushButton:hover { background: #ffffff; border-color: #71b8d6; }
QPushButton:pressed { background: #e7f5fa; }
QPushButton:disabled { color: #a6b1bf; }
QPushButton#power { min-height: 38px; border: none; border-radius: 12px; background: #1fa6c9; color: white; font-weight: 700; }
QPushButton#power:hover { background: #168dad; }
QPushButton#power[off='true'] { background: #e46067; }
QPushButton#iconButton { min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; padding: 0; border-radius: 10px; font-size: 12pt; }
QPushButton#closeButton { border: none; background: transparent; color: #8a98a8; }
QPushButton#closeButton:hover { background: #ffe8e9; color: #c74852; }
QPushButton#minimizeButton { border: none; background: transparent; color: #8a98a8; }
QPushButton#minimizeButton:hover { background: #e7f5fa; color: #168dad; }
QComboBox, QDoubleSpinBox, QSpinBox { min-height: 30px; padding: 0 8px; border: 1px solid rgba(187,201,218,180); border-radius: 9px; background: rgba(255,255,255,220); color: #243244; }
QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color: #42b2d2; }
QComboBox QAbstractItemView { background: #ffffff; color: #243244; selection-background-color: #dff3f8; selection-color: #18212b; border: 1px solid #cbd7e3; }
QPushButton#roundButton { min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 0; border-radius: 18px; font-size: 16pt; color: #268ba7; }
QLabel#temperatureControlValue { color: #18212b; font-size: 16pt; font-weight: 700; }
QPushButton#segmentButton { min-height: 32px; padding: 0 10px; border-radius: 9px; color: #536579; background: rgba(255,255,255,150); }
QPushButton#segmentButton:checked { color: #ffffff; background: #35abc5; border-color: #35abc5; }
QCheckBox { color: #526277; spacing: 7px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #b8c6d5; border-radius: 5px; background: white; }
QCheckBox::indicator:checked { background: #1fa6c9; border-color: #1fa6c9; }
"""

DARK_STYLE = """
QWidget#root { background: transparent; color: #edf4fa; font-family: 'Segoe UI'; }
QFrame#surface { background: rgba(23, 31, 42, 228); border: 1px solid rgba(104,126,149,120); border-radius: 26px; }
QFrame#section { background: rgba(40, 52, 67, 190); border: 1px solid rgba(104,126,149,100); border-radius: 18px; }
QFrame#connectionIndicator { background: rgba(49,76,86,200); border-radius: 9px; }
QLabel#connectionText { color: #aac0ca; font-size: 8pt; font-weight: 600; }
QLabel#connectionDot[state='connected'] { color: #45c8a8; }
QLabel#connectionDot[state='syncing'] { color: #e6b15f; }
QLabel#connectionDot[state='error'] { color: #ef7a84; }
QLabel#connectionDot[state='idle'] { color: #8b9cad; }
QDialog#preferencesDialog { background: #17202a; color: #edf4fa; }
QLabel#dialogSubtitle { color: #a6b7c8; }
QLabel#fieldLabel { color: #b4c4d4; font-size: 9pt; font-weight: 600; }
QLabel#brand, QLabel#eyebrow { color: #8da3b8; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }
QLabel#title { color: #f4f8fc; font-size: 14pt; font-weight: 700; }
QLabel#subtitle, QLabel#status { color: #a6b7c8; }
QLabel#temperature { color: #f4f8fc; font-size: 30pt; font-weight: 700; }
QLabel#metric { color: #a6b7c8; font-size: 9pt; font-weight: 600; }
QLabel#metricValue { color: #edf4fa; font-size: 10pt; font-weight: 700; }
QLabel#switchState { color: #8da3b8; font-size: 8pt; font-weight: 600; }
QPushButton { min-height: 30px; padding: 0 12px; border: 1px solid rgba(129,151,174,150); border-radius: 10px; background: rgba(51,67,85,220); color: #edf4fa; font-weight: 600; }
QPushButton:hover { background: #40546a; border-color: #63c2df; }
QPushButton:pressed { background: #26394c; }
QPushButton:disabled { color: #718499; }
QPushButton#power { min-height: 38px; border: none; border-radius: 12px; background: #20a8c9; color: white; font-weight: 700; }
QPushButton#power:hover { background: #35bddc; }
QPushButton#power[off='true'] { background: #db5964; }
QPushButton#iconButton { min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px; padding: 0; border-radius: 10px; font-size: 12pt; }
QPushButton#closeButton { border: none; background: transparent; color: #9aabbd; }
QPushButton#closeButton:hover { background: #572e37; color: #ff9da5; }
QPushButton#minimizeButton { border: none; background: transparent; color: #9aabbd; }
QPushButton#minimizeButton:hover { background: #29485a; color: #76d4ed; }
QComboBox, QDoubleSpinBox, QSpinBox { min-height: 30px; padding: 0 8px; border: 1px solid rgba(129,151,174,170); border-radius: 9px; background: rgba(51,67,85,220); color: #edf4fa; }
QComboBox:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color: #63c2df; }
QComboBox QAbstractItemView { background: #334355; color: #edf4fa; selection-background-color: #286477; selection-color: #ffffff; border: 1px solid #6f879e; }
QPushButton#roundButton { min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px; padding: 0; border-radius: 18px; font-size: 16pt; color: #7bd1e3; }
QLabel#temperatureControlValue { color: #f4f8fc; font-size: 16pt; font-weight: 700; }
QPushButton#segmentButton { min-height: 32px; padding: 0 10px; border-radius: 9px; color: #b4c4d4; background: rgba(51,67,85,190); }
QPushButton#segmentButton:checked { color: #ffffff; background: #248da8; border-color: #248da8; }
QCheckBox { color: #b4c4d4; spacing: 7px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #8297ab; border-radius: 5px; background: #334355; }
QCheckBox::indicator:checked { background: #20a8c9; border-color: #20a8c9; }
"""


class AirConditionerWidget(QWidget):
    """View/controller adapter that renders only confirmed snapshots."""

    def __init__(
        self,
        controller: ApplicationController | None = None,
        executor: AsyncExecutor | None = None,
        settings_store: SettingsStore | None = None,
        startup_manager: StartupManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._executor = executor
        self._settings_store = settings_store
        self._startup_manager = startup_manager
        self._task_handlers: dict[int, tuple[Callable[[Any], None], Callable[[str], None]]] = {}
        self._executor_signals_connected = False
        self._dark_theme = False
        self._last_confirmed_snapshot: SyncSnapshot | None = None
        self._swing_available = False
        self._swing_state_known = False
        self._display_light_available = False
        self._display_light_state_known = False
        self._sync_timer = QTimer(self)
        self._sync_timer.setSingleShot(False)
        self._sync_timer.timeout.connect(self._request_refresh)
        self._build_ui()
        initial_settings = settings_store.load() if settings_store is not None else None
        self.set_theme(initial_settings.theme if initial_settings else "light", persist=False)
        self._always_on_top.blockSignals(True)
        self._always_on_top.setChecked(
            initial_settings.always_on_top if initial_settings else False
        )
        self._always_on_top.blockSignals(False)
        self._startup_checkbox.blockSignals(True)
        self._startup_checkbox.setChecked(
            initial_settings.start_with_windows if initial_settings else False
        )
        self._startup_checkbox.blockSignals(False)
        self._sync_interval_spin.blockSignals(True)
        self._sync_interval_spin.setValue(
            initial_settings.sync_interval_seconds if initial_settings else 300
        )
        self._sync_interval_spin.blockSignals(False)
        if initial_settings and initial_settings.window_geometry:
            self.restoreGeometry(QByteArray.fromBase64(initial_settings.window_geometry.encode()))
        if self._controller is not None and self._executor is not None:
            self._request_discovery()

    def set_theme(self, theme: str, *, persist: bool = True) -> None:
        normalized = theme.casefold()
        if normalized not in {"light", "dark"}:
            raise ValueError("O tema deve ser 'light' ou 'dark'.")
        self._dark_theme = normalized == "dark"
        stylesheet = DARK_STYLE if self._dark_theme else LIGHT_STYLE
        self.setStyleSheet(stylesheet)
        self._preferences_dialog.setStyleSheet(stylesheet)
        self._glyph.set_dark(self._dark_theme)
        self._glyph.set_motion_enabled(not prefers_reduced_motion())
        self._swing_checkbox.set_dark(self._dark_theme)
        self._display_light_switch.set_dark(self._dark_theme)
        self._theme_button.setText("Tema claro" if self._dark_theme else "Tema escuro")
        if persist:
            self._persist_visual_preferences(theme=normalized)

    def set_controller(self, controller: ApplicationController) -> None:
        self._controller = controller
        self._start_periodic_sync()
        self._request_discovery()

    def initialize(self, controller_factory: Callable[[], Any]) -> None:
        """Create the application controller on the async executor loop."""

        self._status_label.setText("Inicializando integração...")
        self._submit(controller_factory, self.set_controller)

    def request_quit(self) -> None:
        self.close()

    def closeEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        self._sync_timer.stop()
        if self._executor is not None:
            cleanup = self._controller.close if self._controller is not None else None
            self._executor.close(cleanup=cleanup)
        self._persist_visual_preferences(
            window_geometry=bytes(self.saveGeometry().toBase64()).decode("ascii")
        )
        super().closeEvent(event)
        application = QApplication.instance()
        if application is not None:
            application.quit()

    def showEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        super().showEvent(event)
        apply_backdrop(self, self._dark_theme)
        self._glyph.set_motion_enabled(not prefers_reduced_motion())

    def hideEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        self._glyph.set_motion_enabled(False)
        super().hideEvent(event)

    def _build_ui(self) -> None:
        self.setWindowTitle("LG AC Controller")
        self.setObjectName("root")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(360)
        self.setMaximumWidth(430)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)

        surface = QFrame()
        surface.setObjectName("surface")
        if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            shadow = QGraphicsDropShadowEffect(surface)
            shadow.setBlurRadius(30)
            shadow.setOffset(0, 8)
            shadow.setColor(QColor(18, 37, 58, 72))
            surface.setGraphicsEffect(shadow)
        root.addWidget(surface)

        content = QVBoxLayout(surface)
        content.setContentsMargins(18, 14, 18, 16)
        content.setSpacing(12)

        title_bar = ModernDragBar(surface)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        brand = QLabel("LG AC")
        brand.setObjectName("brand")
        title_layout.addWidget(brand)
        title_layout.addStretch(1)
        self._connection_indicator = ConnectionIndicator()
        title_layout.addWidget(self._connection_indicator)
        self._minimize_button = QPushButton("—")
        self._minimize_button.setObjectName("minimizeButton")
        self._minimize_button.setToolTip("Minimizar")
        self._minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(self._minimize_button)
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setToolTip("Encerrar aplicação")
        close_button.clicked.connect(self.request_quit)
        title_layout.addWidget(close_button)
        content.addWidget(title_bar)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self._device_combo = QComboBox()
        self._device_combo.setPlaceholderText("Selecione o ar-condicionado")
        self._device_combo.currentIndexChanged.connect(self._device_changed)
        toolbar.addWidget(self._device_combo, 1)
        self._refresh_button = QPushButton("↻")
        self._refresh_button.setObjectName("iconButton")
        self._refresh_button.setToolTip("Atualizar estado")
        self._refresh_button.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_button)
        self._settings_button = QPushButton("⚙")
        self._settings_button.setObjectName("iconButton")
        self._settings_button.setToolTip("Preferências")
        self._settings_button.clicked.connect(self._open_preferences)
        toolbar.addWidget(self._settings_button)
        content.addLayout(toolbar)

        hero = QFrame()
        hero.setObjectName("section")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(12)
        self._glyph = AnimatedAirConditionerGlyph()
        hero_layout.addWidget(self._glyph)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(1)
        eyebrow = QLabel("AR-CONDICIONADO")
        eyebrow.setObjectName("eyebrow")
        hero_text.addWidget(eyebrow)
        self._temperature_label = QLabel("--")
        self._temperature_label.setObjectName("temperature")
        self._temperature_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hero_text.addWidget(self._temperature_label)
        self._power_label = QLabel("Estado: desconhecido")
        self._power_label.setObjectName("subtitle")
        hero_text.addWidget(self._power_label)
        hero_layout.addLayout(hero_text, 1)
        content.addWidget(hero)

        metrics = QHBoxLayout()
        metrics.setSpacing(8)
        self._mode_label = self._metric_block(metrics, "MODO", "--")
        self._fan_label = self._metric_block(metrics, "VENTILAÇÃO", "--")
        content.addLayout(metrics)

        self._controls_card = QFrame()
        self._controls_card.setObjectName("section")
        controls_outer = QVBoxLayout(self._controls_card)
        controls_outer.setContentsMargins(14, 12, 14, 14)
        controls_outer.setSpacing(8)
        controls_heading = QHBoxLayout()
        controls_title = QLabel("Controles")
        controls_title.setObjectName("title")
        controls_heading.addWidget(controls_title)
        controls_heading.addStretch(1)
        controls_outer.addLayout(controls_heading)
        self._target_control_label = QLabel("Temperatura alvo")
        self._target_control_label.setObjectName("fieldLabel")
        self._temperature_control = TemperatureControl()
        self._temperature_control.editingFinished.connect(
            lambda _value: self._target_changed()
        )
        self._target_spin = self._temperature_control
        controls_outer.addWidget(self._target_control_label)
        controls_outer.addWidget(self._temperature_control)
        self._mode_control_label = QLabel("Modo")
        self._mode_control_label.setObjectName("fieldLabel")
        self._mode_combo = SegmentedSelector()
        self._mode_combo.valueChanged.connect(self._mode_changed)
        controls_outer.addWidget(self._mode_control_label)
        controls_outer.addWidget(self._mode_combo)
        self._fan_control_label = QLabel("Ventilação")
        self._fan_control_label.setObjectName("fieldLabel")
        self._fan_combo = SegmentedSelector()
        self._fan_combo.valueChanged.connect(self._fan_changed)
        controls_outer.addWidget(self._fan_control_label)
        controls_outer.addWidget(self._fan_combo)
        self._swing_checkbox = ModernSwitch()
        self._swing_checkbox.toggled.connect(self._swing_changed)
        self._controls_card.setVisible(False)
        content.addWidget(self._controls_card)

        self._airflow_card = QFrame()
        self._airflow_card.setObjectName("section")
        airflow_outer = QVBoxLayout(self._airflow_card)
        airflow_outer.setContentsMargins(14, 12, 14, 12)
        airflow_outer.setSpacing(8)
        airflow_title = QLabel("Direção do ar")
        airflow_title.setObjectName("title")
        airflow_outer.addWidget(airflow_title)
        self._airflow_row = QHBoxLayout()
        self._airflow_label = QLabel("Oscilação vertical")
        self._airflow_label.setObjectName("fieldLabel")
        self._airflow_row.addWidget(self._airflow_label)
        self._airflow_row.addStretch(1)
        self._swing_state_label = QLabel("Indisponível")
        self._swing_state_label.setObjectName("switchState")
        self._airflow_row.addWidget(self._swing_state_label)
        self._airflow_row.addWidget(self._swing_checkbox)
        airflow_outer.addLayout(self._airflow_row)
        self._airflow_card.setVisible(False)
        content.addWidget(self._airflow_card)

        self._display_card = QFrame()
        self._display_card.setObjectName("section")
        display_outer = QVBoxLayout(self._display_card)
        display_outer.setContentsMargins(14, 12, 14, 12)
        display_outer.setSpacing(8)
        display_title = QLabel("Painel")
        display_title.setObjectName("title")
        display_outer.addWidget(display_title)
        display_row = QHBoxLayout()
        display_label = QLabel("Luz do painel")
        display_label.setObjectName("fieldLabel")
        display_row.addWidget(display_label)
        display_row.addStretch(1)
        self._display_light_state_label = QLabel("Indisponível")
        self._display_light_state_label.setObjectName("switchState")
        display_row.addWidget(self._display_light_state_label)
        self._display_light_switch = ModernSwitch()
        self._display_light_switch.toggled.connect(self._display_light_changed)
        display_row.addWidget(self._display_light_switch)
        display_outer.addLayout(display_row)
        self._display_card.setVisible(False)
        content.addWidget(self._display_card)

        actions = QHBoxLayout()
        self._power_button = PowerButton("⏻  Desligar")
        self._power_button.setObjectName("power")
        self._power_button.setVisible(False)
        self._power_button.clicked.connect(self._request_power_off)
        actions.addWidget(self._power_button, 1)
        content.addLayout(actions)

        self._status_label = QLabel("Aguardando conexão")
        self._status_label.setObjectName("status")
        self._status_label.setWordWrap(True)
        content.addWidget(self._status_label)

        self._build_preferences_dialog()

    def _metric_block(self, layout: QHBoxLayout, title: str, value: str) -> QLabel:
        block = QFrame()
        block.setObjectName("section")
        block_layout = QVBoxLayout(block)
        block_layout.setContentsMargins(12, 8, 12, 8)
        block_layout.setSpacing(1)
        caption = QLabel(title)
        caption.setObjectName("metric")
        block_layout.addWidget(caption)
        label = QLabel(value)
        label.setObjectName("metricValue")
        block_layout.addWidget(label)
        layout.addWidget(block, 1)
        return label

    def _build_preferences_dialog(self) -> None:
        self._preferences_dialog = QDialog(self)
        self._preferences_dialog.setObjectName("preferencesDialog")
        self._preferences_dialog.setWindowTitle("Preferências")
        self._preferences_dialog.setModal(True)
        self._preferences_dialog.setMinimumWidth(320)
        layout = QVBoxLayout(self._preferences_dialog)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        title = QLabel("Preferências")
        title.setObjectName("title")
        layout.addWidget(title)
        subtitle = QLabel("Aparência e comportamento da aplicação")
        subtitle.setObjectName("dialogSubtitle")
        layout.addWidget(subtitle)

        appearance = QFrame()
        appearance.setObjectName("section")
        appearance_layout = QHBoxLayout(appearance)
        appearance_layout.setContentsMargins(12, 10, 12, 10)
        theme_label = QLabel("Tema")
        theme_label.setObjectName("fieldLabel")
        appearance_layout.addWidget(theme_label)
        appearance_layout.addStretch(1)
        self._theme_button = QPushButton("Tema escuro")
        self._theme_button.clicked.connect(self._toggle_theme)
        appearance_layout.addWidget(self._theme_button)
        layout.addWidget(appearance)

        behavior = QFrame()
        behavior.setObjectName("section")
        behavior_layout = QVBoxLayout(behavior)
        behavior_layout.setContentsMargins(12, 10, 12, 10)
        behavior_layout.setSpacing(9)
        self._always_on_top = QCheckBox("Manter janela no topo")
        self._always_on_top.toggled.connect(self._set_always_on_top)
        behavior_layout.addWidget(self._always_on_top)
        self._startup_checkbox = QCheckBox("Iniciar com o Windows")
        self._startup_checkbox.toggled.connect(self._set_start_with_windows)
        behavior_layout.addWidget(self._startup_checkbox)
        sync_row = QHBoxLayout()
        sync_label = QLabel("Atualizar estado a cada")
        sync_label.setObjectName("fieldLabel")
        sync_row.addWidget(sync_label)
        sync_row.addStretch(1)
        self._sync_interval_spin = QSpinBox()
        self._sync_interval_spin.setRange(60, 3600)
        self._sync_interval_spin.setSingleStep(30)
        self._sync_interval_spin.setSuffix(" s")
        self._sync_interval_spin.valueChanged.connect(self._set_sync_interval)
        sync_row.addWidget(self._sync_interval_spin)
        behavior_layout.addLayout(sync_row)
        layout.addWidget(behavior)

        done_button = QPushButton("Concluído")
        done_button.clicked.connect(self._preferences_dialog.accept)
        layout.addWidget(done_button)

    def _open_preferences(self) -> None:
        self._preferences_dialog.exec()

    def _toggle_theme(self) -> None:
        self.set_theme("light" if self._dark_theme else "dark")

    def _set_always_on_top(self, enabled: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self._persist_visual_preferences(always_on_top=enabled)
        self.show()

    def _set_start_with_windows(self, enabled: bool) -> None:
        if self._startup_manager is None:
            return
        try:
            self._startup_manager.set_enabled(enabled)
        except OSError as exc:
            self._startup_checkbox.blockSignals(True)
            self._startup_checkbox.setChecked(False)
            self._startup_checkbox.blockSignals(False)
            self._render_error(f"Não foi possível alterar a inicialização: {exc}")
            return
        self._persist_visual_preferences(start_with_windows=enabled)

    def _set_sync_interval(self, seconds: int) -> None:
        if self._settings_store is None:
            return
        settings = self._settings_store.load()
        settings = replace(settings, sync_interval_seconds=max(60, int(seconds)))
        self._settings_store.save(settings)
        if self._sync_timer.isActive():
            self._sync_timer.setInterval(settings.sync_interval_seconds * 1000)

    def _persist_visual_preferences(
        self,
        *,
        theme: str | None = None,
        always_on_top: bool | None = None,
        start_with_windows: bool | None = None,
        window_geometry: str | None = None,
    ) -> None:
        if self._settings_store is None:
            return
        settings = self._settings_store.load()
        if theme is not None:
            settings = replace(settings, theme=theme)
        if always_on_top is not None:
            settings = replace(settings, always_on_top=always_on_top)
        if start_with_windows is not None:
            settings = replace(settings, start_with_windows=start_with_windows)
        if window_geometry is not None:
            settings = replace(settings, window_geometry=window_geometry)
        self._settings_store.save(settings)

    def _request_discovery(self) -> None:
        if self._controller is None:
            return
        self._start_periodic_sync()
        self._connection_indicator.set_state("syncing", "Conectando")
        self._status_label.setText("Descobrindo dispositivos...")
        self._submit(
            lambda: self._controller.discover_devices(),
            self._on_devices,
        )

    def _on_devices(self, devices: Sequence[DeviceSummary]) -> None:
        self._device_combo.blockSignals(True)
        self._device_combo.clear()
        for device in devices:
            self._device_combo.addItem(
                device.alias or device.model_name or device.device_id,
                userData=device.device_id,
            )
        selected_id = self._controller.selected_device_id if self._controller else None
        selected_index = next(
            (
                index
                for index in range(self._device_combo.count())
                if self._device_combo.itemData(index) == selected_id
            ),
            0 if len(devices) == 1 else -1,
        )
        self._device_combo.blockSignals(False)

        if selected_index >= 0:
            self._device_combo.setCurrentIndex(selected_index)
            self._device_changed(selected_index)
        elif devices:
            self._connection_indicator.set_state("connected", "Online")
            self._status_label.setText("Selecione o ar-condicionado.")
        else:
            self._connection_indicator.set_state("error", "Sem dispositivo")
            self._status_label.setText("Nenhum ar-condicionado encontrado.")

    def _device_changed(self, index: int) -> None:
        if index < 0 or self._controller is None:
            return
        device_id = self._device_combo.itemData(index)
        if not device_id:
            return
        self._status_label.setText("Selecionando dispositivo...")
        self._submit(
            lambda: self._controller.select_device(str(device_id)),
            lambda _device: self._request_refresh(),
        )

    def _request_refresh(self) -> None:
        if self._controller is None:
            return
        self._connection_indicator.set_state("syncing", "Sincronizando")
        self._status_label.setText("Atualizando estado...")
        self._submit(self._controller.refresh, self._render_snapshot)

    def _start_periodic_sync(self) -> None:
        if self._controller is None or self._settings_store is None:
            return
        settings = self._settings_store.load()
        interval_ms = max(60, settings.sync_interval_seconds) * 1000
        if self._sync_timer.interval() != interval_ms:
            self._sync_timer.setInterval(interval_ms)
        if not self._sync_timer.isActive():
            self._sync_timer.start()

    def _request_power_off(self) -> None:
        if self._controller is None:
            return
        operation = self._power_button.property("operation") or "POWER_OFF"
        action = "ligar" if operation == "POWER_ON" else "desligar"
        self._power_button.setEnabled(False)
        self._status_label.setText(
            f"{action.capitalize()}ando e confirmando..."
        )
        self._submit(
            lambda: self._controller.send_and_confirm(
                {"operation": {"airConOperationMode": operation}},
                command_name=str(operation),
                authorized=True,
            ),
            self._render_snapshot,
            lambda error: self._render_error(error),
        )

    def _render_snapshot(self, snapshot: SyncSnapshot) -> None:
        self._set_controls_enabled(True)
        if snapshot.error:
            self._render_error(snapshot.error)
            return
        if snapshot.state is not None:
            self._last_confirmed_snapshot = snapshot
        self._connection_indicator.set_state("connected", "Online")
        if snapshot.pending_command:
            self._status_label.setText(
                f"Aguardando confirmação: {snapshot.pending_command}"
            )
        elif snapshot.last_success_at is not None:
            local_time = snapshot.last_success_at.astimezone().strftime("%H:%M:%S")
            self._status_label.setText(f"Sincronizado às {local_time}")

        attributes = observed_attributes(snapshot.state.state if snapshot.state else {})
        target = _first(attributes, "targetTemperature", "targetTemperatureC")
        current = _first(attributes, "currentTemperature", "currentTemperatureC")
        self._temperature_label.setText(_format_temperature(target))
        operation = attributes.get("airConOperationMode")
        self._power_label.setText(
            f"{_power_text(operation)} · ambiente {_format_temperature(current)}"
        )
        mode = attributes.get("currentJobMode", "--")
        fan = attributes.get("windStrength", "--")
        self._mode_label.setText(_display_value(mode))
        self._fan_label.setText(_display_value(fan))
        self._glyph.set_status(
            operation,
            mode,
            fan,
            attributes.get("rotateUpDown", False),
        )

        power_values = (
            writable_enum_values(
                snapshot.capabilities.profile, "operation", "airConOperationMode"
            )
            if snapshot.capabilities
            else ()
        )
        next_power = "POWER_ON" if operation == "POWER_OFF" else "POWER_OFF"
        can_power = bool(operation in {"POWER_ON", "POWER_OFF"} and next_power in power_values)
        self._power_button.set_operation(next_power)
        self._power_button.setVisible(can_power)

        profile = snapshot.capabilities.profile if snapshot.capabilities else {}
        target_range = writable_range(profile, "temperature", "targetTemperature")
        self._target_control_label.setVisible(target_range is not None)
        self._temperature_control.setVisible(target_range is not None)
        if target_range is not None:
            minimum, maximum, step = target_range
            self._temperature_control.blockSignals(True)
            self._temperature_control.configure(minimum, maximum, step)
            if isinstance(target, (int, float)):
                self._temperature_control.set_value(float(target))
            self._temperature_control.blockSignals(False)

        mode_values = writable_enum_values(profile, "airConJobMode", "currentJobMode")
        fan_values = writable_enum_values(profile, "airFlow", "windStrength")
        self._set_combo_values(
            self._mode_control_label,
            self._mode_combo,
            mode_values,
            attributes.get("currentJobMode"),
        )
        self._set_combo_values(
            self._fan_control_label,
            self._fan_combo,
            fan_values,
            attributes.get("windStrength"),
        )
        swing_values = writable_enum_values(profile, "windDirection", "rotateUpDown")
        self._swing_available = bool(swing_values)
        self._swing_state_known = "rotateUpDown" in attributes
        self._airflow_card.setVisible(self._swing_available)
        self._swing_checkbox.setVisible(self._swing_available)
        self._swing_checkbox.set_unknown(
            self._swing_available and not self._swing_state_known
        )
        self._swing_checkbox.blockSignals(True)
        if "rotateUpDown" in attributes:
            self._swing_checkbox.setChecked(bool(attributes["rotateUpDown"]))
        self._swing_checkbox.blockSignals(False)
        self._swing_state_label.setText(
            _boolean_state_text(attributes.get("rotateUpDown"))
        )

        display_values = writable_enum_values(profile, "display", "light")
        self._display_light_available = bool(display_values)
        self._display_light_state_known = "light" in attributes
        self._display_card.setVisible(self._display_light_available)
        self._display_light_switch.setVisible(self._display_light_available)
        self._display_light_switch.set_unknown(
            self._display_light_available and not self._display_light_state_known
        )
        self._display_light_switch.blockSignals(True)
        if "light" in attributes:
            self._display_light_switch.setChecked(attributes["light"] == "ON")
        self._display_light_switch.blockSignals(False)
        self._display_light_state_label.setText(
            _light_state_text(attributes.get("light"))
        )
        self._controls_card.setVisible(
            target_range is not None
            or bool(mode_values)
            or bool(fan_values)
        )
        self._set_controls_enabled(True)

    def _set_combo_values(
        self,
        label: QLabel,
        combo: SegmentedSelector,
        values: Sequence[Any],
        current: Any,
    ) -> None:
        supported = tuple(values)
        label.setVisible(bool(supported))
        combo.blockSignals(True)
        combo.set_options(supported, current)
        combo.blockSignals(False)

    def _target_changed(self) -> None:
        if self._controller is None or not self._temperature_control.isVisible():
            return
        self._send_control(
            {"temperature": {"targetTemperature": self._temperature_control.value()}},
            "targetTemperature",
        )

    def _mode_changed(self, selection: Any) -> None:
        if self._controller is None:
            return
        value = selection if not isinstance(selection, int) else self._mode_combo.currentData()
        if value is not None:
            self._send_control({"airConJobMode": {"currentJobMode": value}}, str(value))

    def _fan_changed(self, selection: Any) -> None:
        if self._controller is None:
            return
        value = selection if not isinstance(selection, int) else self._fan_combo.currentData()
        if value is not None:
            self._send_control({"airFlow": {"windStrength": value}}, str(value))

    def _swing_changed(self, enabled: bool) -> None:
        if self._controller is not None and self._swing_state_known:
            self._send_control(
                {"windDirection": {"rotateUpDown": enabled}},
                "rotateUpDown",
            )

    def _display_light_changed(self, enabled: bool) -> None:
        if self._controller is not None and self._display_light_state_known:
            self._display_light_state_label.setText("Confirmando...")
            self._send_control(
                {"display": {"light": "ON" if enabled else "OFF"}},
                "light",
            )

    def _send_control(self, payload: dict[str, Any], command_name: str) -> None:
        self._set_controls_enabled(False)
        self._status_label.setText(
            f"Aplicando {_display_value(command_name).lower()} e confirmando..."
        )
        self._submit(
            lambda: self._controller.send_and_confirm(
                payload,
                command_name=command_name,
                authorized=True,
            ),
            self._render_snapshot,
        )

    def _set_controls_enabled(self, enabled: bool) -> None:
        self._power_button.setEnabled(enabled)
        self._target_spin.setEnabled(enabled)
        self._mode_combo.setEnabled(enabled)
        self._fan_combo.setEnabled(enabled)
        self._swing_checkbox.setEnabled(enabled and self._swing_state_known)
        self._display_light_switch.setEnabled(
            enabled and self._display_light_state_known
        )

    def _render_error(self, error: str) -> None:
        if self._last_confirmed_snapshot is not None:
            self._render_snapshot(self._last_confirmed_snapshot)
        self._set_controls_enabled(True)
        self._connection_indicator.set_state("error", "Sem conexão")
        self._status_label.setText(f"Falha: {error}")

    def _submit(
        self,
        operation: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        if self._executor is None:
            self._render_error("Executor assíncrono não configurado.")
            return
        if not self._executor_signals_connected:
            self._executor.completed.connect(self._task_completed)
            self._executor.failed.connect(self._task_failed)
            self._executor_signals_connected = True
        task_id = self._executor.submit(operation)
        self._task_handlers[task_id] = (on_success, on_error or self._render_error)

    def _task_completed(self, task_id: int, result: Any) -> None:
        if self._executor is not None:
            self._executor.discard_completed(task_id)
        handler = self._task_handlers.pop(task_id, None)
        if handler:
            handler[0](result)

    def _task_failed(self, task_id: int, error: str) -> None:
        if self._executor is not None:
            self._executor.discard_completed(task_id)
        handler = self._task_handlers.pop(task_id, None)
        if handler:
            handler[1](error)


def _first(attributes: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in attributes:
            return attributes[key]
    return None


def _format_temperature(value: Any) -> str:
    return "--" if value is None else f"{value} °C"


def _power_text(value: Any) -> str:
    return {"POWER_ON": "ligado", "POWER_OFF": "desligado"}.get(str(value), "--")


def _display_value(value: Any) -> str:
    """Translate provider enum values without changing the API payload."""

    translations = {
        "POWER_ON": "Ligado",
        "POWER_OFF": "Desligado",
        "COOL": "Resfriar",
        "HEAT": "Aquecer",
        "AIR_DRY": "Desumidificar",
        "FAN": "Ventilar",
        "AUTO": "Automático",
        "LOW": "Baixa",
        "MID": "Média",
        "HIGH": "Alta",
        "targetTemperature": "temperatura alvo",
        "currentJobMode": "modo",
        "windStrength": "ventilação",
        "rotateUpDown": "oscilação",
        "light": "luz do painel",
        "ON": "Ligado",
        "OFF": "Desligado",
        "--": "Indisponível",
    }
    return translations.get(str(value), str(value).replace("_", " ").title())


def _boolean_state_text(value: Any) -> str:
    if value is True:
        return "Ativa"
    if value is False:
        return "Desativada"
    return "Indisponível"


def _light_state_text(value: Any) -> str:
    if value == "ON":
        return "Ligada"
    if value == "OFF":
        return "Desligada"
    return "Indisponível"
