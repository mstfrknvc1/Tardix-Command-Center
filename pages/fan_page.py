import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QPushButton,
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
from core.sensors import SensorPoller


class FanMixin:
    """Fan/Power page UI logic."""

    def _stop_sensor_poller(self):
        poller = getattr(self, "_sensor_poller", None)
        if poller is None:
            return
        try:
            poller.stop()
        except Exception:
            pass
        try:
            del self._sensor_poller
        except Exception:
            pass

    def _power_mode_label(self, key: str) -> str:
        return self.tr(f"power_mode_{key.lower().replace(' ', '_')}")

    def _acpi_backend_available(self) -> bool:
        return bool(getattr(self, "is_root", False) and getattr(self, "is_dell_g_series", False))

    def _platform_profile_available(self) -> bool:
        return os.path.exists("/sys/firmware/acpi/platform_profile")

    def _available_backend_modes(self) -> list[str]:
        modes = []
        if self._acpi_backend_available():
            modes.append("acpi")
        if self._platform_profile_available():
            modes.append("platform_profile")
        return modes

    def _resolved_backend_mode(self) -> str:
        forced = self.settings.value("PowerBackend", "auto")
        available = self._available_backend_modes()
        if forced in available:
            return forced
        if forced == "auto":
            if "acpi" in available:
                return "acpi"
            if "platform_profile" in available:
                return "platform_profile"
        return available[0] if available else "none"

    def _selected_power_key(self) -> str:
        data = self.power_combo.currentData()
        if isinstance(data, str) and data:
            return data
        return self.settings.value("Power", "USTT_Balanced")

    def _detect_power_backend(self):
        mode = self._resolved_backend_mode()
        if mode == "acpi":
            return self.tr("power_backend_acpi")
        if mode == "platform_profile":
            return self.tr("power_backend_platform_profile")
        return self.tr("power_backend_none")

    def _current_backend_mode(self):
        return self._resolved_backend_mode()

    def _init_fan_power_page(self):
        fan_page = self.window.findChild(QWidget, "bfancontrol")
        if not fan_page:
            return

        # Stop any existing sensor poller before rebuilding
        self._stop_sensor_poller()

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
        for mode_key in self.power_modes_dict.keys():
            self.power_combo.addItem(self._power_mode_label(mode_key), mode_key)
        current_key = self.settings.value("Power", "USTT_Balanced")
        idx = self.power_combo.findData(current_key)
        self.power_combo.setCurrentIndex(0 if idx < 0 else idx)
        pr.addWidget(self.power_combo, 1)
        self.apply_power_btn = QPushButton(self.tr("apply_power_profile"), power_row)
        self.apply_power_btn.clicked.connect(self._apply_power_profile)
        pr.addWidget(self.apply_power_btn)
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
        self.power_backend_label = QLabel("", group)
        self.power_backend_label.setWordWrap(True)
        main_vbox.addWidget(self.power_backend_label)

        root_layout.addWidget(group)

        self.power_combo.currentTextChanged.connect(self._on_power_changed)
        self.fan1_slider.sliderReleased.connect(lambda: self._on_fan_boost(1))
        self.fan2_slider.sliderReleased.connect(lambda: self._on_fan_boost(2))

        # SensorPoller reads sensors on a background QThread and delivers
        # results via a queued signal — the animation timer is never blocked.
        self._sensor_poller = SensorPoller(interval_ms=1000, parent=self.window)
        self._sensor_poller.data_ready.connect(self._update_sensor_ui)
        self._sensor_poller.start()

        backend = self._detect_power_backend()
        current_profile = self._platform_profile_current()
        backend_text = self.tr("power_backend_current", backend=backend)
        if current_profile:
            backend_text += f"  (active profile: {current_profile})"
        self.power_backend_label.setText(backend_text)

        if not (getattr(self, "is_root", False) and self.is_dell_g_series):
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
        selected_key = self._selected_power_key()
        self.settings.setValue("Power", selected_key)
        is_manual = selected_key == "Manual"
        self.fan1_slider.setEnabled(is_manual)
        self.fan2_slider.setEnabled(is_manual)
        if is_manual:
            self.fan1_slider.setValue(int(self.settings.value("Fan1 Boost", 0x00)))
            self.fan2_slider.setValue(int(self.settings.value("Fan2 Boost", 0x00)))
        if not is_manual:
            self.fan_info.setText(self.tr("fan_manual_info"))
        backend = self._detect_power_backend()
        self.power_backend_label.setText(self.tr("power_backend_current", backend=backend))

    def _apply_power_profile(self):
        message = self._apply_power_profile_message()
        backend = self._detect_power_backend()
        self.fan_info.setText(f"{message}\n{self.tr('power_backend_current', backend=backend)}")

    def _apply_power_profile_message(self) -> str:
        backend_mode = self._current_backend_mode()
        choice = self._selected_power_key()
        self.settings.setValue("Power", choice)
        choice_label = self._power_mode_label(choice)

        if backend_mode == "acpi":
            if not self._acpi_backend_available():
                return self.tr("fan_root_warn")
            mode = self.power_modes_dict[choice]
            self.acpi_call("set_power_mode", mode)
            result = self.acpi_call("get_power_mode")
            message = (
                f"Power mode set to {choice_label}.\n"
                if result == mode
                else f"Error! Command returned: {result}, but expecting {mode}.\n"
            )
            result_g = self.acpi_call("get_G_mode")
            if (choice == "G Mode") != (result_g == "0x1"):
                result_toggle = self.acpi_call("toggle_G_mode")
                expected = "0x1" if choice == "G Mode" else "0x0"
                if expected != result_toggle:
                    message += f"Expected G Mode = {choice == 'G Mode'} but read {result_toggle}!\n"
        elif backend_mode == "platform_profile":
            message = self._set_platform_profile(choice)
        else:
            message = self.tr("power_backend_none")

        return message

    def _platform_profile_choices(self) -> list[str]:
        """Return list of profiles supported by the running kernel."""
        choices_path = "/sys/firmware/acpi/platform_profile_choices"
        try:
            with open(choices_path, encoding="utf-8") as f:
                return f.read().strip().split()
        except OSError:
            return ["balanced", "performance", "low-power", "quiet"]

    def _platform_profile_current(self) -> str | None:
        """Return the currently active platform_profile, or None."""
        try:
            with open("/sys/firmware/acpi/platform_profile", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            return None

    def _set_platform_profile(self, choice: str) -> str:
        profile_path = "/sys/firmware/acpi/platform_profile"
        if not os.path.exists(profile_path):
            return self.tr("power_backend_none")

        mapping = {
            "USTT_Balanced":     "balanced",
            "USTT_Performance":  "performance",
            "USTT_Quiet":        "quiet",
            "USTT_FullSpeed":    "performance",
            "USTT_BatterySaver": "low-power",
            "G Mode":            "performance",
            "Manual":            "balanced",
        }
        desired = mapping.get(choice, "balanced")
        choice_label = self._power_mode_label(choice)

        # If kernel doesn't support the requested profile, use nearest available.
        supported = self._platform_profile_choices()
        profile = desired if desired in supported else (
            "balanced" if "balanced" in supported else (supported[0] if supported else desired)
        )

        def _try_write(path: str, value: str) -> bool:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(value)
                return True
            except OSError:
                return False

        ok = _try_write(profile_path, profile)
        if not ok:
            # pkexec fallback (prompts user for password once)
            try:
                result = subprocess.run(
                    ["pkexec", "sh", "-c", f"echo {profile} > {profile_path}"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
                ok = True
            except Exception:
                ok = False

        if not ok:
            return self.tr("power_backend_apply_fail", mode=choice_label, mapped=profile)

        # Verify by reading back
        actual = self._platform_profile_current() or ""
        if actual == profile:
            return self.tr("power_backend_apply_ok", mode=choice_label, mapped=profile)
        # Wrote without error but read-back differs — report what is active
        return self.tr("power_backend_apply_ok", mode=choice_label, mapped=actual or profile)


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

    def _update_sensor_ui(self, fan1: int, cpu: int, fan2: int, gpu: int):
        if hasattr(self, "fan1_widget"):    self.fan1_widget.set_rpm(fan1)
        if hasattr(self, "cpu_temp_gauge"): self.cpu_temp_gauge.set_temperature(cpu)
        if hasattr(self, "fan2_widget"):    self.fan2_widget.set_rpm(fan2)
        if hasattr(self, "gpu_temp_gauge"): self.gpu_temp_gauge.set_temperature(gpu)
        if hasattr(self, "fan1_current"):   self.fan1_current.setText(f"{fan1} RPM, {cpu} °C")
        if hasattr(self, "fan2_current"):   self.fan2_current.setText(f"{fan2} RPM, {gpu} °C")

    def get_rpm_and_temp(self):
        pass  # kept for compatibility; polling is now handled by SensorPoller
