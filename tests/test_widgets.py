#!/usr/bin/env python3
"""Quick test of new widgets"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from widgets.color_wheel import ColorWheel
from widgets.fan_widget import FanWidget
from widgets.temperature_gauge import TemperatureGauge
import sys

# Create QApplication first
app = QApplication(sys.argv)

print("Testing ColorWheel.setColor()...")
cw = ColorWheel()
cw.setColor(QColor(255, 0, 0))
print("✓ ColorWheel OK")

print("\nTesting FanWidget.set_rpm()...")
fw = FanWidget()
fw.set_rpm(3000)
print(f"✓ FanWidget OK (RPM: {fw.rpm})")

print("\nTesting TemperatureGauge.set_temperature()...")
tg = TemperatureGauge(label="CPU")
tg.set_temperature(70)
print(f"✓ TemperatureGauge OK (Temp: {tg.temp}°C)")

print("\n✓ All widgets working correctly!")
