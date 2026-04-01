import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QColor

class ColorWheel(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("RGB Renk Tekerleği")
        self.setGeometry(100, 100, 400, 400)

        self.color1 = QColor(255, 0, 0)  # Başlangıç rengi kırmızı
        self.color2 = QColor(0, 255, 0)  # Başlangıç rengi yeşil

        self.initUI()

    def initUI(self):
        # Layout
        layout = QVBoxLayout(self)

        # İlk renk etiketi ve kutusu
        self.label1 = QLabel("Henüz renk 1 seçilmedi", self)
        layout.addWidget(self.label1)

        self.color_display1 = QLabel(self)
        self.color_display1.setFixedSize(100, 50)
        self.color_display1.setStyleSheet("background-color: red;")
        layout.addWidget(self.color_display1)

        # İkinci renk etiketi ve kutusu
        self.label2 = QLabel("Henüz renk 2 seçilmedi", self)
        layout.addWidget(self.label2)

        self.color_display2 = QLabel(self)
        self.color_display2.setFixedSize(100, 50)
        self.color_display2.setStyleSheet("background-color: green;")
        layout.addWidget(self.color_display2)

        # Renk çarkı
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(50, 50, 300, 300)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.scene.setSceneRect(QRectF(0, 0, 300, 300))

        self.draw_color_wheel()

        layout.addWidget(self.view)

    def draw_color_wheel(self):
        # Çark için dairesel dilimler çiz
        for i in range(360):
            angle1 = i * math.pi / 180
            angle2 = (i + 1) * math.pi / 180
            r, g, b = self.rgb_from_angle(angle1)
            color = QColor(r, g, b)

            item = QGraphicsEllipseItem(0, 0, 300, 300)
            item.setStartAngle(i * 16)
            item.setSpanAngle(16)
            item.setBrush(QBrush(color))
            item.setPen(Qt.NoPen)
            self.scene.addItem(item)

        # Mouse tıklama olayı
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.viewport().installEventFilter(self)

    def rgb_from_angle(self, angle):
        """Açıyı RGB değerine çevir"""
        r = int((math.cos(angle) + 1) * 127)
        g = int((math.cos(angle - 2*math.pi/3) + 1) * 127)
        b = int((math.cos(angle - 4*math.pi/3) + 1) * 127)
        return r, g, b

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress and source is self.view.viewport():
            if event.button() == Qt.LeftButton:  # Sol tıklama, birinci renk seçimi
                self.select_color(event, self.label1, self.color_display1, 1)
            elif event.button() == Qt.RightButton:  # Sağ tıklama, ikinci renk seçimi
                self.select_color(event, self.label2, self.color_display2, 2)
            return True
        return False

    def select_color(self, event, label, color_display, color_number):
        x, y = event.pos().x() - 150, event.pos().y() - 150
        angle = (math.pi + (math.pi + -1 * math.atan2(y, x))) % (2 * math.pi)
        r, g, b = self.rgb_from_angle(angle)
        color = QColor(r, g, b)
        color_str = color.name()

        label.setText(f'Seçilen renk {color_number}: {color_str}')
        color_display.setStyleSheet(f"background-color: {color_str};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorWheel()
    window.show()
    sys.exit(app.exec_())
