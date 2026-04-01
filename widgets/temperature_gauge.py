"""
Circular temperature gauge with circular progress bar
"""
import math
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget


class TemperatureGauge(QWidget):
    """Circular temperature gauge that shows temp with glowing effect"""
    
    def __init__(self, parent=None, max_temp: int = 100, label: str = ""):
        super().__init__(parent)
        self.temp = 0
        self.max_temp = max_temp
        self.label = label
        
    def set_temperature(self, temp: int):
        """Set the temperature value"""
        self.temp = max(0, min(self.max_temp, temp))
        self.update()
        
    def set_label(self, label: str):
        """Set the label text"""
        self.label = label
        self.update()
        
    def paintEvent(self, event):
        """Draw the temperature gauge"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        size = min(self.width(), self.height())
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = size / 2 - 15
        
        # Color based on temperature
        if self.temp < 60:
            color = QColor("#00ff9d")  # Green
        elif self.temp < 80:
            color = QColor("#ffcc00")  # Yellow
        else:
            color = QColor("#ff3333")  # Red
        
        # Draw background circle
        painter.setPen(QPen(QColor("#333333"), 2))
        painter.setBrush(QBrush(QColor("#1a1a1a")))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius),
                           int(radius * 2), int(radius * 2))
        
        # Draw circular progress bar (arc)
        pen = QPen(color, 6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Calculate arc angle
        progress = self.temp / self.max_temp
        start_angle = 90  # Start from top
        sweep_angle = -360 * progress  # Negative for clockwise
        
        # Draw arc
        arc_rect = QRect(int(center_x - radius), int(center_y - radius),
                        int(radius * 2), int(radius * 2))
        painter.drawArc(arc_rect, int(start_angle * 16), int(sweep_angle * 16))
        
        # Draw border circle
        painter.setPen(QPen(QColor("#1C3F95"), 3))
        painter.setBrush(QBrush())
        painter.drawEllipse(int(center_x - radius), int(center_y - radius),
                           int(radius * 2), int(radius * 2))
        
        # Draw temperature text in center
        painter.setPen(QPen(color))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        
        temp_text = f"{self.temp}°C"
        painter.drawText(QRect(int(center_x - radius), int(center_y - 30),
                              int(radius * 2), 50),
                        Qt.AlignmentFlag.AlignCenter, temp_text)
        
        # Draw label below
        if self.label:
            painter.setPen(QPen(QColor("#e0e0e0")))
            font.setPointSize(10)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(QRect(int(center_x - radius), int(center_y + 20),
                                  int(radius * 2), 30),
                            Qt.AlignmentFlag.AlignCenter, self.label)
