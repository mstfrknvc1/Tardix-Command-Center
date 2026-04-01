try:
    from hardware import awelc  # type: ignore
except (ModuleNotFoundError, ImportError):
    awelc = None

import traceback

try:
    import usb.core as usb_core  # type: ignore
except (ModuleNotFoundError, ImportError):
    usb_core = None

from PySide6.QtWidgets import QMessageBox


class LEDMixin:
    """LED/RGB hardware control methods."""

    def _set_last_rgb_mode(self, mode_key: str):
        if mode_key != "off":
            self.settings.setValue("LastRGBMode", mode_key)

    def _last_rgb_mode_key(self) -> str:
        mode_key = self.settings.value("LastRGBMode", "static_color")
        if not isinstance(mode_key, str):
            return "static_color"
        normalized = mode_key.strip().lower().replace(" ", "_")
        if normalized in {"static_color", "morph", "color_and_morph"}:
            return normalized
        return "static_color"

    def _effective_rgb_mode_key(self) -> str:
        mode_key = self._current_rgb_mode_key()
        return self._last_rgb_mode_key() if mode_key == "off" else mode_key

    def _set_home_led_status(self, state: str):
        if hasattr(self, "home_led_label"):
            self.home_led_label.setText(
                self.tr("led_status", state=state, action=self._home_led_action_label())
            )

    def _apply_mode_key(self, mode_key: str):
        if mode_key == "static_color":
            self.apply_static()
        elif mode_key == "morph":
            self.apply_morph()
        elif mode_key == "color_and_morph":
            self.apply_color_and_morph()
        else:
            self.remove_animation()

    def toggle_led_state(self, source: str = "ui"):
        current_state = self.settings.value("State", "Off")
        try:
            if current_state == "Off":
                mode_key = self._effective_rgb_mode_key()
                self._apply_mode_key(mode_key)
                self._set_home_led_status("On")
                if hasattr(self, "log_event"):
                    self.log_event(f"LED toggle on succeeded via {source} using mode={mode_key}")
            else:
                self.remove_animation()
                self._set_home_led_status("Off")
                if hasattr(self, "log_event"):
                    self.log_event(f"LED toggle off succeeded via {source}")
        except Exception as err:
            if hasattr(self, "log_exception"):
                self.log_exception(
                    f"LED toggle failed via {source} state={current_state} mode={self._current_rgb_mode_key()}",
                    err,
                )
            raise

    def _current_rgb_mode_key(self) -> str:
        if hasattr(self, "_rgb_mode_key"):
            return self._rgb_mode_key()

        action = self.settings.value("RGB Mode", self.settings.value("Action", "Static Color"))
        if not isinstance(action, str):
            return "static_color"
        normalized = action.strip().lower().replace(" ", "_")
        return {
            "static": "static_color",
            "static_color": "static_color",
            "morph": "morph",
            "color_and_morph": "color_and_morph",
            "off": "off",
        }.get(normalized, "static_color")

    def apply_leds(self):
        try:
            mode_key = self._current_rgb_mode_key()
            if mode_key == "static_color":
                self.apply_static()
            elif mode_key == "morph":
                self.apply_morph()
            elif mode_key == "color_and_morph":
                self.apply_color_and_morph()
            else:
                self.remove_animation()
        except Exception as err:
            QMessageBox.warning(
                self.window, "Error",
                f"Cannot apply LED settings:\n\n{err.__class__.__name__}: {err}"
            )
            raise

    def apply_static(self):
        if awelc is None:
            raise RuntimeError(
                "pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun."
            )
        awelc.set_static(self._rgb_static.red(), self._rgb_static.green(), self._rgb_static.blue())
        self._set_last_rgb_mode("static_color")
        if hasattr(self, "_sync_rgb_mode_settings"):
            self._sync_rgb_mode_settings("static_color")
        else:
            self.settings.setValue("Action", "Static Color")
        self.settings.setValue("State", "On")

    def apply_morph(self):
        if awelc is None:
            raise RuntimeError(
                "pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun."
            )
        awelc.set_morph(
            self._rgb_morph.red(), self._rgb_morph.green(), self._rgb_morph.blue(),
            self._rgb_duration,
        )
        self._set_last_rgb_mode("morph")
        if hasattr(self, "_sync_rgb_mode_settings"):
            self._sync_rgb_mode_settings("morph")
        else:
            self.settings.setValue("Action", "Morph")
        self.settings.setValue("State", "On")

    def apply_color_and_morph(self):
        if awelc is None:
            raise RuntimeError(
                "pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun."
            )
        awelc.set_color_and_morph(
            self._rgb_static.red(),
            self._rgb_static.green(),
            self._rgb_static.blue(),
            self._rgb_morph.red(),
            self._rgb_morph.green(),
            self._rgb_morph.blue(),
            self._rgb_duration,
        )
        self._set_last_rgb_mode("color_and_morph")
        if hasattr(self, "_sync_rgb_mode_settings"):
            self._sync_rgb_mode_settings("color_and_morph")
        else:
            self.settings.setValue("Action", "Color and Morph")
        self.settings.setValue("State", "On")

    def remove_animation(self):
        if awelc is None:
            if hasattr(self, "_sync_rgb_mode_settings"):
                self._sync_rgb_mode_settings("off")
            self.settings.setValue("State", "Off")
            return
        try:
            awelc.remove_animation()
        except Exception as err:
            if usb_core is not None and not isinstance(err, usb_core.USBError):
                raise
            if hasattr(self, "log_exception"):
                self.log_exception("LED remove_animation USB error", err)
        if hasattr(self, "_sync_rgb_mode_settings"):
            self._sync_rgb_mode_settings("off")
        self.settings.setValue("State", "Off")

    def tray_on(self):
        self.toggle_led_state(source="tray")

    def tray_off(self):
        self.toggle_led_state(source="tray")
