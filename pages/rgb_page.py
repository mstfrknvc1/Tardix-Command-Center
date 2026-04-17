import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
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

    RGB_MODE_OPTIONS = (
        ("static_color", "rgb_mode_static"),
        ("morph", "rgb_mode_morph"),
        ("rgb", "rgb_mode_rgb"),
        ("dual_morph", "rgb_mode_dual_morph"),
        ("windows_setting", "rgb_mode_windows_setting"),
        ("off", "rgb_mode_off"),
    )

    def _rgb_mode_key(self) -> str:
        saved_mode = self.settings.value("RGB Mode", self.settings.value("Action", "Static Color"))
        if not isinstance(saved_mode, str):
            return "static_color"

        aliases = {
            "static": "static_color",
            "static_color": "static_color",
            "morph": "morph",
            "rgb": "rgb",
            "dual_morph": "dual_morph",
            "windows_setting": "windows_setting",
            "off": "off",
        }
        normalized = saved_mode.strip().lower().replace(" ", "_")
        return aliases.get(normalized, "static_color")

    def _legacy_action_for_mode(self, mode_key: str) -> str:
        return {
            "static_color": "Static Color",
            "morph": "Morph",
            "rgb": "RGB",
            "dual_morph": "Dual Morph",
            "windows_setting": "Windows Setting",
            "off": "Off",
        }.get(mode_key, "Static Color")

    def _sync_rgb_mode_settings(self, mode_key: str):
        if mode_key != "off":
            self.settings.setValue("LastRGBMode", mode_key)
        self.settings.setValue("RGB Mode", mode_key)
        self.settings.setValue("Action", self._legacy_action_for_mode(mode_key))

    def _rgb_mode_label(self, mode_key: str) -> str:
        return self.tr(f"rgb_mode_{mode_key}")

    def _current_rgb_action_label(self) -> str:
        return self._rgb_mode_label(self._rgb_mode_key())

    def _stabilize_rgb_layout(self):
        metrics_source = self.rgb_mode or self.window
        if metrics_source is None:
            return
        metrics = metrics_source.fontMetrics()

        label_widths = [
            metrics.horizontalAdvance(f"{self.tr('rgb_target_static')}: #FFFFFF"),
            metrics.horizontalAdvance(f"{self.tr('rgb_target_morph')}: #FFFFFF"),
        ]
        label_min_width = max(label_widths) + 16
        value_min_width = metrics.horizontalAdvance("100%") + 16
        mode_min_width = max(
            metrics.horizontalAdvance(self.tr(label_key))
            for _, label_key in self.RGB_MODE_OPTIONS
        ) + 48

        if self.rgb_label_static:
            self.rgb_label_static.setMinimumWidth(label_min_width)
        if self.rgb_label_morph:
            self.rgb_label_morph.setMinimumWidth(label_min_width)
        if self.static_hex_label:
            self.static_hex_label.setMinimumWidth(metrics.horizontalAdvance("#FFFFFF") + 16)
        if self.morph_hex_label:
            self.morph_hex_label.setMinimumWidth(metrics.horizontalAdvance("#FFFFFF") + 16)
        if self.brightness_value_label:
            self.brightness_value_label.setMinimumWidth(value_min_width)
        if hasattr(self, "duration_value"):
            self.duration_value.setMinimumWidth(value_min_width)
        if self.rgb_mode:
            self.rgb_mode.setMinimumContentsLength(18)
            self.rgb_mode.setMinimumWidth(mode_min_width)
            self.rgb_mode.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            self.rgb_mode.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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

        current_mode = self._rgb_mode_key()

        # Block signals during combo reinit to avoid saving empty action string
        self.rgb_mode.blockSignals(True)
        self.rgb_mode.clear()
        for mode_key, label_key in self.RGB_MODE_OPTIONS:
            self.rgb_mode.addItem(self.tr(label_key), mode_key)
        current_index = self.rgb_mode.findData(current_mode)
        self.rgb_mode.setCurrentIndex(0 if current_index < 0 else current_index)
        self.rgb_mode.blockSignals(False)
        self._sync_rgb_mode_settings(current_mode)

        self._rgb_target   = self.settings.value("RGB Target", "Static")
        self._rgb_static   = QColor(self.settings.value("RGB Static",  "#7a7a7a"))
        self._rgb_morph    = QColor(self.settings.value("RGB Morph",   "#7a7a7a"))
        self._rgb_duration = int(self.settings.value("Duration", 3500))
        self._rgb_dim      = int(self.settings.value("RGB Dim",   0))

        if self.brightness_slider and self.brightness_value_label:
            self.brightness_slider.blockSignals(True)
            self.brightness_slider.setValue(100 - self._rgb_dim)
            self.brightness_slider.blockSignals(False)
            self.brightness_value_label.setText(f"{100 - self._rgb_dim}%")

        if self.keyboard_preview:
            path = os.path.join(self.script_dir, "assets", "keyboard_preview.svg")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._keyboard_svg_template = f.read()
            except OSError:
                self._keyboard_svg_template = ""
            self._update_keyboard_preview_tint()
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
                self._duration_row = duration_row
                dur_layout = QHBoxLayout(duration_row)
                dur_layout.setContentsMargins(0, 0, 0, 0)
                self._duration_label_widget = QLabel(self.tr("speed"), duration_row)
                dur_layout.addWidget(self._duration_label_widget)
                _dur_init = max(3000, min(4095, self._rgb_duration))
                speed_pct_init = int(round((4095 - _dur_init) / (4095 - 3000) * 100))
                self.duration_slider = QSlider(Qt.Horizontal, duration_row)
                self.duration_slider.setRange(0, 100)
                self.duration_slider.setSingleStep(1)
                self.duration_slider.setPageStep(10)
                self.duration_slider.setValue(speed_pct_init)
                self.duration_value = QLabel(f"{speed_pct_init}%", duration_row)
                self.duration_value.setMinimumWidth(48)
                dur_layout.addWidget(self.duration_slider, 1)
                dur_layout.addWidget(self.duration_value)
                layout.addWidget(duration_row)

                self.apply_button = QPushButton(self.tr("apply"), container)
                layout.addWidget(self.apply_button)

                self.duration_slider.valueChanged.connect(self._on_duration_changed)
                self.apply_button.clicked.connect(self.apply_leds)
                container.setMinimumHeight(160)
            else:
                # Retranslate existing widgets only
                if hasattr(self, "_duration_label_widget"):
                    self._duration_label_widget.setText(self.tr("speed"))
                if hasattr(self, "apply_button"):
                    self.apply_button.setText(self.tr("apply"))

        # — Signals (connected once only) ————————————————————————————————————
        if not getattr(self, "_rgb_signals_connected", False):
            self._rgb_signals_connected = True
            self.rgb_mode.currentTextChanged.connect(self._on_mode_changed)
            self.color_wheel.colorChanged.connect(self._on_color_changed)
            if self.brightness_slider:
                # Update label in real-time but only save on release
                self.brightness_slider.valueChanged.connect(self._on_dim_value_changed)
                self.brightness_slider.sliderReleased.connect(self._on_dim_save)

        self._sync_speed_visibility()
        self._stabilize_rgb_layout()
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
        if self.color_wheel:
            self.color_wheel.setColor(
                self._rgb_static if target == "Static" else self._rgb_morph
            )

    def _select_color_from_swatch(self, target: str):
        """Select *target* and sync the color wheel to that color."""
        self._set_rgb_target(target)
        # _set_rgb_target already calls color_wheel.setColor(); no duplicate needed.

    def _make_swatch_handler(self, target: str):
        def handler(event):
            self._select_color_from_swatch(target)
        return handler  # kept for compatibility

    def _refresh_rgb_labels(self):
        static_hex = self._rgb_static.name()
        morph_hex  = self._rgb_morph.name()
        if self.rgb_label_static:
            self.rgb_label_static.setText(f"{self.tr('rgb_target_static')}: {static_hex}")
        if self.rgb_label_morph:
            self.rgb_label_morph.setText(f"{self.tr('rgb_target_morph')}: {morph_hex}")

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
        self._update_keyboard_preview_tint()

    def _update_keyboard_preview_tint(self):
        if not self.keyboard_preview:
            return
        mode = self._rgb_mode_key()
        if mode == "morph":
            tint = self._rgb_morph
        elif mode == "rgb":
            tint = QColor(255, 0, 0)  # Red for RGB mode preview
        elif mode == "dual_morph":
            tint = QColor(
                (self._rgb_static.red() + self._rgb_morph.red()) // 2,
                (self._rgb_static.green() + self._rgb_morph.green()) // 2,
                (self._rgb_static.blue() + self._rgb_morph.blue()) // 2,
            )
        else:
            tint = self._rgb_static
        if not getattr(self, "_keyboard_svg_template", ""):
            return

        svg = self._keyboard_svg_template.replace("__KEY_COLOR__", tint.name())
        data = svg.encode("utf-8")
        renderer = QSvgRenderer(data)
        if not renderer.isValid():
            return

        width = max(1, self.keyboard_preview.width())
        height = max(1, self.keyboard_preview.height())
        pm = QPixmap(width, height)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        renderer.render(p)
        p.end()
        self.keyboard_preview.setPixmap(pm)

    def _sync_speed_visibility(self):
        needs_speed = self._rgb_mode_key() in {"morph", "rgb", "dual_morph"}
        if hasattr(self, "_duration_row") and self._duration_row:
            self._duration_row.setEnabled(needs_speed)
            self._duration_row.setVisible(True)
        if hasattr(self, "duration_slider"):
            self.duration_slider.setEnabled(needs_speed)

    def _on_mode_changed(self, _text: str):
        mode_key = self.rgb_mode.currentData() if self.rgb_mode else None
        if isinstance(mode_key, str) and mode_key:
            self._sync_rgb_mode_settings(mode_key)
            if mode_key == "morph":
                self._set_rgb_target("Morph")
            elif mode_key == "static_color":
                self._set_rgb_target("Static")
        self._sync_speed_visibility()
        self._update_keyboard_preview_tint()

    def _on_color_changed(self, new_color: QColor):
        if self._rgb_target == "Morph":
            self._rgb_morph = new_color
            self.settings.setValue("RGB Morph", new_color.name())
        else:
            self._rgb_static = new_color
            self.settings.setValue("RGB Static", new_color.name())
        self._refresh_rgb_labels()
        self._refresh_selected_color_previews()

    def _on_dim_value_changed(self, value: int):
        """Update brightness label in real-time while sliding (no saving)."""
        if self.brightness_value_label:
            self.brightness_value_label.setText(f"{value}%")

    def _on_dim_save(self):
        """Save brightness setting only when slider is released."""
        if not self.brightness_slider:
            return
        value = self.brightness_slider.value()
        # value = brightness (0=off, 100=full); internally stored as dim (inverted)
        actual_dim = 100 - value
        self._rgb_dim = actual_dim
        self.settings.setValue("RGB Dim", actual_dim)
        if awelc is not None:
            try:
                awelc.set_dim(actual_dim)
            except Exception:
                pass

    def _on_duration_changed(self, value: int):
        # Slider is "speed %" where 0 = slowest, 100 = fastest (still intentionally slow).
        speed_pct = max(0, min(100, int(value)))
        duration = int(round(4095 - (speed_pct / 100.0) * (4095 - 3000)))
        self._rgb_duration = duration
        self.settings.setValue("Duration", duration)
        if hasattr(self, "duration_value"):
            self.duration_value.setText(f"{speed_pct}%")
