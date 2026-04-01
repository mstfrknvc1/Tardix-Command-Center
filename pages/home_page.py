from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.utils import _clear_layout


class HomeMixin:
    """Home page UI logic."""

    def _home_power_mode_label(self) -> str:
        power_key = self.settings.value("Power", "USTT_Balanced")
        if hasattr(self, "_power_mode_label"):
            return self._power_mode_label(power_key)
        return str(power_key)

    def _home_led_action_label(self) -> str:
        if hasattr(self, "_current_rgb_action_label"):
            return self._current_rgb_action_label()
        return str(self.settings.value("Action", "Static Color"))

    def _init_home_page(self):
        home_page = self.window.findChild(QWidget, "ahome")
        if not home_page:
            return

        layout = home_page.layout()
        if layout:
            _clear_layout(layout)
        else:
            layout = QVBoxLayout(home_page)

        title = QLabel(self.tr("home_title"), home_page)
        f = title.font(); f.setPointSize(20); f.setBold(True); title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        grid = QHBoxLayout()

        # System Status
        stats_group = QGroupBox(self.tr("system_status"), home_page)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.addWidget(QLabel(self.tr("laptop_model_label", model=self.model), home_page))
        kb_key = "keyboard_backlight_supported" if self.is_keyboard_supported else "keyboard_backlight_unsupported"
        stats_layout.addWidget(QLabel(self.tr(kb_key), home_page))
        power_label = QLabel(
            self.tr("power_mode_status", mode=self._home_power_mode_label()),
            home_page,
        )
        stats_layout.addWidget(power_label)
        led_label = QLabel(
            self.tr(
                "led_status",
                state=self.settings.value("State", "Off"),
                action=self._home_led_action_label(),
            ),
            home_page,
        )
        stats_layout.addWidget(led_label)
        stats_layout.addStretch()
        grid.addWidget(stats_group, 1)

        # Quick Actions
        act_group = QGroupBox(self.tr("quick_actions"), home_page)
        act_layout = QVBoxLayout(act_group)
        btn_led = QPushButton(self.tr("toggle_leds"), home_page)
        btn_led.clicked.connect(self._toggle_leds)
        act_layout.addWidget(btn_led)
        btn_rgb = QPushButton(self.tr("go_rgb"), home_page)
        btn_rgb.clicked.connect(lambda: self.main_stack.setCurrentIndex(2))
        act_layout.addWidget(btn_rgb)
        btn_fan = QPushButton(self.tr("go_fan"), home_page)
        btn_fan.clicked.connect(lambda: self.main_stack.setCurrentIndex(1))
        act_layout.addWidget(btn_fan)
        btn_set = QPushButton(self.tr("go_settings"), home_page)
        btn_set.clicked.connect(lambda: self.main_stack.setCurrentIndex(3))
        act_layout.addWidget(btn_set)
        act_layout.addStretch()
        grid.addWidget(act_group, 1)

        # Tips
        tips_group = QGroupBox(self.tr("tips_title"), home_page)
        tips_layout = QVBoxLayout(tips_group)
        tips_lbl = QLabel(self.tr("tips_text"), home_page)
        tips_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        tips_layout.addWidget(tips_lbl)
        grid.addWidget(tips_group, 1)

        layout.addLayout(grid, 1)

        self.home_led_label   = led_label
        self.home_power_label = power_label

        # Warn once if laptop model not recognised
        if (
            self.model == "Unknown"
            and not self.settings.value("ModelWarningSeen", False, type=bool)
        ):
            self.settings.setValue("ModelWarningSeen", True)
            QTimer.singleShot(300, lambda: QMessageBox.warning(
                home_page,
                self.tr("unsupported_model_title"),
                self.tr("unsupported_model_msg"),
            ))

    def _toggle_leds(self):
        try:
            self.toggle_led_state(source="home")
        except Exception as err:
            QMessageBox.warning(self.window, "Error", f"Cannot toggle LEDs:\n\n{err}")
