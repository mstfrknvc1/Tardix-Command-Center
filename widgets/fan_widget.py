"""
Fan speed visualization widget with rotating animation
"""
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget


class FanWidget(QWidget):
    """Animates a rotating fan based on RPM value"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rpm = 0
        self.rotation = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_rotation)
        self.timer.start(50)  # Update every 50ms
        
    def set_rpm(self, rpm: int):
        """Set the RPM value (0-5000 range)"""
        self.rpm = max(0, min(5000, rpm))
        
    def _update_rotation(self):
        """Update rotation based on RPM"""
        if self.rpm > 0:
            # RPM to rotation speed (full rotation = 360 degrees)
            # 5000 RPM = fast rotation, 0 RPM = stationary
            rotation_speed = (self.rpm / 5000) * 36  # degrees per update
            self.rotation = (self.rotation + rotation_speed) % 360
            self.update()
            
    def paintEvent(self, event):
        """Draw the fan"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and size
        size = min(self.width(), self.height())
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = size / 2 - 10
        
        # Draw outer circle
        painter.setPen(QPen(QColor("#1C3F95"), 2))
        painter.setBrush(QBrush(QColor("#1a1a1a")))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                           int(radius * 2), int(radius * 2))
        
        # Save painter state for rotation
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation)
        
        # Draw 3 fan blades
        blade_color = QColor("#1C3F95")
        painter.setBrush(QBrush(blade_color))
        for i in range(3):
            painter.save()
            painter.rotate(i * 120)  # 3 blades equally spaced
            painter.drawEllipse(int(-radius * 0.3), int(-radius * 0.8),
                               int(radius * 0.6), int(radius * 0.6))
            painter.restore()
        
        painter.restore()
        
        # Draw center circle
        painter.setBrush(QBrush(QColor("#1C3F95")))
        painter.drawEllipse(int(center_x - 8), int(center_y - 8), 16, 16)
        
        # Draw RPM text
        painter.setPen(QPen(QColor("#e0e0e0")))
        painter.setFont(painter.font())
        painter.drawText(QRect(0, int(center_y + radius + 10), 
                              self.width(), 30),
                        Qt.AlignmentFlag.AlignCenter, 
                        f"{self.rpm} RPM")
