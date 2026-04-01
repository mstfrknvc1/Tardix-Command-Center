try:
    from hardware import awelc  # type: ignore
except (ModuleNotFoundError, ImportError):
    awelc = None

from PySide6.QtWidgets import QMessageBox


class LEDMixin:
    """LED/RGB hardware control methods."""

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
        self.settings.setValue("Action", "Color and Morph")
        self.settings.setValue("State", "On")

    def remove_animation(self):
        if awelc is None:
            raise RuntimeError(
                "pyusb/usb modülü bulunamadı. `pip install -r requirements.txt` ile bağımlılıkları kurun."
            )
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
