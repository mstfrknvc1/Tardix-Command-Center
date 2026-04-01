#!/usr/bin/env python3
import sys
import os

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, QSettings
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from widgets.color_wheel import ColorWheel
from widgets.fan_widget import FanWidget
from widgets.temperature_gauge import TemperatureGauge
from core.i18n import TRANSLATIONS

from pages.home_page import HomeMixin
from pages.rgb_page import RGBMixin
from pages.fan_page import FanMixin
from pages.settings_page import SettingsMixin
from pages.info_page import InfoMixin
from pages.macro_page import MacroMixin
from core.led_control import LEDMixin
from core.acpi import ACPIMixin
from core.tray import TrayIcon


class TardixApp(HomeMixin, RGBMixin, FanMixin, SettingsMixin,
                InfoMixin, MacroMixin, LEDMixin, ACPIMixin):
    """Main application controller – loads main.ui and wires all pages."""

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self._load_ui()

    # ──────────────────────────────────────────────────────────
    # Translation helper
    # ──────────────────────────────────────────────────────────
    def tr(self, key: str, **kwargs):
        lang = getattr(self, "_current_lang", "Türkçe")
        table = TRANSLATIONS.get(lang, TRANSLATIONS["Türkçe"])
        val = table.get(key, TRANSLATIONS["Türkçe"].get(key, key))
        if kwargs and isinstance(val, str):
            try:
                val = val.format(**kwargs)
            except KeyError:
                pass
        return val

    def _load_ui(self):
        loader = QUiLoader()
        loader.registerCustomWidget(ColorWheel)
        loader.registerCustomWidget(FanWidget)
        loader.registerCustomWidget(TemperatureGauge)

        ui_path = os.path.join(self.script_dir, "main.ui")
        ui_file = QFile(ui_path)
        if not ui_file.open(QIODevice.ReadOnly):
            raise RuntimeError(f"main.ui dosyası açılamadı: {ui_file.errorString()}")

        self.window = loader.load(ui_file)
        ui_file.close()

        if not self.window:
            raise RuntimeError(loader.errorString())

        for icon_name in ["icon.png", "logo.png", "tardix.png", "atom.png"]:
            icon_path = os.path.join(self.script_dir, "Design", "png", icon_name)
            if os.path.exists(icon_path):
                self.window.setWindowIcon(QIcon(icon_path))
                break

        self.settings = QSettings("Tardix", "CommandCenter")

        # Language must be initialised first so tr() works everywhere below
        self._current_lang = self.settings.value("Language", "Türkçe")

        self.is_dell_g_series = False
        self.is_keyboard_supported = True
        self.model = "Unknown"
        self.timer = None

        try:
            self.logfile = open("/tmp/tardix-command-center.log", "w")
        except Exception:
            self.logfile = None

        self.init_acpi_call()

        self.main_stack    = self.window.findChild(QStackedWidget, "stackedWidget")
        self.btn_home      = self.window.findChild(QPushButton, "homebutton")
        self.btn_fan       = self.window.findChild(QPushButton, "fanbutton")
        self.btn_rgb       = self.window.findChild(QPushButton, "rgbbutton")
        self.btn_macro     = self.window.findChild(QPushButton, "macrobutton")
        self.btn_settings  = self.window.findChild(QPushButton, "settingsbutton")
        self.btn_info      = self.window.findChild(QPushButton, "infobutton")

        if self.main_stack:
            page_home     = self.window.findChild(QWidget, "ahome")
            page_fan      = self.window.findChild(QWidget, "bfancontrol")
            page_rgb      = self.window.findChild(QWidget, "rgbcontrol")
            page_macro    = self.window.findChild(QWidget, "macropage")
            page_settings = self.window.findChild(QWidget, "settings")
            page_info     = self.window.findChild(QWidget, "zinfo")

            def _go(page):
                if page:
                    self.main_stack.setCurrentWidget(page)

            if self.btn_home:     self.btn_home.clicked.connect(lambda: _go(page_home))
            if self.btn_fan:      self.btn_fan.clicked.connect(lambda: _go(page_fan))
            if self.btn_rgb:      self.btn_rgb.clicked.connect(lambda: _go(page_rgb))
            if self.btn_macro:    self.btn_macro.clicked.connect(lambda: _go(page_macro))
            if self.btn_settings: self.btn_settings.clicked.connect(lambda: _go(page_settings))
            if self.btn_info:     self.btn_info.clicked.connect(lambda: _go(page_info))

        self._retranslate_chrome()
        self._init_home_page()
        self._init_rgb_page()
        self._init_fan_power_page()
        self._init_settings_page()
        self._init_info_page()
        self._init_macro_page()

        self.window.show()

    # ──────────────────────────────────────────────────────────
    # Chrome (window title + sidebar tooltips)
    # ──────────────────────────────────────────────────────────
    def _retranslate_chrome(self):
        self.window.setWindowTitle(self.tr("window_title"))
        if self.btn_home:     self.btn_home.setToolTip(self.tr("btn_home_tooltip"))
        if self.btn_fan:      self.btn_fan.setToolTip(self.tr("btn_fan_tooltip"))
        if self.btn_rgb:      self.btn_rgb.setToolTip(self.tr("btn_rgb_tooltip"))
        if self.btn_macro:    self.btn_macro.setToolTip(self.tr("btn_macro_tooltip"))
        if self.btn_settings: self.btn_settings.setToolTip(self.tr("btn_settings_tooltip"))
        if self.btn_info:     self.btn_info.setToolTip(self.tr("btn_info_tooltip"))


def main():
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    icon = QIcon.fromTheme("alienarena")
    if not icon.isNull():
        qt_app.setWindowIcon(icon)

    app = TardixApp()

    tray = TrayIcon(app)
    if not icon.isNull():
        tray.setIcon(icon)
    tray.setVisible(True)
    tray.setToolTip("Left click: toggle leds. Right click: menu.")

    menu = QMenu()
    action_show = QAction("Show Window")
    action_quit = QAction("Quit")
    menu.addAction(action_show)
    menu.addAction(action_quit)
    tray.setContextMenu(menu)

    action_show.triggered.connect(app.window.show)
    action_quit.triggered.connect(qt_app.quit)

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
