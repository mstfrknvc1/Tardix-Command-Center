from PySide6.QtWidgets import QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app, *args, **kwargs):
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
