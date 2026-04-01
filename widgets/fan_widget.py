"""
Fan speed visualization widget with smooth rotating animation.
"""
import math
from PySide6.QtCore import Qt, QElapsedTimer, QRect, QTimer
from PySide6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QBrush,
    QLinearGradient, QRadialGradient,
)
from PySide6.QtWidgets import QWidget

# Blades
_BLADES      = 5
_BLADE_SWEEP = 55    # arc degrees swept by each blade
_BLADE_WIDTH = 0.42  # fraction of radius
_HUB_RATIO   = 0.14  # hub radius / fan radius

# Animation
_TICK_MS      = 16      # ~60 fps
_MAX_RPM      = 6000.0
# How fast RPM interpolates toward target (fraction per second, 0–1).
# Higher = snappier, lower = more inertia.
_INERTIA_UP   = 2.0    # spin-up rate  (reaches target in ~0.5 s)
_INERTIA_DOWN = 0.6    # spin-down rate (reaches 0 in ~1.7 s)


def _blade_path(r: float, sweep: float, width: float) -> QPainterPath:
    """
    Build a single blade path centred at origin pointing UP.

    The blade is an arc‑sector shape: two concentric arcs joined by
    straight edges, giving a curved, wing‑like appearance.
    """
    inner_r = r * 0.16
    outer_r = r * 0.90
    half_w  = sweep / 2.0
    tilt    = 20.0          # twist: outer edge leads by this many degrees

    path = QPainterPath()

    # Four corners (in polar → Cartesian)
    def pt(radius: float, angle_deg: float):
        a = math.radians(angle_deg - 90)
        return radius * math.cos(a), radius * math.sin(a)

    tl = pt(inner_r, -half_w)
    tr = pt(inner_r,  half_w)
    br = pt(outer_r,  half_w + tilt)
    bl = pt(outer_r, -half_w + tilt)

    path.moveTo(*tl)
    path.lineTo(*tr)
    # Outer arc (curves outward)
    path.quadTo(
        *pt(outer_r * 1.05, tilt),   # control point
        *br,
    )
    path.lineTo(*bl)
    # Inner arc (curves back)
    path.quadTo(
        *pt(inner_r * 0.9, 0),
        *tl,
    )
    path.closeSubpath()
    return path


class FanWidget(QWidget):
    """Smooth fan animation with inertia-based acceleration/deceleration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_rpm  = 0      # what set_rpm() last requested
        self._display_rpm = 0.0    # smoothed value used for drawing/label

        self._angle   = 0.0
        self._elapsed = QElapsedTimer()
        self._elapsed.start()
        self._last_ms = 0

        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── public ────────────────────────────────────────────────────────────
    def set_rpm(self, rpm: int):
        self._target_rpm = max(0, int(rpm))

    # ── animation ─────────────────────────────────────────────────────────
    def _tick(self):
        now = self._elapsed.elapsed()
        dt  = (now - self._last_ms) / 1000.0
        self._last_ms = now
        # Cap dt so a delayed timer fire never causes a visible angle jump.
        # At 60 fps the normal dt is ~0.016 s; allow up to 2 frames max.
        dt = min(dt, 0.033)

        rate = _INERTIA_UP if self._target_rpm > self._display_rpm else _INERTIA_DOWN
        alpha = 1.0 - math.exp(-rate * dt)
        self._display_rpm += alpha * (self._target_rpm - self._display_rpm)

        if self._display_rpm < 1.0:
            self._display_rpm = 0.0

        if self._display_rpm > 0:
            self._angle = (self._angle + (self._display_rpm / 60.0) * 360.0 * dt) % 360.0
        self.update()

    # ── paint ──────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h   = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r      = min(w, h) / 2.0 - 8

        # ── housing ring ──
        housing_grad = QRadialGradient(cx, cy, r)
        housing_grad.setColorAt(0.0,  QColor("#1a1a2e"))
        housing_grad.setColorAt(0.7,  QColor("#12122a"))
        housing_grad.setColorAt(1.0,  QColor("#0d0d1a"))
        painter.setPen(QPen(QColor("#2a3f7f"), 2))
        painter.setBrush(QBrush(housing_grad))
        painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

        # ── blades ────────────────────────────────────────────────────────
        blade_path = _blade_path(r * 0.88, _BLADE_SWEEP, _BLADE_WIDTH)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle)

        for i in range(_BLADES):
            painter.save()
            painter.rotate(i * (360.0 / _BLADES))

            # gradient: root dark → tip bright blue
            g = QLinearGradient(0, 0, 0, -r * 0.9)
            g.setColorAt(0.0, QColor("#1C3F95"))
            g.setColorAt(0.5, QColor("#2a5abd"))
            g.setColorAt(1.0, QColor("#4a8ae0"))
            painter.setBrush(QBrush(g))

            # subtle dark border
            painter.setPen(QPen(QColor("#0a1a40"), 1))
            painter.drawPath(blade_path)
            painter.restore()

        painter.restore()

        # ── hub cap ───────────────────────────────────────────────────────
        hub_r = r * _HUB_RATIO
        hub_grad = QRadialGradient(cx - hub_r * 0.3, cy - hub_r * 0.3, hub_r * 1.2)
        hub_grad.setColorAt(0.0, QColor("#5080d0"))
        hub_grad.setColorAt(1.0, QColor("#1C3F95"))
        painter.setBrush(QBrush(hub_grad))
        painter.setPen(QPen(QColor("#0a1830"), 1))
        painter.drawEllipse(int(cx - hub_r), int(cy - hub_r),
                            int(hub_r * 2), int(hub_r * 2))

        # ── RPM label ─────────────────────────────────────────────────────
        font = QFont("monospace", 8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#c8d8ff"))
        painter.drawText(
            QRect(0, int(cy + r + 4), w, 20),
            Qt.AlignmentFlag.AlignCenter,
            f"{int(self._display_rpm)} RPM",
        )
