from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from core.utils import _clear_layout


class MacroMixin:
    """Macro page UI logic."""

    def _init_macro_page(self):
        macro_page = self.window.findChild(QWidget, "macropage")
        if not macro_page:
            macro_page = QWidget()
            self.main_stack.addWidget(macro_page)

        layout = macro_page.layout()
        if layout:
            _clear_layout(layout)
        else:
            layout = QVBoxLayout(macro_page)

        title = QLabel(self.tr("macro_title"))
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        group = QGroupBox(self.tr("macro_group"), macro_page)
        group_layout = QVBoxLayout(group)
        macro_names = ["A (F2)", "B (F3)", "C (F4)", "D (F5)", "E (F6)"]
        self.macro_inputs = {}
        for name in macro_names:
            row = QHBoxLayout()
            lbl = QLabel(f"{name}:", macro_page)
            lbl.setMinimumWidth(80)
            row.addWidget(lbl)
            inp = QLineEdit(macro_page)
            inp.setPlaceholderText(self.tr("macro_placeholder"))
            key = name.split()[0]
            inp.setText(self.settings.value(f"Macro_{key}", ""))
            inp.textChanged.connect(
                lambda text, k=key: self.settings.setValue(f"Macro_{k}", text)
            )
            row.addWidget(inp, 1)
            self.macro_inputs[key] = inp
            group_layout.addLayout(row)

        layout.addWidget(group)
        info_lbl = QLabel(self.tr("macro_info"), macro_page)
        info_lbl.setWordWrap(True)
        layout.addWidget(info_lbl)
        layout.addStretch()
