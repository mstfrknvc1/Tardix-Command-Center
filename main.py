#!/usr/bin/env python3
import sys
import tempfile

try:
    import pexpect  # type: ignore
except ModuleNotFoundError:
    pexpect = None

try:
    import awelc  # type: ignore
except ModuleNotFoundError:
    awelc = None

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice, QSettings, QTimer, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from patch import g15_5530_patch, g15_5520_patch, g15_5515_patch, g15_5511_patch, g16_7630_patch
from color_wheel import ColorWheel


class TardixApp:
    """
    Tek GUI: main.ui (tardix tasarımı) + main.py işlevleri.
    """

    def __init__(self):
        self._load_ui()

    def _load_ui(self):
        loader = QUiLoader()
        loader.registerCustomWidget(ColorWheel)

        ui_file = QFile("main.ui")
        if not ui_file.open(QIODevice.ReadOnly):
            raise RuntimeError(f"main.ui dosyası açılamadı: {ui_file.errorString()}")

        self.window = loader.load(ui_file)
        ui_file.close()

        if not self.window:
            raise RuntimeError(loader.errorString())

        self.settings = QSettings("Tardix", "CommandCenter")

        # Donanım/ACPI hazırlığı
        self.is_dell_g_series = False
        self.is_keyboard_supported = True
        self.model = "Unknown"
        self.timer = None

        try:
            self.logfile = open("/tmp/tardix-command-center.log", "w")
        except Exception:
            self.logfile = None

        self.init_acpi_call()

        # Sol menü / sayfa geçişleri
        self.main_stack = self.window.findChild(QStackedWidget, "stackedWidget")
        self.btn_home = self.window.findChild(QPushButton, "homebutton")
        self.btn_info = self.window.findChild(QPushButton, "infobutton")
        self.btn_rgb = self.window.findChild(QPushButton, "rgbbutton")
        self.btn_settings = self.window.findChild(QPushButton, "settingsbutton")
        self.btn_fan = self.window.findChild(QPushButton, "fanbutton")

        if self.main_stack:
            self.btn_home.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))  # Home
            self.btn_fan.clicked.connect(lambda: self.main_stack.setCurrentIndex(1))  # Fan
            self.btn_rgb.clicked.connect(lambda: self.main_stack.setCurrentIndex(2))  # RGB
            self.btn_settings.clicked.connect(lambda: self.main_stack.setCurrentIndex(3))  # Settings
            self.btn_info.clicked.connect(lambda: self.main_stack.setCurrentIndex(4))  # Info

        # RGB + Fan/Power bağlama
        self._init_rgb_page()
        self._init_fan_power_page()
        self._init_settings_page()

        self.window.show()

    # ------------------------------
    # UI: RGB page bindings
    # ------------------------------
    def _init_rgb_page(self):
        self.rgb_mode = self.window.findChild(QComboBox, "comboBox")
        self.rgb_label_static = self.window.findChild(QLabel, "label_2")
        self.rgb_label_morph = self.window.findChild(QLabel, "label_3")
        self.color_wheel = self.window.findChild(ColorWheel, "colorwheel")
        self.keyboard_preview = self.window.findChild(QLabel, "keyboardPreviewLabel")
        self.static_swatch = self.window.findChild(QWidget, "selectedStaticSwatch")
        self.morph_swatch = self.window.findChild(QWidget, "selectedMorphSwatch")
        self.static_hex_label = self.window.findChild(QLabel, "selectedStaticHex")
        self.morph_hex_label = self.window.findChild(QLabel, "selectedMorphHex")
        self.brightness_slider = self.window.findChild(QSlider, "brightnessSlider")
        self.brightness_value_label = self.window.findChild(QLabel, "brightnessValueLabel")

        if not (self.rgb_mode and self.rgb_label_static and self.rgb_label_morph and self.color_wheel):
            return

        self.rgb_mode.clear()
        self.rgb_mode.addItems(["Static Color", "Morph", "Color and Morph", "Off"])
        self.rgb_mode.setCurrentText(self.settings.value("Action", "Static Color"))

        # Renk hedefi seçimi: label'a tıklayınca hedef değişsin
        self._rgb_target = self.settings.value("RGB Target", "Static")
        self.rgb_label_static.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.rgb_label_morph.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.rgb_label_static.mousePressEvent = lambda event: self._set_rgb_target("Static")  # type: ignore[method-assign]
        self.rgb_label_morph.mousePressEvent = lambda event: self._set_rgb_target("Morph")  # type: ignore[method-assign]

        self._rgb_static = QColor(self.settings.value("RGB Static", "#7a7a7a"))
        self._rgb_morph = QColor(self.settings.value("RGB Morph", "#7a7a7a"))
        self._rgb_duration = int(self.settings.value("Duration", 255))

        # RGB Brightness (klavyeye uygulanır; wheel görünümünü etkilemez)
        # 0 = tam parlak (dim=0), 100 = tamamen kısık (dim=100)
        self._rgb_dim = int(self.settings.value("RGB Dim", 0))
        if self.brightness_slider and self.brightness_value_label:
            self.brightness_slider.setValue(self._rgb_dim)
            self.brightness_value_label.setText(f"{self._rgb_dim}%")
            self.brightness_slider.valueChanged.connect(self._on_dim_changed)

        # Klavye önizleme SVG'si
        if self.keyboard_preview:
            pm = QPixmap("assets/keyboard_preview.svg")
            if not pm.isNull():
                self.keyboard_preview.setPixmap(pm)
                self.keyboard_preview.setScaledContents(True)

        # Apply + Duration slider'ı programatik ekle (UI stilini bozmadan)
        container = self.rgb_mode.parentWidget()
        if container and not getattr(self, "_rgb_extra_built", False):
            self._rgb_extra_built = True
            layout = container.layout()
            if layout is None:
                layout = QVBoxLayout(container)
                container.setLayout(layout)

            duration_row = QWidget(container)
            duration_layout = QHBoxLayout(duration_row)
            duration_layout.setContentsMargins(0, 0, 0, 0)
            duration_layout.addWidget(QLabel("Duration", duration_row))
            self.duration_slider = QSlider(Qt.Horizontal, duration_row)
            self.duration_slider.setRange(0x4, 0xFFF)
            self.duration_slider.setValue(self._rgb_duration)
            self.duration_value = QLabel(str(self._rgb_duration), duration_row)
            duration_layout.addWidget(self.duration_slider, 1)
            duration_layout.addWidget(self.duration_value)
            layout.addWidget(duration_row)

            self.apply_button = QPushButton("Apply", container)
            layout.addWidget(self.apply_button)

            self.duration_slider.valueChanged.connect(self._on_duration_changed)
            self.apply_button.clicked.connect(self.apply_leds)

        self.rgb_mode.currentTextChanged.connect(lambda _: self.settings.setValue("Action", self.rgb_mode.currentText()))
        self.color_wheel.colorChanged.connect(self._on_color_changed)
        self._refresh_rgb_labels()
        self._refresh_selected_color_previews()

    def _set_rgb_target(self, target: str):
        self._rgb_target = target
        self.settings.setValue("RGB Target", target)
        self._refresh_rgb_labels()

    def _refresh_rgb_labels(self):
        static_hex = self._rgb_static.name()
        morph_hex = self._rgb_morph.name()
        active_static = " (selected)" if self._rgb_target == "Static" else ""
        active_morph = " (selected)" if self._rgb_target == "Morph" else ""
        self.rgb_label_static.setText(f"Static: {static_hex}{active_static}")
        self.rgb_label_morph.setText(f"Morph:  {morph_hex}{active_morph}")

    def _refresh_selected_color_previews(self):
        if self.static_swatch and self.static_hex_label:
            hex_ = self._rgb_static.name()
            self.static_hex_label.setText(hex_)
            self.static_swatch.setStyleSheet(f"background-color: {hex_}; border-radius: 8px; border: 2px solid #1C3F95;")
        if self.morph_swatch and self.morph_hex_label:
            hex_ = self._rgb_morph.name()
            self.morph_hex_label.setText(hex_)
            self.morph_swatch.setStyleSheet(f"background-color: {hex_}; border-radius: 8px; border: 2px solid #1C3F95;")

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
            # 0 = parlak, 100 = kısık
            try:
                awelc.set_dim(value)
            except Exception:
                pass

    def _on_duration_changed(self, value: int):
        self._rgb_duration = value
        self.settings.setValue("Duration", value)
        if hasattr(self, "duration_value"):
            self.duration_value.setText(str(value))

    # ------------------------------
    # UI: Fan/Power page bindings
    # ------------------------------
    def _init_fan_power_page(self):
        fan_page = self.window.findChild(QWidget, "bfancontrol")
        if not fan_page:
            return

        if getattr(self, "_fan_ui_built", False):
            return
        self._fan_ui_built = True

        root_layout = fan_page.layout()
        if root_layout is None:
            root_layout = QVBoxLayout(fan_page)
            fan_page.setLayout(root_layout)

        group = QGroupBox("Power and Fans", fan_page)
        vbox = QVBoxLayout(group)

        self.power_modes_dict = {
            "USTT_Balanced": "0xa0",
            "USTT_Performance": "0xa1",
            "USTT_Quiet": "0xa3",
            "USTT_FullSpeed": "0xa4",
            "USTT_BatterySaver": "0xa5",
            "G Mode": "0xab",
            "Manual": "0x0",
        }

        self.power_combo = QComboBox(group)
        self.power_combo.addItems(list(self.power_modes_dict.keys()))
        self.power_combo.setCurrentText(self.settings.value("Power", "USTT_Balanced"))
        vbox.addWidget(self.power_combo)

        self.fan1_slider, self.fan1_current = self._fan_row(group, "CPU Fan Boost", "Fan1 Boost", vbox)
        self.fan2_slider, self.fan2_current = self._fan_row(group, "GPU Fan Boost", "Fan2 Boost", vbox)

        self.fan_info = QLabel("", group)
        self.fan_info.setWordWrap(True)
        vbox.addWidget(self.fan_info)

        root_layout.addWidget(group)

        self.power_combo.currentTextChanged.connect(self._on_power_changed)
        self.fan1_slider.sliderReleased.connect(lambda: self._on_fan_boost(1))
        self.fan2_slider.sliderReleased.connect(lambda: self._on_fan_boost(2))

        if getattr(self, "is_root", False) and self.is_dell_g_series:
            self.timer = QTimer(self.window)
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.get_rpm_and_temp)
            self.timer.start()
        else:
            self.fan_info.setText("Power/Fan kontrolleri için root yetkisi gerekebilir (pkexec).")

    def _fan_row(self, parent: QWidget, title: str, setting_key: str, vbox: QVBoxLayout):
        label = QLabel(title, parent)
        vbox.addWidget(label)
        row = QWidget(parent)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal, row)
        slider.setRange(0x00, 0xFF)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(25.5)
        slider.setValue(int(self.settings.value(setting_key, 0x00)))
        current = QLabel("0 RPM", row)
        h.addWidget(slider, 1)
        h.addWidget(current)
        vbox.addWidget(row)
        return slider, current

    def _on_power_changed(self):
        self.fan1_slider.setValue(0)
        self.fan2_slider.setValue(0)
        self.settings.setValue("Power", self.power_combo.currentText())

        if not (getattr(self, "is_root", False) and self.is_dell_g_series):
            return

        choice = self.settings.value("Power", "USTT_Balanced")
        mode = self.power_modes_dict[choice]
        self.acpi_call("set_power_mode", mode)
        result = self.acpi_call("get_power_mode")
        message = ""
        if result == mode:
            message = f"Power mode set to {choice}.\n"
        else:
            message = f"Error! Command returned: {result}, but expecting {mode}.\n"

        result_g = self.acpi_call("get_G_mode")
        if (choice == "G Mode") != (result_g == "0x1"):
            result_toggle = self.acpi_call("toggle_G_mode")
            expected = "0x1" if choice == "G Mode" else "0x0"
            if expected != result_toggle:
                message += f"Expected to read G Mode = {choice == 'G Mode'} but read {result_toggle}!\n"
        self.fan_info.setText(message)

    def _on_fan_boost(self, which: int):
        if not (getattr(self, "is_root", False) and self.is_dell_g_series):
            return

        if which == 1:
            last = self.acpi_call("get_fan1_boost")
            new_val = self.fan1_slider.value()
            self.acpi_call("set_fan1_boost", f"0x{new_val:02X}")
            now = self.acpi_call("get_fan1_boost")
            self.settings.setValue("Fan1 Boost", new_val)
            self.fan_info.setText(f"Fan1 Boost: {int(last,0)/0xFF*100:.0f}% to {int(now,0)/0xFF*100:.0f}%.")
        else:
            last = self.acpi_call("get_fan2_boost")
            new_val = self.fan2_slider.value()
            self.acpi_call("set_fan2_boost", f"0x{new_val:02X}")
            now = self.acpi_call("get_fan2_boost")
            self.settings.setValue("Fan2 Boost", new_val)
            self.fan_info.setText(f"Fan2 Boost: {int(last,0)/0xFF*100:.0f}% to {int(now,0)/0xFF*100:.0f}%.")

    def get_rpm_and_temp(self):
        if not self.window.isVisible():
            return
        try:
            fan1_rpm = self.acpi_call("get_fan1_rpm")
            cpu_temp = self.acpi_call("get_cpu_temp")
            fan2_rpm = self.acpi_call("get_fan2_rpm")
            gpu_temp = self.acpi_call("get_gpu_temp")
            self.fan1_current.setText(f"{int(fan1_rpm,0)} RPM, {int(cpu_temp,0)} °C")
            self.fan2_current.setText(f"{int(fan2_rpm,0)} RPM, {int(gpu_temp,0)} °C")
        except Exception:
            pass

    # ------------------------------
    # UI: Settings bindings (şimdilik çoğu UI-only)
    # ------------------------------
    def _init_settings_page(self):
        self.turbo_boost_toggle = self.window.findChild(QCheckBox, "turboBoostToggle")
        self.temp_limit_slider = self.window.findChild(QSlider, "tempLimitSlider")
        self.temp_limit_value = self.window.findChild(QLabel, "tempLimitValueLabel")

        if self.turbo_boost_toggle:
            enabled = self.settings.value("DisableTurboBoost", "false") == "true"
            self.turbo_boost_toggle.setChecked(enabled)
            self.turbo_boost_toggle.toggled.connect(self._on_turbo_boost_toggled)

        if self.temp_limit_slider and self.temp_limit_value:
            limit = int(self.settings.value("TempLimitC", 95))
            limit = max(85, min(100, limit))
            self.temp_limit_slider.setValue(limit)
            self.temp_limit_value.setText(f"{limit}°C")
            self.temp_limit_slider.valueChanged.connect(self._on_temp_limit_changed)

    def _on_turbo_boost_toggled(self, checked: bool):
        # İstenen: UI’de olsun; işlevsel olması şart değil.
        self.settings.setValue("DisableTurboBoost", "true" if checked else "false")

    def _on_temp_limit_changed(self, value: int):
        value = max(85, min(100, int(value)))
        self.settings.setValue("TempLimitC", value)
        if self.temp_limit_value:
            self.temp_limit_value.setText(f"{value}°C")

    # ------------------------------
    # LED actions
    # ------------------------------
    def apply_leds(self):
        try:
            action = self.settings.value("Action", "Static Color")
            if action == "Static Color":
                self.apply_static()
            elif action == "Morph":
                self.apply_morph()
            elif action == "Color and Morph":
                self.apply_color_and_morph()
            else:
                self.remove_animation()
        except Exception as err:
            QMessageBox.warning(self.window, "Error", f"Cannot apply LED settings:\n\n{err.__class__.__name__}: {err}")
            raise

    def apply_static(self):
        if awelc is None:
            raise RuntimeError("pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun.")
        awelc.set_static(self._rgb_static.red(), self._rgb_static.green(), self._rgb_static.blue())
        self.settings.setValue("Action", "Static Color")
        self.settings.setValue("State", "On")

    def apply_morph(self):
        if awelc is None:
            raise RuntimeError("pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun.")
        awelc.set_morph(self._rgb_morph.red(), self._rgb_morph.green(), self._rgb_morph.blue(), self._rgb_duration)
        self.settings.setValue("Action", "Morph")
        self.settings.setValue("State", "On")

    def apply_color_and_morph(self):
        if awelc is None:
            raise RuntimeError("pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun.")
        awelc.set_color_and_morph(
            self._rgb_static.red(),
            self._rgb_static.green(),
            self._rgb_static.blue(),
            self._rgb_morph.red(),
            self._rgb_morph.green(),
            self._rgb_morph.blue(),
            self._rgb_duration,
        )
        self.settings.setValue("Action", "Color and Morph")
        self.settings.setValue("State", "On")

    def remove_animation(self):
        if awelc is None:
            raise RuntimeError("pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun.")
        awelc.remove_animation()
        self.settings.setValue("State", "Off")

    def tray_on(self):
        if awelc is None:
            return
        awelc.set_dim(0)
        self.settings.setValue("State", "On")

    def tray_off(self):
        if awelc is None:
            return
        awelc.set_dim(100)
        self.settings.setValue("State", "Off")

    # ------------------------------
    # ACPI / model detection
    # ------------------------------
    def init_acpi_call(self):
        if pexpect is None:
            self.is_root = False
            self.is_dell_g_series = False
            return

        self.acpi_call_dict = {
            "get_laptop_model": ["0x1a", "0x02", "0x02"],
            "get_power_mode": ["0x14", "0x0b", "0x00"],
            "set_power_mode": ["0x15", "0x01"],
            "toggle_G_mode": ["0x25", "0x01"],
            "get_G_mode": ["0x25", "0x02"],
            "set_fan1_boost": ["0x15", "0x02", "0x32"],
            "get_fan1_boost": ["0x14", "0x0c", "0x32"],
            "get_fan1_rpm": ["0x14", "0x05", "0x32"],
            "get_cpu_temp": ["0x14", "0x04", "0x01"],
            "set_fan2_boost": ["0x15", "0x02", "0x33"],
            "get_fan2_boost": ["0x14", "0x0c", "0x33"],
            "get_fan2_rpm": ["0x14", "0x05", "0x33"],
            "get_gpu_temp": ["0x14", "0x04", "0x06"],
        }

        self.is_root = False
        try:
            self.shell = pexpect.spawn(
                "bash",
                encoding="utf-8",
                logfile=self.logfile,
                env=None,
                args=["--noprofile", "--norc"],
            )
            self.shell.expect("[#$] ")
            self.shell_exec(" export HISTFILE=/dev/null; history -c")
            self.shell_exec("pkexec bash --noprofile --norc")
            self.shell_exec(" export HISTFILE=/dev/null; history -c")
            self.is_root = self.shell_exec("whoami")[1].find("root") != -1
            if not self.is_root:
                return
        except Exception:
            return

        self._check_laptop_model()

    def _check_laptop_model(self):
        # Intel
        self.acpi_cmd = 'echo "\\\\_SB.AMWW.WMAX 0 {} {{{}, {}, {}, 0x00}}" | tee /proc/acpi/call; cat /proc/acpi/call'
        laptop_model = self.acpi_call("get_laptop_model")

        if laptop_model == "0x0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5530"
            g15_5530_patch(self)
            return

        if laptop_model == "0x12c0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5520"
            g15_5520_patch(self)
            return

        if laptop_model == "0xc80":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5511"
            g15_5511_patch(self)
            return

        # G16 7630 check (orijinal davranış korunuyor)
        if laptop_model == "0x0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = False
            self.model = "G16 7630"
            g16_7630_patch(self)
            return

        # AMD
        self.acpi_cmd = 'echo "\\\\_SB.AMW3.WMAX 0 {} {{{}, {}, {}, 0x00}}" | tee /proc/acpi/call; cat /proc/acpi/call'
        laptop_model = self.acpi_call("get_laptop_model")

        if laptop_model == "0x12c0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5525"
            return

        if laptop_model == "0xc80":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5515"
            g15_5515_patch(self)

    def acpi_call(self, cmd, arg1="0x00", arg2="0x00"):
        args = self.acpi_call_dict[cmd]
        if len(args) == 4:
            cmd_current = self.acpi_cmd.format(args[0], args[1], args[2], args[3])
        elif len(args) == 3:
            cmd_current = self.acpi_cmd.format(args[0], args[1], args[2], arg1)
        elif len(args) == 2:
            cmd_current = self.acpi_cmd.format(args[0], args[1], arg1, arg2)
        else:
            cmd_current = ""
        return self.parse_shell_exec(self.shell_exec(cmd_current)[2])

    def shell_exec(self, cmd: str):
        self.shell.sendline(cmd)
        self.shell.expect("[#$] ")
        return self.shell.before.split("\n")

    def parse_shell_exec(self, line: str):
        return line[line.find("\r") + 1 : line.find("\x00")]


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app: TardixApp, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = app
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason != QSystemTrayIcon.ActivationReason.Trigger:
            return
        # Sol tık: led toggle
        if self.app.settings.value("State", "Off") == "Off":
            self.app.tray_on()
        else:
            self.app.tray_off()


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
