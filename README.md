# Tardix Command Center

**Dell G Serisi ve bazı Alienware laptopları kontrol eden modern bir UI uygulaması**

Tardix, Dell G15/G16 ve Alienware M16 serisi laptopların klavye arka aydınlatması (RGB LED), güç modu ve fan hızını kontrol eden bir Python/PySide6 uygulamasıdır. Gerçekçi sensor verilerine dayalı animasyonlu dashboard ve Türkçe/İngilizce arayüz sunar.

---

## Özellikler

✅ **RGB Keyboard Control** — Statik renk, Morph, Color & Morph modları, kapatma  
✅ **Power Management** — Balanced, Performance, Quiet, FullSpeed, BatterySaver, G Mode, Manual  
✅ **Fan Control** — CPU ve GPU fan boost ayarı (root gerekli)  
✅ **Live Hardware Monitoring** — Real-time CPU/GPU sıcaklık ve fan RPM (psutil via alienware_wmi)  
✅ **Smooth Fan Animation** — Akıcı fan dönüşü, inertia-based yumuşak hız değişimleri  
✅ **System Tray** — LED quick toggle on/off (Sol tık = toggle, Sağ tık = menü)  
✅ **Dual Language UI** — Türkçe & English, hot-switch desteği  
✅ **Persistent Settings** — QSettings ile ayarlar kaydedilir  
✅ **Clean Modular Architecture** — core/, hardware/, widgets/, pages/ yapısı  

**Ek iyileştirmeler (Modernizasyon):**
- 1071-line monolith → 11 modüllü yapı
- Background thread sensor polling (jitter-free)
- Type hints & comprehensive exception handling

---

## Desteklenen Modeller

| Model | Güç Ayarları | Keyboard Backlight |
|-------|:----------:|:--:|
| G15 5530 | ✅ | ❓ |
| G15 5525 | ✅ | ✅ |
| G15 5520 | ✅ | ✅ |
| G15 5511 | ✅ | ✅ |
| G16 7620 | ✅ | ✅ |
| G16 7630 | ✅ | ✅ |
| Alienware M16 R1 | ✅ | ❓ |

---

## Gereksinimler

### Python Paketleri
```
PySide6 >= 6.0    # Qt UI framework
psutil            # Hardware sensors (CPU/GPU temp, fan RPM)
pexpect           # Optional: ACPI shell automation (power/fan control)
pyusb             # Optional: USB LED controller
```

### Sistem Paketleri
- `python3.10+`
- `polkit` (power/fan control ve ACPI çağrıları için)
- `acpi_call` kernel module
- `udev` (USB cihaz erişimi)

### USB LED Cihazı (Alienware 187c:0550)
udev kuralı gerekli — aşağıya bakın.

---

## Kurulum

### 1. udev Kuralı (USB LED erişimi için)
```bash
sudo cp 00-aw-elc.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2. Python Bağımlılıkları
```bash
pip install -r requirements.txt
```

### 3. ACPI Module (root/fan control için — opsiyonel)
```bash
sudo modprobe acpi_call
```

Kalıcı olarak yüklemek için:
```bash
echo "acpi_call" | sudo tee /etc/modules-load.d/tardix.conf
```

### 4. Keyboard Backlight Kuralı (opsiyonel)
Yalnızca root olmadan LED yazıp okuyacaksa:
```bash
# Cihaz yolunu bul
lsusb | grep "187c:0550"  # Bus 00X Device 00Y: ID 187c:0550 ...
```

---

## Çalıştırma

```bash
cd Tardix-Command-Center
python3 main.py
```

### Sistem Tray Entegrasyonu

Uygulamayı penceresiz çalıştırmak (tray'de başlar):
```bash
python3 main.py &
```

**Kısayollar:**
- Sol tık: LED hızlı toggle on/off
- Sağ tık: Menü (Show Window, Quit)

---

## Kullanım

### RGB Sayfası (Keyboard Backlight)

1. **Mode Seç:** Static Color, Morph, Color & Morph, Off
2. **Renk Seç:** Color wheel veya swatch tıkla
3. **Brightness:** Dim slider (0–100%)
4. **Animation Speed:** Duration slider (Morph modunda)
5. **Uygula:** Apply butonu

### Fan/Güç Sayfası

1. **Power Mode:** Balanced, Performance, Quiet, Full Speed, G Mode, Manual
2. **Manual Mode:** Fan boost sliderları etkinleşir
3. **Real-time Stats:** CPU/GPU temp ve fan RPM canlı yenilenir
4. **Demo Mode:** Root olmadan psutil sensor verisi gösterilir; ACPI yazamaz

### Ayarlar

- **Dil:** Türkçe ↔ English (hot-switch)
- **Turbo Boost:** CPU turbo boost toggle (root gerekli)
- **Sıcaklık Limiti:** Termal limit değiştirilmesi

### Hakkında

- Desteklenen modeller, linkler, özelliklerin listesi

---

## Proje Yapısı

```
Tardix-Command-Center/
├── main.py                 # Giriş noktası
├── main.ui                 # Qt Designer UI (kenar çubuğu + sayfa iskeletleri)
├── requirements.txt
├── ARCHITECTURE.md         # Detaylı mimari belgesi
├── CONTRIBUTING.md         # Geliştirici rehberi
│
├── core/                   # Uygulama mantığı
│   ├── utils.py           # _clear_layout, _ClickFilter
│   ├── i18n.py            # Türkçe/İngilizce çeviriler
│   ├── sensors.py         # psutil wrapper + SensorPoller (QThread)
│   ├── patch.py           # Model-based power mode patches
│   ├── acpi.py            # ACPI shell interface
│   ├── led_control.py     # apply_static/morph/color_and_morph
│   └── tray.py            # TrayIcon (system tray)
│
├── hardware/              # USB/HID LED driver
│   ├── awelc.py           # High-level LED API
│   ├── elc.py             # ELC protocol implementation
│   ├── elc_constants.py   # Protocol constants
│   ├── hidreport.py       # HID SetReport helper
│   └── rgbwheel.py        # Legacy PyQt5 (archived)
│
├── widgets/               # Custom Qt widgets
│   ├── color_wheel.py     # HSV color picker
│   ├── fan_widget.py      # Smooth fan animation (5 blades)
│   └── temperature_gauge.py
│
├── pages/                 # Page mixins (TardixApp miras alır)
│   ├── home_page.py       # System status, quick actions
│   ├── rgb_page.py        # Color wheel, swatch, brightness
│   ├── fan_page.py        # Fan/power, temperature gauges
│   ├── settings_page.py   # Language, turbo, temp limit
│   ├── info_page.py       # About, credits
│   └── macro_page.py      # Macro key bindings
│
├── tests/                 # Developer tests
│   └── test_widgets.py    # Widget standalone preview
│
└── assets/
    ├── keyboard_preview.svg
    └── window.png
```

Detaylı mimari → [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Geliştirme Özellikleri

### Mimari Yükseltmeler
- **Modülasyon:** 1071-line monolith → ayrı modüller (core, hardware, widgets, pages)
- **Mixin Pattern:** Her sayfanın sorumluluğu kendi sınıfında
- **Türkçe/İngilizce:** `core/i18n.py` tüm UI metinlerini kapsüller

### Sensör & Grafikleri Geliştirmeler
- **Real Hardware Sensors:** `alienware_wmi` hwmon driver via psutil
- **Background QThread:** Sensor okuma ana thread'i hiç bloklamaz (`SensorPoller`)
- **Smooth Fan Animation:** 60fps, 5-blade fan, inertia-based RPM smoothing
- **No Jitter:** Animation timer `dt` bound ile frame skipping önlenir

### Hat Kalitesi
- Full type hints (Python 3.10+)
- Exception handling tüm hardware çalışmaları
- Graceful degradation (root/USB olmadan bile sensor görünür)

---

## Lisans

GNU GENERAL PUBLIC LICENSE v3

Detaylar için [`LICENSE.md`](LICENSE.md) dosyasına bakın.

---

## Teşekkürler & Tarihçe

**Orijinal Proje:**
- [@cemkaya-mpi](https://github.com/cemkaya-mpi) — Dell-G-Series-Controller orijinal geliştiricisi
- [@trackmastersteve](https://github.com/trackmastersteve) — alienfx projesinden yararlanılan ACPI bilgisi
- [@AlexIII](https://github.com/AlexIII) ve [@T-Troll](https://github.com/T-Troll) — ACPI çağrıları ile ilgili yardım

**Modernizasyon (Furkan Avcı):**
Modülasyon, gerçek sensor okuma, smooth animasyon, Türkçe/İngilizce dil desteği, detaylı belgeleme

---

## İletişim & Katkı

Hata raporları, öneriler ve pull request'ler hoş karşılanır!

**Geliştirme rehberi:** [`CONTRIBUTING.md`](CONTRIBUTING.md)


## License
GNU GENERAL PUBLIC LICENSE v3

## Contributions
Written using the information and code from https://github.com/trackmastersteve/alienfx/issues/41. 

Many thanks to @AlexIII and @T-Troll for their help with the ACPI calls.

