import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

# Özel bileşeni import et
from color_wheel import ColorWheel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # UI Dosyasını Yükleme İşlemi
        self.load_ui()

    def load_ui(self):
        loader = QUiLoader()

        # --- KRİTİK NOKTA: Custom Widget'ı Tanıtma ---
        # Bunu yapmazsanız Qt Designer'daki promote işlemi çalışmaz.
        loader.registerCustomWidget(ColorWheel)

        ui_file = QFile("main.ui")
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Hata: main.ui dosyası açılamadı: {ui_file.errorString()}")
            sys.exit(-1)

        # UI dosyasını yükle ve pencereyi al
        self.window = loader.load(ui_file)
        ui_file.close()

        if not self.window:
            print(loader.errorString())
            sys.exit(-1)

        # Pencereyi göster
        self.window.show()

        # --- Widget'a Erişim ve Sinyal Bağlama ---
        # Qt Designer'da widget'a verdiğiniz 'objectName' neyse onu yazın.
        # Örnek: 'widgetRenkSecici'
        self.renk_tekerlegi = self.window.findChild(ColorWheel, "widgetRenkSecici")

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
