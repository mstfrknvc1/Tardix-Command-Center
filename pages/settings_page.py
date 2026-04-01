from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.i18n import TRANSLATIONS
from core.utils import _clear_layout


class SettingsMixin:
    """Settings page UI logic."""

    def _init_settings_page(self):
        settings_page = self.window.findChild(QWidget, "settings")
        if not settings_page:
            return

        layout = settings_page.layout()
        if layout:
            _clear_layout(layout)
        else:
            layout = QVBoxLayout(settings_page)

        perf_group = QGroupBox(self.tr("performance"), settings_page)
        perf_layout = QVBoxLayout(perf_group)
        self.turbo_boost_toggle = QCheckBox(self.tr("disable_turbo"), settings_page)
        self.turbo_boost_toggle.setChecked(
            self.settings.value("DisableTurboBoost", "false") == "true"
        )
        self.turbo_boost_toggle.toggled.connect(self._on_turbo_boost_toggled)
        perf_layout.addWidget(self.turbo_boost_toggle)
        perf_layout.addWidget(QLabel(self.tr("turbo_note"), settings_page))
        layout.addWidget(perf_group)

        thermal_group = QGroupBox(self.tr("thermals"), settings_page)
        thermal_layout = QHBoxLayout(thermal_group)
        thermal_layout.addWidget(QLabel(self.tr("temp_limit"), settings_page))
        self.temp_limit_slider = QSlider(Qt.Horizontal, settings_page)
        self.temp_limit_slider.setRange(85, 100)
        limit = max(85, min(100, int(self.settings.value("TempLimitC", 95))))
        self.temp_limit_slider.setValue(limit)
        self.temp_limit_slider.valueChanged.connect(self._on_temp_limit_changed)
        thermal_layout.addWidget(self.temp_limit_slider, 1)
        self.temp_limit_value = QLabel(f"{limit}\u00b0C", settings_page)
        thermal_layout.addWidget(self.temp_limit_value)
        layout.addWidget(thermal_group)

        lang_group = QGroupBox(self.tr("language"), settings_page)
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.addWidget(QLabel(self.tr("select_language"), settings_page))
        self.language_combo = QComboBox(settings_page)
        self.language_combo.addItems(["T\u00fcrk\u00e7e", "English"])
        self.language_combo.setCurrentText(self._current_lang)
        self.language_combo.currentTextChanged.connect(self._on_language_changed_handler)
        lang_layout.addWidget(self.language_combo, 1)
        layout.addWidget(lang_group)

        layout.addStretch()

    def _on_language_changed_handler(self, language: str):
        if language not in TRANSLATIONS:
            return
        self._current_lang = language
        self.settings.setValue("Language", language)
        self._temp_warning_shown = False
        self._retranslate_chrome()
        self._init_home_page()
        self._init_rgb_page()
        self._init_fan_power_page()
        self._init_settings_page()
        self._init_info_page()
        self._init_macro_page()

    def _on_turbo_boost_toggled(self, checked: bool):
        self.settings.setValue("DisableTurboBoost", "true" if checked else "false")

    def _on_temp_limit_changed(self, value: int):
        value = max(85, min(100, int(value)))
        self.settings.setValue("TempLimitC", value)
        if hasattr(self, "temp_limit_value") and self.temp_limit_value:
            self.temp_limit_value.setText(f"{value}\u00b0C")
