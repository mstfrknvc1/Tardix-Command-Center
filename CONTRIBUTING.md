# Katkı Rehberi — Tardix Command Center

Tardix'a katkı sağladığınız için teşekkürler! Bu belge, projede hata düzeltme, yeni özellik ekleme veya yapı iyileştirmelerine nasıl katkı sağlayacağınızı açıklar.

---

## Hızlı Başlangıç

### 1. Ortam Hazırlığı

```bash
# Fork ve clone edin
git clone https://github.com/sizin-kullanıcıadı/Tardix-Command-Center.git
cd Tardix-Command-Center

# Python virtual environment
python3 -m venv tcc
source tcc/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 2. Çalıştırma & Test Etme

```bash
# Uygulamayı çalıştırın
python3 main.py

# Sözdizimi kontrol edin
python3 -m py_compile core/*.py hardware/*.py widgets/*.py pages/*.py
```

### 3. Değişiklik Yapın & Pull Request

```bash
git checkout -b feature/your-feature-name
# ... (kodunuzu değiştirin) ...
git add .
git commit -m "Feature: Açıklama (Title)" -m "Detaylı açıklama (Body)"
git push origin feature/your-feature-name
```

---

## Proje Yapısı

Kodunuzu nereye ekleyeceğinizi anlamak için bu rehberi izleyin:

### `core/` — Uygulama Mantığı & Yardımcı İşlevler

Tüm kullanım yapıları, çeviriler, sensor okuma, ACPI otomasyon, LED kontrol:

| Dosya | Amaç | Örnek Ekleme |
|-------|------|-----------|
| `utils.py` | Genel UI helpers | `_clear_layout()`, `_ClickFilter` |
| `i18n.py` | Türkçe/İngilizce çeviriler | Yeni dil desteği eklemek |
| `sensors.py` | psutil tabanlı sensor polling (QThread-safe) | Yeni sensor okuma fonksiyonu |
| `acpi.py` | ACPI shell arayüzü | Yeni güç modu komutu |
| `led_control.py` | RGB LED protokol mantığı | Morph modunu değiştirmek |
| `patch.py` | Model-bazlı patch'ler | Yeni laptop modelinin ACPI komutları |
| `tray.py` | Sistem tray ikon | Tray menüsünü özelleştirmek |

### `hardware/` — USB/HID LED Sürücü

Alienware 187c:0550 USB cihazla iletişim:

| Dosya | Amaç | Örnek Ekleme |
|-------|------|-----------|
| `awelc.py` | Üst düzey LED API (`apply_static()`, `apply_morph()`) | Yeni animasyon modu |
| `elc.py` | ELC protokol implementasyon | Protokol komutu değiştirmek |
| `elc_constants.py` | Sabit değerler | İzin verilen HID report türleri |
| `hidreport.py` | `usb_control_msg` wrapper | USB işletim komutu |

### `widgets/` — Özel Qt Widget'ları

Yeniden kullanılabilir, bağımsız UI bileşenleri:

| Dosya | Amaç | Örnek Ekleme |
|-------|------|-----------|
| `color_wheel.py` | HSV renk seçici | Yeni swatch modu |
| `fan_widget.py` | Animasyonlu fan 5 kanat | Turbin animasyon görüşü |
| `temperature_gauge.py` | Dairesel sıcaklık ölçüsü | Radyal gösterge |

**Kurallar:**
- Widget'lar bağımsız olmalıdır (hiçbir page sayfasına bağlı olmayacak)
- `__init__()` parametreleri sayısal/string olmalı (no page dependency)
- Signal'ler (`value_changed`, `color_selected`) geriye çağrılar için

### `pages/` — Kullanıcı Arabirim Sayfaları (Mixin Deseni)

Her sayfa ayrı bir Mixin sınıf (`TardixApp`'ı miras alır):

| Dosya | Sayfa | Mixin Sınıf |
|-------|-------|-----------|
| `home_page.py` | Anasayfa (Sistem durumu) | `HomeMixin` |
| `rgb_page.py` | RGB Kontrol (Renk, parlaklık) | `RGBMixin` |
| `fan_page.py` | Fan/Güç (Sıcaklık, RPM) | `FanMixin` |
| `settings_page.py` | Ayarlar (Dil, turbo, limit) | `SettingsMixin` |
| `info_page.py` | Hakkında (Bilgiler, kredi) | `InfoMixin` |
| `macro_page.py` | Makrolar (Tuş bağlamları) | `MacroMixin` |

**Mixin Deseni:**

```python
# pages/your_page.py
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class YourPageMixin:
    """Sayfanız için ek metodlar"""
    
    def _setup_your_page(self):
        """main.py'da TardixApp.__init__() sırasında çağrılır"""
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Your content here"))
        self.your_page_layout.addLayout(layout)
    
    def _on_your_event(self):
        """Slot için event handler"""
        self.your_label.setText("Updated!")
```

**main.py'da:**
```python
# main.py
from pages.your_page import YourPageMixin

class TardixApp(YourPageMixin, RGBMixin, FanMixin, ..., QMainWindow):
    def __init__(self):
        super().__init__()
        # ...
        self._setup_your_page()
```

### `tests/` — Test & Demo

```python
# tests/test_your_widget.py
from widgets.your_widget import YourWidget
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    widget = YourWidget()
    widget.show()
    app.exec()
```

---

## İş Parçacığı (Thread) Güvenliği — ÖNEMLİ

### ❌ YANLIŞ: Sensor Okuma UI Thread'te

```python
# ❌ Fan Page'de bunu yapma!
def _update_fan_speed(self):
    # Bu I/O engelleme ve animasyon jitter'ına neden olur!
    rpm = read_fan_rpm(1)  # ← 10-30ms blok!
    self.fan_widget.set_rpm(rpm)
```

### ✅ DOĞRU: SensorPoller QThread Kullan

```python
# ✅ Doğru yol (pages/fan_page.py'da kullanıldığı gibi)
from core.sensors import SensorPoller

class FanMixin:
    def _setup_fan_page(self):
        # ...
        self.sensor_poller = SensorPoller()
        self.sensor_poller.data_ready.connect(self._on_sensor_data)
        self.sensor_poller.start()
    
    def _on_sensor_data(self, fan1, cpu_temp, fan2, gpu_temp):
        # Qt otomatik olarak main thread'te çalıştırır (Signal/Slot)
        self.temperature_gauge.set_temp(cpu_temp)
        self.fan_widget.set_rpm(fan1)
```

### Thread Modeli

```
┌─────────────────────────────────────┐
│ Main Thread (UI/Animation)          │
│ ├─ 60fps animation timer            │
│ ├─ User clicks                      │
│ └─ draw/repaint                     │
└──────────────────────────────────────┘
        ↑                  ↓
        │ Signal emit      │ Queued
        │ (thread-safe)    │ Connection
        │                  ↓
┌──────────────────────────────────────┐
│ Sensor Worker Thread                 │
│ ├─ psutil.sensors_temperatures()     │
│ ├─ alienware_wmi hwmon read          │
│ └─ emit data_ready(values)           │
└──────────────────────────────────────┘
```

### Signal/Slot Emniyeti

```python
# ✅ DOĞRU: Queued (automatic with cross-thread)
worker.data_ready.connect(self._on_data)  # Auto-queued

# ❌ YANLIŞ: Direct call across threads
worker.direct_method()  # Race condition!
```

---

## Yeni Sayfa Ekleme

Örnek: "Performance Monitor" sayfası ekleyin

### 1. Sayfa Sınıfı Oluşturun

```python
# pages/performance_page.py
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from widgets.temperature_gauge import TemperatureGauge
from core.sensors import SensorPoller

class PerformanceMixin:
    def _setup_performance_page(self):
        """main.py'da TardixApp.__init__() sırasında çağrılır"""
        layout = QVBoxLayout()
        
        # Widget'lar
        self.perf_gauge = TemperatureGauge()
        self.perf_label = QLabel("Başlıyor...")
        
        layout.addWidget(self.perf_label)
        layout.addWidget(self.perf_gauge)
        
        # Sensor polling
        self.perf_poller = SensorPoller()
        self.perf_poller.data_ready.connect(self._on_perf_sensor_data)
        self.perf_poller.start()
        
        self.performance_page_layout.addLayout(layout)
    
    def _on_perf_sensor_data(self, fan1, cpu_temp, fan2, gpu_temp):
        """Sensor veri geldi (Signal/Slot, main thread'te çalışır)"""
        self.perf_label.setText(f"CPU: {cpu_temp}°C | GPU: {gpu_temp}°C")
        self.perf_gauge.set_temp(cpu_temp)
```

### 2. main.ui'ye Tab Ekleyin

Qt Designer'da:
- `stackedWidget` seçin
- Sayfaya "Performance" adlı yeni `QWidget` ekleyin
- Bu widget'ın `ObjectName` = `performance_page` olacak
- İçine bir `QVBoxLayout` yerleştirin, `ObjectName` = `performance_page_layout`

### 3. main.py'da Mixin'i Dahil Edin

```python
# main.py
from pages.performance_page import PerformanceMixin

class TardixApp(
    PerformanceMixin,  # ← Yeni
    HomeMixin,
    RGBMixin,
    FanMixin,
    SettingsMixin,
    InfoMixin,
    MacroMixin,
    QMainWindow
):
    def __init__(self):
        super().__init__()
        # ...
        
        # Sidebar buton ekleyin
        # (bu önceden yapılmış olabilir)
        self.performance_page_btn = QPushButton("Performance")
        self.performance_page_btn.clicked.connect(
            lambda: self.stackedWidget.setCurrentWidget(self.performance_page)
        )
        self.sidebar_layout.addWidget(self.performance_page_btn)
        
        # Sayfa kurulumunu çalıştırın
        self._setup_performance_page()
```

---

## Yeni Sensor Okuma Ekleme

Örnek: "GPU Fan Speed" ekleyin

### 1. Okuma Fonksiyonu Ekleyin

```python
# core/sensors.py
def read_gpu_fan_rpm(fan_num=1):
    """GPU fan RPM'i psutil aracılığıyla oku"""
    try:
        fans = psutil.sensors_fans().get('acpi-fan-gpu', [])
        if fan_num <= len(fans):
            return fans[fan_num - 1].current
    except (AttributeError, OSError):
        pass
    return 0
```

### 2. SensorPoller'ı Genişletin

```python
# core/sensors.py - _SensorWorker sınıfında
class _SensorWorker(QObject):
    data_ready = pyqtSignal(int, float, int, float, int)  # ← Yeni param ekle
    
    def run(self):
        while self.running:
            try:
                fan1 = read_fan_rpm(1) or 0
                cpu = read_cpu_temp() or 0
                fan2 = read_fan_rpm(2) or 0
                gpu = read_gpu_temp() or 0
                gpu_fan = read_gpu_fan_rpm() or 0  # ← Yeni
                
                self.data_ready.emit(fan1, cpu, fan2, gpu, gpu_fan)
            except Exception:
                pass
            
            time.sleep(self.update_interval)
```

### 3. Sayfada Slot'ı Güncelle

```python
# pages/fan_page.py
def _on_sensor_data(self, fan1, cpu_temp, fan2, gpu_temp, gpu_fan):  # ← Yeni param
    # ...
    self.gpu_fan_label.setText(f"GPU Fan: {gpu_fan} RPM")
```

---

## Hata Giderme & Sözdizimi Kontrolü

### Sözdizimi Hatalarını Kontrol Edin

```bash
python3 -m py_compile core/*.py hardware/*.py widgets/*.py pages/*.py tests/*.py
# Hata yoksa sessizce bitir
```

### Çalıştırma Sırasında Debug

```bash
# Verbose output
python3 -u main.py

# pdb ile debug
python3 -m pdb main.py
```

### Sık Hatalar

| Hata | Sebep | Çözüm |
|------|-------|-------|
| `ImportError: no module named 'pages.your_page'` | Dosya eksik veya yanlış konum | Dosya adı kontrol edin, `__init__.py` var mı? |
| `RuntimeError: Cannot use GUI from non-main thread` | Widget UI thread'te oluşturuldu | QtCore.QThread + Signal/Slot kullanın |
| `AttributeError: object has no attribute 'sensor_data'` | Signal tanımlı değil | Mixin'de `pyqtSignal` bildir |
| Jitter her 1-2 saniyede | Sensor okuma UI thread'i blokluyor | SensorPoller'a geçin |

---

## Deneme & Onay Süreci

### Pre-Commit Checklist

- [ ] Sözdizimi öğesi yok (`python3 -m py_compile ...`)
- [ ] Uygulamayı başlatırsınız ve çalışır (`python3 main.py`)
- [ ] UI responsive kalır (animasyon jitter yok, tıklar yan etki yok)
- [ ] Yeni feature çalışıyor
- [ ] Eski feature'lar hala çalışıyor

### Test Sayfaları

```bash
# Bağımsız widget testi
python3 tests/test_widgets.py
```

### Pull Request Değerlendirmesi

PR'niz şunları içermelidir:
- ✅ Net başlık + açıklama
- ✅ Düzeltilen hata referansı veya benimsenen özellik
- ✅ Sözdizimi kontrolü geçti
- ✅ Thread güvenliği onayı (QThread/Signal/Slot deseni)
- ✅ Önceki özellikler bozulmadı

---

## İletişim & Soru

**Sorularınız var mı?**
- GitHub Issues açın: Bug raporları, özellik istekleri, tartışmalar
- Pull Request: Kod gözden geçirmesi için önerilerin tartışılması

**Topluluk Kuralları:**
- Saygılı, yapıcı dil kullanın
- Kodunuz hakkında açık olun
- Ekip üyeleri gönüllüdür — sabırla cevap bekleyin

---

## Ek Kaynaklar

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — Detaylı proje mimarisi
- [`README.md`](README.md) — Kullanıcı rehberi
- [PySide6 Docs](https://doc.qt.io/qtforpython-6/) — Qt/QThread/Signal/Slot
- [psutil Docs](https://psutil.readthedocs.io/) — Sensor API

---

**Teşekkürler!** 🚀
