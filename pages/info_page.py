from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.utils import _clear_layout


class InfoMixin:
    """Info/About page UI logic."""

    def _init_info_page(self):
        info_page = self.window.findChild(QWidget, "zinfo")
        if not info_page:
            return

        layout = info_page.layout()
        if layout:
            _clear_layout(layout)
        else:
            layout = QVBoxLayout(info_page)

        scroll = QScrollArea(info_page)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel(self.tr("about_title"))
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(title)

        desc_group = QGroupBox(self.tr("description"))
        desc_layout = QVBoxLayout(desc_group)
        desc_lbl = QLabel(self.tr("description_text"))
        desc_lbl.setWordWrap(True)
        desc_layout.addWidget(desc_lbl)
        scroll_layout.addWidget(desc_group)

        features_group = QGroupBox(self.tr("features"))
        features_layout = QVBoxLayout(features_group)
        features_layout.setSpacing(4)
        for item in self.tr("features_list"):
            lbl = QLabel(item)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            features_layout.addWidget(lbl)
        scroll_layout.addWidget(features_group)

        models_group = QGroupBox(self.tr("supported_models"))
        models_layout = QVBoxLayout(models_group)
        models_layout.setSpacing(3)
        for item in self.tr("models_list"):
            lbl = QLabel(item)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            models_layout.addWidget(lbl)
        scroll_layout.addWidget(models_group)

        credits_group = QGroupBox(self.tr("credits"))
        credits_layout = QVBoxLayout(credits_group)
        credits_lbl = QLabel(self.tr("credits_text"))
        credits_lbl.setWordWrap(True)
        credits_layout.addWidget(credits_lbl)
        scroll_layout.addWidget(credits_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
