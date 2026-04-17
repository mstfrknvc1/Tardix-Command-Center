#!/usr/bin/env python3
import argparse
from datetime import datetime
import sys
import os
import traceback


def _prefer_local_venv_python():
    # On PEP 668 distros, system python may not have project deps.
    if os.environ.get("TCC_SKIP_VENV_REEXEC") == "1":
        return
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    if not os.path.exists(venv_python):
        return

    env = os.environ.copy()
    env["TCC_SKIP_VENV_REEXEC"] = "1"
    os.execve(venv_python, [venv_python, *sys.argv], env)


_prefer_local_venv_python()

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, QSettings
from PySide6.QtGui import QAction, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
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
from core.app_meta import (
    APP_ID,
    APP_NAME,
    APP_ORGANIZATION,
    APP_ORGANIZATION_DOMAIN,
    APP_VERSION,
)

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

    def __init__(self, start_hidden: bool = False):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self._start_hidden = start_hidden
        self._init_runtime_logging()
        self._load_ui()

    def _init_runtime_logging(self):
        log_dir = os.path.join(os.path.expanduser("~"), ".cache", "tardix-command-center")
        os.makedirs(log_dir, exist_ok=True)
        self.runtime_log_path = os.path.join(log_dir, "runtime.log")

    def log_event(self, message: str):
        timestamp = datetime.now().isoformat(timespec="seconds")
        try:
            with open(self.runtime_log_path, "a", encoding="utf-8") as handle:
                handle.write(f"[{timestamp}] {message}\n")
        except OSError:
            pass

    def log_exception(self, context: str, err: Exception):
        self.log_event(f"{context}: {err.__class__.__name__}: {err}")
        try:
            with open(self.runtime_log_path, "a", encoding="utf-8") as handle:
                handle.write(traceback.format_exc())
                handle.write("\n")
        except OSError:
            pass

    def _app_icon(self):
        for icon_name in ["logo.png", "tardix.png", "icon.png", "atom.png"]:
            icon_path = os.path.join(self.script_dir, "Design", "png", icon_name)
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        return QIcon.fromTheme("alienarena")

    def _icon_from_design(self, filename: str) -> QIcon:
        icon_path = os.path.join(self.script_dir, "Design", "png", filename)
        return QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

    def _apply_sidebar_icons(self):
        icon_map = {
            "btn_home": "house-simple.png",
            "btn_fan": "fan.png",
            "btn_rgb": "lightbulb.png",
            "btn_macro": "keyboard.png",
            "btn_settings": "gear.png",
            "btn_info": "info.png",
        }
        for attr_name, filename in icon_map.items():
            button = getattr(self, attr_name, None)
            if button is None:
                continue
            icon = self._icon_from_design(filename)
            if not icon.isNull():
                button.setIcon(icon)

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

        icon = self._app_icon()
        if not icon.isNull():
            self.window.setWindowIcon(icon)

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
        self.log_event("Application startup")

        self.init_acpi_call()

        self.main_stack    = self.window.findChild(QStackedWidget, "stackedWidget")
        self.btn_home      = self.window.findChild(QPushButton, "homebutton")
        self.btn_fan       = self.window.findChild(QPushButton, "fanbutton")
        self.btn_rgb       = self.window.findChild(QPushButton, "rgbbutton")
        self.btn_macro     = self.window.findChild(QPushButton, "macrobutton")
        self.btn_settings  = self.window.findChild(QPushButton, "settingsbutton")
        self.btn_info      = self.window.findChild(QPushButton, "infobutton")
        self._apply_sidebar_icons()

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

        self.window.closeEvent = self._handle_window_close
        if self._start_hidden:
            self.window.hide()
        else:
            self.window.show()

    def _cleanup(self):
        self.log_event("Application shutdown")
        if hasattr(self, "_stop_sensor_poller"):
            self._stop_sensor_poller()
        shell = getattr(self, "shell", None)
        if shell is not None:
            try:
                shell.close(force=True)
            except Exception:
                pass
        logfile = getattr(self, "logfile", None)
        if logfile is not None:
            try:
                logfile.close()
            except Exception:
                pass

    def _handle_window_close(self, event):
        """Always hide to tray on close; quit only via tray menu."""
        self.window.hide()
        event.ignore()

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


def _single_instance_lock(app_name: str) -> QLocalServer | None:
    """
    Returns a live QLocalServer that acts as a single-instance lock.
    Returns None if another instance is already running (caller should exit).
    """
    socket = QLocalSocket()
    socket.connectToServer(app_name)
    if socket.waitForConnected(200):
        socket.disconnectFromServer()
        return None   # another instance is running

    # Remove any stale socket file from a previous crash
    QLocalServer.removeServer(app_name)
    server = QLocalServer()
    server.listen(app_name)
    return server


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--background", action="store_true")
    args, qt_args = parser.parse_known_args()

    qt_app = QApplication([sys.argv[0], *qt_args])
    qt_app.setApplicationName(APP_NAME)
    qt_app.setApplicationDisplayName(APP_NAME)
    qt_app.setApplicationVersion(APP_VERSION)
    qt_app.setOrganizationName(APP_ORGANIZATION)
    qt_app.setOrganizationDomain(APP_ORGANIZATION_DOMAIN)
    qt_app.setDesktopFileName(APP_ID)
    # Never quit when last window closes – tray keeps app alive.
    qt_app.setQuitOnLastWindowClosed(False)

    # ── Single-instance guard ──────────────────────────────────────────────
    _lock = _single_instance_lock(APP_ID)
    if _lock is None:
        # Another instance is already running; bring it to front via tray.
        print(f"{APP_NAME} is already running.", file=sys.stderr)
        sys.exit(0)

    app = TardixApp(start_hidden=args.background)
    icon = app._app_icon()
    if not icon.isNull():
        qt_app.setWindowIcon(icon)

    def _quit():
        app._cleanup()
        _lock.close()
        qt_app.quit()

    qt_app.aboutToQuit.connect(app._cleanup)

    tray = TrayIcon(app)
    if not icon.isNull():
        tray.setIcon(icon)
    tray.setVisible(True)
    tray.setToolTip(APP_NAME)

    menu = QMenu()
    action_show = QAction("Göster / Show")
    action_quit = QAction("Çıkış / Quit")
    menu.addAction(action_show)
    menu.addSeparator()
    menu.addAction(action_quit)
    tray.setContextMenu(menu)

    action_show.triggered.connect(app.window.show)
    action_show.triggered.connect(app.window.raise_)
    action_quit.triggered.connect(_quit)

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
