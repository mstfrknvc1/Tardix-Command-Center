import math
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QConicalGradient, QRadialGradient, QColor, QBrush, QPen, QMouseEvent

# --- Çizim Yapan İç Sınıf (Sadece Tekerlek) ---
class _WheelCanvas(QWidget):
    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)

        self.hue = 0.0
        self.saturation = 1.0
        self.value = 1.0 # Parlaklık dışarıdan (slider'dan) gelecek

    def setBrightness(self, val_float):
        self.value = val_float
        self.emitColor()
        self.update()

    def emitColor(self):
        c = QColor.fromHsvF(self.hue, self.saturation, self.value)
        self.colorChanged.emit(c)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2 - 10

        # 1. Renkler (Hue)
        h_gradient = QConicalGradient(center, 90)
        h_gradient.setColorAt(0.0, QColor("red"))
        h_gradient.setColorAt(60/360, QColor("yellow"))
        h_gradient.setColorAt(120/360, QColor("green"))
        h_gradient.setColorAt(180/360, QColor("cyan"))
        h_gradient.setColorAt(240/360, QColor("blue"))
        h_gradient.setColorAt(300/360, QColor("magenta"))
        h_gradient.setColorAt(1.0, QColor("red"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(h_gradient))
        painter.drawEllipse(center, int(radius), int(radius))

        # 2. Beyazlık (Saturation - Merkezden dışa)
        s_gradient = QRadialGradient(center, radius)
        s_gradient.setColorAt(0.0, QColor(255, 255, 255, 255))
        s_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(s_gradient))
        painter.drawEllipse(center, int(radius), int(radius))

        # 3. Siyahlık (Value - Üzerine siyah perde)
        black_overlay = QColor(0, 0, 0)
        alpha = int((1.0 - self.value) * 255)
        black_overlay.setAlpha(alpha)
        painter.setBrush(QBrush(black_overlay))
        painter.drawEllipse(center, int(radius), int(radius))

        # 4. Seçici
        angle_rad = math.radians((self.hue * 360) + 90)
        dist = self.saturation * radius
        sel_x = center.x() + dist * math.cos(angle_rad)
        sel_y = center.y() - dist * math.sin(angle_rad)

        # Seçici rengi (zıt renk olsun)
        stroke_color = QColor("white") if self.value < 0.5 else QColor("black")
        painter.setPen(QPen(stroke_color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(sel_x, sel_y), 8, 8)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.handleMouse(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.handleMouse(event.position())

    def handleMouse(self, pos):
        center = self.rect().center()
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        radius = min(self.rect().width(), self.rect().height()) / 2 - 10

        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0: angle += 360
        visual_angle = (angle - 90) % 360
        self.hue = visual_angle / 360.0

        dist = math.sqrt(dx**2 + dy**2)
        self.saturation = min(dist / radius, 1.0)

        self.emitColor()
        self.update()


# --- Ana Sınıf (Tardix'in İmport Ettiği) ---
class ColorWheel(QWidget):
    # Dışarıya yayınlanacak sinyal
    colorChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Dikey yerleşim: Üstte tekerlek, altta slider
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # Kenar boşluklarını sil

        # 1. Tekerleği ekle
        self.canvas = _WheelCanvas()
        layout.addWidget(self.canvas)

        # 2. Slider'ı ekle (Siyahlık/Parlaklık için)
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 255)
        self.brightness_slider.setValue(255) # Varsayılan tam parlak
        self.brightness_slider.setToolTip("Parlaklık / Siyahlık Ayarı")
        layout.addWidget(self.brightness_slider)

        # Bağlantılar
        # Slider değişince tekerleğe haber ver
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)

        # Tekerlek renk değiştirince dışarıya (tardix'e) sinyal ver
        self.canvas.colorChanged.connect(self.colorChanged)

    def on_brightness_changed(self, value):
        # 0-255 arasını 0.0-1.0 arasına çevir
        val_float = value / 255.0
        self.canvas.setBrightness(val_float)
