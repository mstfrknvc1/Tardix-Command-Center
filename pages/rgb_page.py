import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from widgets.color_wheel import ColorWheel
from core.utils import _ClickFilter

try:
    from hardware import awelc  # type: ignore
except (ModuleNotFoundError, ImportError):
    awelc = None


class RGBMixin:
    """RGB page UI logic."""

    def _init_rgb_page(self):
        self.rgb_mode               = self.window.findChild(QComboBox,  "comboBox")
        self.rgb_label_static       = self.window.findChild(QLabel,     "label_2")
        self.rgb_label_morph        = self.window.findChild(QLabel,     "label_3")
        self.color_wheel            = self.window.findChild(ColorWheel, "colorwheel")
        self.keyboard_preview       = self.window.findChild(QLabel,     "keyboardPreviewLabel")
        self.static_swatch          = self.window.findChild(QWidget,    "selectedStaticSwatch")
        self.morph_swatch           = self.window.findChild(QWidget,    "selectedMorphSwatch")
        self.static_hex_label       = self.window.findChild(QLabel,     "selectedStaticHex")
        self.morph_hex_label        = self.window.findChild(QLabel,     "selectedMorphHex")
        self.brightness_slider      = self.window.findChild(QSlider,    "brightnessSlider")
        self.brightness_value_label = self.window.findChild(QLabel,     "brightnessValueLabel")

        if not (self.rgb_mode and self.rgb_label_static and self.rgb_label_morph and self.color_wheel):
            return

        # Block signals during combo reinit to avoid saving empty action string
        self.rgb_mode.blockSignals(True)
        self.rgb_mode.clear()
        self.rgb_mode.addItems(["Static Color", "Morph", "Color and Morph", "Off"])
        self.rgb_mode.setCurrentText(self.settings.value("Action", "Static Color"))
        self.rgb_mode.blockSignals(False)

        self._rgb_target   = self.settings.value("RGB Target", "Static")
        self._rgb_static   = QColor(self.settings.value("RGB Static",  "#7a7a7a"))
        self._rgb_morph    = QColor(self.settings.value("RGB Morph",   "#7a7a7a"))
        self._rgb_duration = int(self.settings.value("Duration", 255))
        self._rgb_dim      = int(self.settings.value("RGB Dim",   0))

        if self.brightness_slider and self.brightness_value_label:
            self.brightness_slider.blockSignals(True)
            self.brightness_slider.setValue(self._rgb_dim)
            self.brightness_slider.blockSignals(False)
            self.brightness_value_label.setText(f"{self._rgb_dim}%")

        if self.keyboard_preview:
            path = os.path.join(self.script_dir, "assets", "keyboard_preview.svg")
            pm = QPixmap(path)
            if not pm.isNull():
                self.keyboard_preview.setPixmap(pm)
                self.keyboard_preview.setScaledContents(True)

        # — Event filters for label + swatch clicks (installed once only) ——————
        if not hasattr(self, "_static_label_filter"):
            self._static_label_filter = _ClickFilter(
                lambda: self._set_rgb_target("Static"), self.rgb_label_static
            )
            self.rgb_label_static.installEventFilter(self._static_label_filter)

        if not hasattr(self, "_morph_label_filter"):
            self._morph_label_filter = _ClickFilter(
                lambda: self._set_rgb_target("Morph"), self.rgb_label_morph
            )
            self.rgb_label_morph.installEventFilter(self._morph_label_filter)

        if self.static_swatch and not hasattr(self, "_static_swatch_filter"):
            self.static_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
            self._static_swatch_filter = _ClickFilter(
                lambda: self._select_color_from_swatch("Static"), self.static_swatch
            )
            self.static_swatch.installEventFilter(self._static_swatch_filter)

        if self.morph_swatch and not hasattr(self, "_morph_swatch_filter"):
            self.morph_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
            self._morph_swatch_filter = _ClickFilter(
                lambda: self._select_color_from_swatch("Morph"), self.morph_swatch
            )
            self.morph_swatch.installEventFilter(self._morph_swatch_filter)

        # — Duration slider + Apply button (created once, text updated on retranslate) —
        container = self.rgb_mode.parentWidget()
        if container:
            layout = container.layout()
            if layout is None:
                layout = QVBoxLayout(container)
                container.setLayout(layout)

            if not getattr(self, "_rgb_extra_built", False):
                self._rgb_extra_built = True

                duration_row = QWidget(container)
                dur_layout = QHBoxLayout(duration_row)
                dur_layout.setContentsMargins(0, 0, 0, 0)
                self._duration_label_widget = QLabel(self.tr("duration"), duration_row)
                dur_layout.addWidget(self._duration_label_widget)
                self.duration_slider = QSlider(Qt.Horizontal, duration_row)
                self.duration_slider.setRange(0x4, 0xFFF)
                self.duration_slider.setValue(self._rgb_duration)
                self.duration_value = QLabel(str(self._rgb_duration), duration_row)
                dur_layout.addWidget(self.duration_slider, 1)
                dur_layout.addWidget(self.duration_value)
                layout.addWidget(duration_row)

                self.apply_button = QPushButton(self.tr("apply"), container)
                layout.addWidget(self.apply_button)

                self.duration_slider.valueChanged.connect(self._on_duration_changed)
                self.apply_button.clicked.connect(self.apply_leds)
            else:
                # Retranslate existing widgets only
                if hasattr(self, "_duration_label_widget"):
                    self._duration_label_widget.setText(self.tr("duration"))
                if hasattr(self, "apply_button"):
                    self.apply_button.setText(self.tr("apply"))

        # — Signals (connected once only) ————————————————————————————————————
        if not getattr(self, "_rgb_signals_connected", False):
            self._rgb_signals_connected = True
            self.rgb_mode.currentTextChanged.connect(
                lambda text: self.settings.setValue("Action", text) if text else None
            )
            self.color_wheel.colorChanged.connect(self._on_color_changed)
            if self.brightness_slider:
                self.brightness_slider.valueChanged.connect(self._on_dim_changed)

        self._refresh_rgb_labels()
        self._refresh_selected_color_previews()
        self.color_wheel.setColor(
            self._rgb_static if self._rgb_target == "Static" else self._rgb_morph
        )

    def _set_rgb_target(self, target: str):
        self._rgb_target = target
        self.settings.setValue("RGB Target", target)
        self._refresh_rgb_labels()
        self._refresh_selected_color_previews()

    def _select_color_from_swatch(self, target: str):
        """Select *target* and sync the color wheel to that color."""
        self._set_rgb_target(target)
        self.color_wheel.setColor(
            self._rgb_static if target == "Static" else self._rgb_morph
        )

    def _make_swatch_handler(self, target: str):
        def handler(event):
            self._select_color_from_swatch(target)
        return handler  # kept for compatibility

    def _refresh_rgb_labels(self):
        static_hex = self._rgb_static.name()
        morph_hex  = self._rgb_morph.name()
        sel_s = " (selected)" if self._rgb_target == "Static" else ""
        sel_m = " (selected)" if self._rgb_target == "Morph"  else ""
        if self.rgb_label_static:
            self.rgb_label_static.setText(f"Static: {static_hex}{sel_s}")
        if self.rgb_label_morph:
            self.rgb_label_morph.setText(f"Morph:  {morph_hex}{sel_m}")

    def _refresh_selected_color_previews(self):
        static_border = "#00ff9d" if self._rgb_target == "Static" else "#1C3F95"
        morph_border  = "#00ff9d" if self._rgb_target == "Morph"  else "#1C3F95"
        if self.static_swatch and self.static_hex_label:
            hex_ = self._rgb_static.name()
            self.static_hex_label.setText(hex_)
            self.static_swatch.setStyleSheet(
                f"background-color: {hex_}; border-radius: 8px; border: 3px solid {static_border};"
            )
        if self.morph_swatch and self.morph_hex_label:
            hex_ = self._rgb_morph.name()
            self.morph_hex_label.setText(hex_)
            self.morph_swatch.setStyleSheet(
                f"background-color: {hex_}; border-radius: 8px; border: 3px solid {morph_border};"
            )

    def _on_color_changed(self, new_color: QColor):
        if self._rgb_target == "Morph":
            self._rgb_morph = new_color
            self.settings.setValue("RGB Morph", new_color.name())
        else:
            self._rgb_static = new_color
            self.settings.setValue("RGB Static", new_color.name())
        self._refresh_rgb_labels()
        self._refresh_selected_color_previews()

    def _on_dim_changed(self, value: int):
        self._rgb_dim = value
        self.settings.setValue("RGB Dim", value)
        if self.brightness_value_label:
            self.brightness_value_label.setText(f"{value}%")
        if awelc is not None:
            try:
                awelc.set_dim(value)
            except Exception:
                pass

    def _on_duration_changed(self, value: int):
        self._rgb_duration = value
        self.settings.setValue("Duration", value)
        if hasattr(self, "duration_value"):
            self.duration_value.setText(str(value))
