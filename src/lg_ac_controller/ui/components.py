"""Componentes visuais reutilizáveis do widget LG AC Controller."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import QPoint, QPointF, QRectF, QTimer, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class DragBar(QFrame):
    """Barra de título sem moldura que permite mover a janela."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._drag_offset: QPoint | None = None
        self.setFixedHeight(34)

    def mousePressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        self._drag_offset = None
        super().mouseReleaseEvent(event)


class TemperatureControl(QWidget):
    """Controle de temperatura com botões arredondados e debounce curto."""

    valueChanged = Signal(float)
    editingFinished = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum = 0.0
        self._maximum = 100.0
        self._step = 1.0
        self._value = 0.0
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(220)
        self._debounce.timeout.connect(lambda: self.editingFinished.emit(self._value))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._minus_button = QPushButton("−")
        self._minus_button.setObjectName("roundButton")
        self._minus_button.setToolTip("Diminuir temperatura")
        self._minus_button.clicked.connect(lambda: self._nudge(-1))
        layout.addWidget(self._minus_button)
        self._value_label = QLabel("-- °C")
        self._value_label.setObjectName("temperatureControlValue")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value_label.setMinimumWidth(92)
        layout.addWidget(self._value_label, 1)
        self._plus_button = QPushButton("+")
        self._plus_button.setObjectName("roundButton")
        self._plus_button.setToolTip("Aumentar temperatura")
        self._plus_button.clicked.connect(lambda: self._nudge(1))
        layout.addWidget(self._plus_button)
        self.setMinimumHeight(40)

    def configure(self, minimum: float, maximum: float, step: float) -> None:
        self._minimum = float(minimum)
        self._maximum = float(maximum)
        self._step = max(float(step), 0.1)
        self._update_buttons()

    def set_value(self, value: float, *, emit: bool = False) -> None:
        self._value = self._clamp(float(value))
        self._render_value()
        self._update_buttons()
        if emit:
            self.valueChanged.emit(self._value)

    def value(self) -> float:
        return self._value

    # Compatibility helpers keep the old widget contract usable by tests/callers.
    def setRange(self, minimum: float, maximum: float) -> None:  # noqa: N802
        self.configure(minimum, maximum, self._step)

    def setSingleStep(self, step: float) -> None:  # noqa: N802
        self._step = max(float(step), 0.1)

    def setValue(self, value: float) -> None:  # noqa: N802
        self.set_value(value, emit=False)

    def _nudge(self, direction: int) -> None:
        self.set_value(self._value + direction * self._step, emit=True)
        self._debounce.start()

    def _clamp(self, value: float) -> float:
        value = min(self._maximum, max(self._minimum, value))
        decimals = 1 if self._step < 1 or self._step % 1 else 0
        return round(value, decimals)

    def _render_value(self) -> None:
        if self._step < 1 or self._step % 1:
            text = f"{self._value:.1f} °C"
        else:
            text = f"{self._value:.0f} °C"
        self._value_label.setText(text)

    def _update_buttons(self) -> None:
        self._minus_button.setEnabled(self._value > self._minimum)
        self._plus_button.setEnabled(self._value < self._maximum)

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802 - Qt API name
        super().setEnabled(enabled)
        self._update_buttons()


class SegmentedSelector(QWidget):
    """Seletor de chips segmentados que preserva o valor cru da API."""

    valueChanged = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)
        self._values: list[Any] = []
        self._buttons: list[QPushButton] = []
        self._current_index = -1
        self._updating = False
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_options(self, values: Sequence[Any], current: Any = None) -> None:
        self._updating = True
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._buttons.clear()
        self._values = list(values)
        self._current_index = -1
        for index, value in enumerate(self._values):
            button = QPushButton(_display_value(value))
            button.setObjectName("segmentButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked, i=index: self._select(i, True))
            self._buttons.append(button)
            self._layout.addWidget(button, 1)
        if current in self._values:
            self._current_index = self._values.index(current)
        elif self._values:
            self._current_index = 0
        self._refresh_selection()
        self._updating = False
        self.setVisible(bool(self._values))

    def currentData(self) -> Any:  # noqa: N802
        return self._values[self._current_index] if self._current_index >= 0 else None

    def currentIndex(self) -> int:  # noqa: N802
        return self._current_index

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        self._select(index, False)

    def itemText(self, index: int) -> str:  # noqa: N802
        return self._buttons[index].text()

    def itemData(self, index: int) -> Any:  # noqa: N802
        return self._values[index]

    def count(self) -> int:
        return len(self._values)

    def _select(self, index: int, emit: bool) -> None:
        if not 0 <= index < len(self._values):
            return
        self._current_index = index
        self._refresh_selection()
        if emit and not self._updating:
            self.valueChanged.emit(self._values[index])

    def _refresh_selection(self) -> None:
        for index, button in enumerate(self._buttons):
            button.blockSignals(True)
            button.setChecked(index == self._current_index)
            button.blockSignals(False)


class ModernSwitch(QAbstractButton):
    """Switch compacto desenhado com QPainter, sem checkbox nativa."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dark = False
        self._unknown = False
        self._knob_x = 4.0
        self._knob_animation = QVariantAnimation(self)
        self._knob_animation.setDuration(180)
        self._knob_animation.valueChanged.connect(self._set_knob_x)
        self.toggled.connect(self._animate_knob)
        self.setFixedSize(48, 28)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.update()

    def set_unknown(self, unknown: bool) -> None:
        """Render an unavailable state without guessing a boolean value."""

        self._unknown = unknown
        if unknown:
            self._knob_animation.stop()
            self._knob_x = 15.0
        else:
            self._knob_x = 28.0 if self.isChecked() else 4.0
        self.update()

    def hitButton(self, position: Any) -> bool:  # noqa: N802 - Qt API name
        return self.rect().contains(position)

    def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(1, 4, 46, 20)
        if self._unknown:
            track_color = QColor("#718499" if self._dark else "#c6d0da")
        elif self.isChecked():
            track_color = QColor("#20a8c9")
        else:
            track_color = QColor("#607488" if self._dark else "#bdc9d5")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track, 10, 10)
        knob = QRectF(self._knob_x, 7, 14, 14)
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(knob)
        painter.end()

    def _animate_knob(self, checked: bool) -> None:
        self._knob_animation.stop()
        self._knob_animation.setStartValue(self._knob_x)
        self._knob_animation.setEndValue(28.0 if checked else 4.0)
        self._knob_animation.start()

    def _set_knob_x(self, value: Any) -> None:
        self._knob_x = float(value)
        self.update()


class PowerButton(QPushButton):
    """Botão de potência com ícone textual e estado visual."""

    def set_operation(self, operation: Any) -> None:
        self.setProperty("operation", operation)
        is_on_action = operation == "POWER_ON"
        self.setProperty("off", "false" if is_on_action else "true")
        self.setText("⏻  Ligar" if is_on_action else "⏻  Desligar")
        self.style().unpolish(self)
        self.style().polish(self)


class ConnectionIndicator(QFrame):
    """Indicador discreto de conexão, sincronização ou falha."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("connectionIndicator")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(4)
        self._dot = QLabel("●")
        self._dot.setObjectName("connectionDot")
        layout.addWidget(self._dot)
        self._text = QLabel("Offline")
        self._text.setObjectName("connectionText")
        layout.addWidget(self._text)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(420)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_on = True
        self.set_state("idle", "Offline")

    def set_state(self, state: str, text: str) -> None:
        self.setProperty("state", state)
        self._dot.setProperty("state", state)
        self._text.setText(text)
        if state == "syncing":
            if not self._pulse_timer.isActive():
                self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._dot.setText("●")
        for widget in (self, self._dot, self._text):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _pulse(self) -> None:
        self._pulse_on = not self._pulse_on
        self._dot.setText("●" if self._pulse_on else "·")


class AirConditionerGlyph(QWidget):
    """Ilustração vetorial animada baseada no estado confirmado do aparelho."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._power = "POWER_OFF"
        self._mode = ""
        self._fan = ""
        self._swing = False
        self._dark = False
        self._phase = 0.0
        self._motion_enabled = True
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(80)
        self._animation_timer.timeout.connect(self._tick)
        self.setMinimumSize(122, 96)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        self.update()

    def set_motion_enabled(self, enabled: bool) -> None:
        self._motion_enabled = enabled
        self._update_animation()

    def set_status(self, power: Any, mode: Any, fan: Any, swing: Any) -> None:
        self._power = str(power or "")
        self._mode = str(mode or "")
        self._fan = str(fan or "")
        self._swing = bool(swing)
        self._update_animation()
        self.update()

    def showEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        super().showEvent(event)
        self._update_animation()

    def hideEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        self._animation_timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event: Any) -> None:  # noqa: N802 - Qt API name
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        accent = self._accent()
        unit = QRectF(12, 19, 98, 36)
        gradient = QLinearGradient(unit.topLeft(), unit.bottomRight())
        gradient.setColorAt(0, QColor(accent).lighter(145 if not self._is_off() else 120))
        gradient.setColorAt(1, QColor(accent).darker(115 if not self._is_off() else 125))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(unit, 15, 15)
        painter.setBrush(QColor(255, 255, 255, 92 if not self._is_off() else 45))
        painter.drawRoundedRect(QRectF(23, 29, 76, 7), 3.5, 3.5)
        painter.setPen(QPen(QColor(255, 255, 255, 150 if not self._is_off() else 65), 2))
        painter.drawLine(QPointF(29, 46), QPointF(93, 46))
        painter.setPen(QPen(QColor(accent).darker(145), 2))
        for x in (35, 47, 59, 71, 83):
            painter.drawLine(QPointF(x, 49), QPointF(x + 2, 53))

        wave_pen = QPen(
            QColor(accent).lighter(135),
            2.4,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(wave_pen)
        if not self._is_off():
            count = {"LOW": 1, "MID": 2, "HIGH": 3, "AUTO": 3}.get(self._fan, 2)
            for index in range(count):
                x = 30 + index * 23 + ((self._phase + index * 2) % 8)
                path = QPainterPath(QPointF(x, 65))
                path.cubicTo(QPointF(x - 5, 72), QPointF(x + 8, 77), QPointF(x + 2, 86))
                painter.drawPath(path)
            if self._mode == "AIR_DRY":
                painter.setBrush(QColor(accent).lighter(125))
                for x in (46, 62, 78):
                    y = 65 + ((self._phase + x) % 10)
                    painter.drawEllipse(QPointF(x, y), 2.2, 2.2)
            if self._swing:
                painter.drawArc(QRectF(48, 59, 28, 25), 205 * 16, 130 * 16)
                painter.drawLine(QPointF(73, 65), QPointF(78, 63))
        else:
            painter.setPen(
                QPen(
                    QColor(accent).lighter(125),
                    2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                )
            )
            painter.drawLine(QPointF(46, 70), QPointF(76, 70))
            painter.drawLine(QPointF(53, 78), QPointF(69, 78))
        painter.end()

    def _tick(self) -> None:
        self._phase = (self._phase + 1.0) % 16.0
        self.update()

    def _update_animation(self) -> None:
        should_run = self._motion_enabled and not self._is_off() and self.isVisible()
        if should_run and not self._animation_timer.isActive():
            self._animation_timer.start()
        elif not should_run:
            self._animation_timer.stop()

    def _is_off(self) -> bool:
        return self._power != "POWER_ON"

    def _accent(self) -> str:
        if self._is_off():
            return "#74869a" if self._dark else "#a7b6c4"
        return {
            "COOL": "#21a8d0",
            "HEAT": "#e29b47",
            "AIR_DRY": "#8b7de0",
            "FAN": "#6caeb5",
        }.get(self._mode, "#40b8aa")


def _display_value(value: Any) -> str:
    translations = {
        "COOL": "Resfriar",
        "HEAT": "Aquecer",
        "AIR_DRY": "Desumidificar",
        "FAN": "Ventilar",
        "AUTO": "Automático",
        "LOW": "Baixa",
        "MID": "Média",
        "HIGH": "Alta",
        "POWER_ON": "Ligado",
        "POWER_OFF": "Desligado",
    }
    return translations.get(str(value), str(value).replace("_", " ").title())
