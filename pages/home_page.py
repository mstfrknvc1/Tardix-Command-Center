from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.utils import _clear_layout
from core.news import NewsPoller, FeedItem
from widgets.news_item_widget import NewsItemWidget


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

        # ── top row: system status ────────────────────────────────────────────
        stats_group = QGroupBox(self.tr("system_status"), home_page)
        stats_layout = QHBoxLayout(stats_group)

        left_stats = QVBoxLayout()
        left_stats.addWidget(QLabel(self.tr("laptop_model_label", model=self.model), home_page))
        kb_key = "keyboard_backlight_supported" if self.is_keyboard_supported else "keyboard_backlight_unsupported"
        left_stats.addWidget(QLabel(self.tr(kb_key), home_page))
        left_stats.addStretch()

        right_stats = QVBoxLayout()
        power_label = QLabel(
            self.tr("power_mode_status", mode=self._home_power_mode_label()),
            home_page,
        )
        right_stats.addWidget(power_label)
        led_label = QLabel(
            self.tr(
                "led_status",
                state=self.settings.value("State", "Off"),
                action=self._home_led_action_label(),
            ),
            home_page,
        )
        right_stats.addWidget(led_label)
        right_stats.addStretch()

        stats_layout.addLayout(left_stats, 1)
        stats_layout.addLayout(right_stats, 1)
        layout.addWidget(stats_group)

        # ── news widget ───────────────────────────────────────────────────────
        news_group = QGroupBox(self.tr("news_title"), home_page)
        news_vbox = QVBoxLayout(news_group)

        # Haber widget'ları için scroll area
        self._news_scroll = QScrollArea(home_page)
        self._news_scroll.setWidgetResizable(True)
        self._news_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._news_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Haber widget'ları için container
        self._news_container = QWidget()
        self._news_layout = QVBoxLayout(self._news_container)
        self._news_layout.setSpacing(2)
        self._news_layout.addStretch()
        
        self._news_scroll.setWidget(self._news_container)
        news_vbox.addWidget(self._news_scroll)

        # Yükleniyor placeholder'ı
        self._news_loading_label = QLabel(self.tr("news_loading"), self._news_container)
        self._news_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._news_loading_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
        self._news_layout.addWidget(self._news_loading_label)

        disclaimer = QLabel(self.tr("news_disclaimer"), home_page)
        disclaimer.setWordWrap(True)
        disclaimer.setStyleSheet("color: gray; font-size: 9pt;")
        news_vbox.addWidget(disclaimer)

        layout.addWidget(news_group, 1)

        self.home_led_label   = led_label
        self.home_power_label = power_label

        # ── start news poller ─────────────────────────────────────────────────
        lang = getattr(self, "_current_lang", "Türkçe")
        if not hasattr(self, "_news_poller") or self._news_poller is None:
            self._news_poller = NewsPoller(lang=lang, interval_ms=900_000, parent=self.window)
            self._news_poller.news_ready.connect(self._on_news_ready)
            self._news_poller.start()

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

    def _on_news_ready(self, items: list) -> None:
        """Haber scroll area'sını resimli widget'larla doldurur."""
        if not hasattr(self, "_news_layout"):
            return
        
        # Mevcut widget'ları temizle (sondaki stretch hariç)
        while self._news_layout.count() > 1:
            item = self._news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not items:
            no_news_label = QLabel(self.tr("news_unavailable"), self._news_container)
            no_news_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_news_label.setStyleSheet("color: #888; font-style: italic; padding: 20px;")
            self._news_layout.insertWidget(0, no_news_label)
            return
        
        # Haber widget'larını ekle
        for item in items:  # item: FeedItem
            news_widget = NewsItemWidget(item, self._news_container)
            news_widget.clicked.connect(self._open_news_url)
            self._news_layout.insertWidget(self._news_layout.count() - 1, news_widget)

    def _open_news_url(self, url: str) -> None:
        """Haber URL'sini tarayıcıda açar."""
        if url:
            QDesktopServices.openUrl(QUrl(url))
