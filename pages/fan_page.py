import random

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from widgets.fan_widget import FanWidget
from widgets.temperature_gauge import TemperatureGauge
from core.utils import _clear_layout


class FanMixin:
    """Fan/Power page UI logic."""

    def _init_fan_power_page(self):
        fan_page = self.window.findChild(QWidget, "bfancontrol")
        if not fan_page:
            return

        # Stop existing polling timer to avoid multiple timers after retranslate
        if self.timer:
            self.timer.stop()
            self.timer = None

        root_layout = fan_page.layout()
        if root_layout is None:
            root_layout = QVBoxLayout(fan_page)
            fan_page.setLayout(root_layout)
        _clear_layout(root_layout)

        self.power_modes_dict = {
            "USTT_Balanced":     "0xa0",
            "USTT_Performance":  "0xa1",
            "USTT_Quiet":        "0xa3",
            "USTT_FullSpeed":    "0xa4",
            "USTT_BatterySaver": "0xa5",
            "G Mode":            "0xab",
            "Manual":            "0x0",
        }

        group = QGroupBox(self.tr("power_and_fans"), fan_page)
        main_vbox = QVBoxLayout(group)

        power_row = QWidget(group)
        pr = QHBoxLayout(power_row); pr.setContentsMargins(0, 0, 0, 0)
        pr.addWidget(QLabel(self.tr("power_mode_label")))
        self.power_combo = QComboBox(power_row)
        self.power_combo.addItems(list(self.power_modes_dict.keys()))
        self.power_combo.setCurrentText(self.settings.value("Power", "USTT_Balanced"))
        pr.addWidget(self.power_combo, 1)
        main_vbox.addWidget(power_row)

        fan_hbox = QHBoxLayout()
        fan_left = QWidget(group)
        fan_left_layout = QVBoxLayout(fan_left)

        cpu_hbox = QHBoxLayout()
        self.fan1_widget = FanWidget(fan_left)
        self.fan1_widget.setMinimumSize(150, 150)
        cpu_hbox.addWidget(self.fan1_widget, 1)
        self.cpu_temp_gauge = TemperatureGauge(fan_left, max_temp=100, label="CPU")
        self.cpu_temp_gauge.setMinimumSize(150, 150)
        cpu_hbox.addWidget(self.cpu_temp_gauge, 1)
        fan_left_layout.addLayout(cpu_hbox)

        gpu_hbox = QHBoxLayout()
        self.fan2_widget = FanWidget(fan_left)
        self.fan2_widget.setMinimumSize(150, 150)
        gpu_hbox.addWidget(self.fan2_widget, 1)
        self.gpu_temp_gauge = TemperatureGauge(fan_left, max_temp=100, label="GPU")
        self.gpu_temp_gauge.setMinimumSize(150, 150)
        gpu_hbox.addWidget(self.gpu_temp_gauge, 1)
        fan_left_layout.addLayout(gpu_hbox)
        fan_hbox.addWidget(fan_left, 2)

        fan_right = QWidget(group)
        fan_right_layout = QVBoxLayout(fan_right)
        self.fan1_slider, self.fan1_current = self._fan_row(
            fan_right, self.tr("cpu_fan_boost"), "Fan1 Boost", fan_right_layout
        )
        self.fan2_slider, self.fan2_current = self._fan_row(
            fan_right, self.tr("gpu_fan_boost"), "Fan2 Boost", fan_right_layout
        )
        fan_right_layout.addStretch()
        fan_hbox.addWidget(fan_right, 1)

        main_vbox.addLayout(fan_hbox)

        self.fan_info = QLabel("", group)
        self.fan_info.setWordWrap(True)
        main_vbox.addWidget(self.fan_info)

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
            self.fan_info.setText(self.tr("fan_root_warn"))

    def _fan_row(self, parent: QWidget, title: str, setting_key: str, vbox: QVBoxLayout):
        vbox.addWidget(QLabel(title, parent))
        row = QWidget(parent)
        h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0)
        slider = QSlider(Qt.Horizontal, row)
        slider.setRange(0x00, 0xFF)
        slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider.setTickInterval(25)
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
        is_manual = self.power_combo.currentText() == "Manual"
        self.fan1_slider.setEnabled(is_manual)
        self.fan2_slider.setEnabled(is_manual)
        if not is_manual:
            self.fan_info.setText(self.tr("fan_manual_info"))
            return
        if not (getattr(self, "is_root", False) and self.is_dell_g_series):
            return
        choice = self.settings.value("Power", "USTT_Balanced")
        mode = self.power_modes_dict[choice]
        self.acpi_call("set_power_mode", mode)
        result = self.acpi_call("get_power_mode")
        message = (
            f"Power mode set to {choice}.\n"
            if result == mode
            else f"Error! Command returned: {result}, but expecting {mode}.\n"
        )
        result_g = self.acpi_call("get_G_mode")
        if (choice == "G Mode") != (result_g == "0x1"):
            result_toggle = self.acpi_call("toggle_G_mode")
            expected = "0x1" if choice == "G Mode" else "0x0"
            if expected != result_toggle:
                message += f"Expected G Mode = {choice == 'G Mode'} but read {result_toggle}!\n"
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
            self.fan_info.setText(f"Fan1 Boost: {int(last,0)/0xFF*100:.0f}% → {int(now,0)/0xFF*100:.0f}%.")
        else:
            last = self.acpi_call("get_fan2_boost")
            new_val = self.fan2_slider.value()
            self.acpi_call("set_fan2_boost", f"0x{new_val:02X}")
            now = self.acpi_call("get_fan2_boost")
            self.settings.setValue("Fan2 Boost", new_val)
            self.fan_info.setText(f"Fan2 Boost: {int(last,0)/0xFF*100:.0f}% → {int(now,0)/0xFF*100:.0f}%.")

    def get_rpm_and_temp(self):
        if not self.window.isVisible():
            return
        try:
            if getattr(self, "is_root", False) and self.is_dell_g_series:
                fan1_rpm_int = int(self.acpi_call("get_fan1_rpm"), 0)
                cpu_temp_int = int(self.acpi_call("get_cpu_temp"),  0)
                fan2_rpm_int = int(self.acpi_call("get_fan2_rpm"), 0)
                gpu_temp_int = int(self.acpi_call("get_gpu_temp"),  0)
            else:
                cpu_temp_int = random.randint(45, 85)
                gpu_temp_int = random.randint(40, 80)
                fan1_rpm_int = random.randint(1500, 5000)
                fan2_rpm_int = random.randint(1200, 4500)
                if not getattr(self, "_temp_warning_shown", False):
                    self._temp_warning_shown = True
                    self.fan_info.setText(self.tr("fan_demo_warn"))
            if hasattr(self, "fan1_widget"):    self.fan1_widget.set_rpm(fan1_rpm_int)
            if hasattr(self, "cpu_temp_gauge"): self.cpu_temp_gauge.set_temperature(cpu_temp_int)
            if hasattr(self, "fan2_widget"):    self.fan2_widget.set_rpm(fan2_rpm_int)
            if hasattr(self, "gpu_temp_gauge"): self.gpu_temp_gauge.set_temperature(gpu_temp_int)
            self.fan1_current.setText(f"{fan1_rpm_int} RPM, {cpu_temp_int} °C")
            self.fan2_current.setText(f"{fan2_rpm_int} RPM, {gpu_temp_int} °C")
        except Exception as e:
            if hasattr(self, "fan_info"):
                self.fan_info.setText(f"⚠️  Sıcaklık verisi alınamıyor: {str(e)[:50]}")
