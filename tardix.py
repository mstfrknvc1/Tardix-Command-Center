import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt, QTimer

class AlienwareApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Alienware Control Center")
        self.setGeometry(100, 100, 800, 600)

        # --- 1. ANA TASARIM (QSS - Stil Dosyası) ---
        # Burası "CSS" gibidir. Renkleri, kenarları buradan ayarlarsın.
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212; /* Koyu Arka Plan */
            }
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #1e1e1e;
                color: #00ff99;  /* Neon Yeşili Yazı */
                border: 2px solid #00ff99; /* Neon Çerçeve */
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00ff99;
                color: #000000;
            }
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background-color: #00bcd4; /* Mavi Doluluk Rengi */
                border-radius: 3px;
            }
        """)

        # --- 2. ARAYÜZ ELEMANLARI ---
        layout = QVBoxLayout()

        # Başlık
        self.label_title = QLabel("SİSTEM DURUMU")
        self.label_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_title.setStyleSheet("font-size: 24px; color: #00bcd4; font-weight: bold;")
        layout.addWidget(self.label_title)

        # CPU Kullanım Çubuğu
        self.cpu_label = QLabel("CPU Kullanımı:")
        layout.addWidget(self.cpu_label)

        self.progress_cpu = QProgressBar()
        self.progress_cpu.setRange(0, 100)
        self.progress_cpu.setValue(45) # Örnek değer
        layout.addWidget(self.progress_cpu)

        # Fan Hızı Butonu
        self.btn_boost = QPushButton("TURBO FAN MODU: KAPALI")
        self.btn_boost.setCheckable(True) # Basılı kalma özelliği
        self.btn_boost.clicked.connect(self.toggle_fan_mode)
        layout.addWidget(self.btn_boost)

        # Boşluk bırak (Esnek yapı)
        layout.addStretch()

        # Widget'ları pencereye yerleştir
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def toggle_fan_mode(self):
        if self.btn_boost.isChecked():
            self.btn_boost.setText("TURBO FAN MODU: AÇIK")
            self.btn_boost.setStyleSheet("background-color: #ff0055; color: white; border: 2px solid #ff0055;")
        else:
            self.btn_boost.setText("TURBO FAN MODU: KAPALI")
            # Varsayılan stile dönmek için styleSheet'i sıfırlamak veya üzerine yazmak gerekebilir
            # Basitlik adına burada bırakıyorum.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlienwareApp()
    window.show()
    sys.exit(app.exec())
