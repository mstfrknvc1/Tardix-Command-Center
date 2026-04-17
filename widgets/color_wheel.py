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
        # Görsel parlaklık (wheel üzerindeki siyahlık perdesi).
        # Bu değer, Tardix UI'deki "Brightness" ayarından bağımsız olmalı.
        self.value = 1.0

    def setBrightness(self, val_float):
        self.value = val_float
        self.emitColor()
        self.update()

    def emitColor(self):
        # Renk seçimi wheel üzerinde "tam parlaklık" mantığıyla çalışsın.
        # (Parlaklık ayarı klavyeye uygulanacak; wheel görüntüsünü etkilemeyecek.)
        c = QColor.fromHsvF(self.hue, self.saturation, 1.0)
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
        # Wheel görüntüsünde parlaklık sabit (value=1.0) kalsın:
        # Siyah perdeyi çizme.

        # 4. Seçici
        angle_rad = math.radians((self.hue * 360) + 90)
        dist = self.saturation * radius
        sel_x = center.x() + dist * math.cos(angle_rad)
        sel_y = center.y() - dist * math.sin(angle_rad)

        # Seçici rengi (zıt renk olsun)
        stroke_color = QColor("black")
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

        # Wheel içi parlaklık slider'ını (eski davranış) kapalı tutuyoruz.
        # Parlaklık ayarı Tardix UI'deki ayrı slider ile klavyeye uygulanacak.
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 255)
        self.brightness_slider.setValue(255)
        self.brightness_slider.hide()

        # Tekerlek renk değiştirince dışarıya (tardix'e) sinyal ver
        self.canvas.colorChanged.connect(self.colorChanged)

    def on_brightness_changed(self, value):
        # Eski API uyumluluğu: çağrılsa bile wheel görünümünü etkilemesin.
        self.canvas.setBrightness(1.0)

    def setColor(self, color: QColor):
        """Set the color wheel to display a specific QColor.

        Only updates the visual position of the selector — does NOT emit
        colorChanged. Signal fires only on user mouse interaction.
        """
        h, s, v, a = color.getHsvF()
        if h < 0:  # -1 means achromatic
            h = 0
        self.canvas.hue = h
        self.canvas.saturation = s
        self.canvas.update()
