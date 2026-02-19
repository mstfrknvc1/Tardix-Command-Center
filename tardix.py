import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QStackedWidget, QPushButton
# Özel bileşeni import et
from color_wheel import ColorWheel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # UI Dosyasını Yükleme İşlemi
        self.load_ui()


    def load_ui(self):
        loader = QUiLoader()
        loader.registerCustomWidget(ColorWheel)

        ui_file = QFile("main.ui")
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Hata: main.ui dosyası açılamadı: {ui_file.errorString()}")
            sys.exit(-1)

        self.window = loader.load(ui_file)
        ui_file.close()

        if not self.window:
            print(loader.errorString())
            sys.exit(-1)

        self.main_stack = self.window.findChild(QStackedWidget, "stackedWidget")
        self.btn_home = self.window.findChild(QPushButton, "homebutton")
        self.btn_info = self.window.findChild(QPushButton, "infobutton")
        self.btn_rgb = self.window.findChild(QPushButton, "rgbbutton")
        self.btn_settings = self.window.findChild(QPushButton, "settingsbutton")
        self.btn_fan = self.window.findChild(QPushButton, "fanbutton")

        # Sayfa geçişleri için sinyal bağlantıları
# Sayfa geçişleri için sinyal bağlantıları
        if self.main_stack:
            self.btn_home.clicked.connect(lambda: self.main_stack.setCurrentIndex(0))  # Home
            self.btn_info.clicked.connect(lambda: self.main_stack.setCurrentIndex(4))  # Info
            self.btn_rgb.clicked.connect(lambda: self.main_stack.setCurrentIndex(2))  # RGB
            self.btn_settings.clicked.connect(lambda: self.main_stack.setCurrentIndex(3))  # Settings
            self.btn_fan.clicked.connect(lambda: self.main_stack.setCurrentIndex(1))  # Fan
        else:
            print("HATA: 'stackedWidget' bulunamadı! Designer'daki ismini kontrol et.")

        self.window.show()

        # --- Widget'a Erişim ve Sinyal Bağlama ---
        # Qt Designer'da widget'a verdiğiniz 'objectName' neyse onu yazın.
        # Örnek: 'widgetRenkSecici'
        self.renk_tekerlegi = self.window.findChild(ColorWheel, "colorwheel")

        if self.renk_tekerlegi:
            print("Renk Tekerleği Bulundu ve Bağlandı!")
            self.renk_tekerlegi.colorChanged.connect(self.renk_degisti)
        else:
            print("UYARI: 'widgetRenkSecici' isminde bir widget bulunamadı!")
            print("Lütfen Qt Designer'da objectName kısmını kontrol edin.")

    def renk_degisti(self, yeni_renk):
        # Renk kodunu al (#RRGGBB formatında)
        renk_kodu = yeni_renk.name()
        print(f"Seçilen Renk: {renk_kodu}")

        # Örnek: Seçilen rengi pencerenin arka planı yap
        # self.window.setStyleSheet(f"background-color: {renk_kodu};")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_app = MainWindow()
    # Not: MainWindow sınıfı içinde self.window.show() çağrıldığı için
    # burada tekrar main_app.show() demeye gerek yoktur.
    sys.exit(app.exec())
