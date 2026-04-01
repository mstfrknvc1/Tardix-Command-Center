from PySide6.QtCore import QEvent, QObject


def _clear_layout(layout):
    """Remove and delete all widgets from *layout*."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()


class _ClickFilter(QObject):
    """Event filter that invokes *callback* on mouse-button-release."""

    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self._cb = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonRelease:
            self._cb()
            return True
        return super().eventFilter(obj, event)
