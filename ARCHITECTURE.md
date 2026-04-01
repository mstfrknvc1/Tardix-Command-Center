# Tardix Command Center — Proje Mimarisi

Tardix Command Center, Dell G Serisi ve bazı Alienware laptoplar için yazılmış bir Python/PySide6 kontrol paneli uygulamasıdır. Klavye arka aydınlatması, güç modu ve fan hızı yönetimi sağlar.

---

## Dizin Yapısı

```
Tardix-Command-Center/
│
├── main.py                  ← Uygulama giriş noktası; TardixApp sınıfı + main()
├── main.ui                  ← Qt Designer UI tanımı (kenar çubuğu + sayfa iskeletleri)
├── requirements.txt         ← Python bağımlılıkları (PySide6, pexpect, pyusb)
├── 00-aw-elc.rules          ← udev kuralı (USB LED cihazı izinleri)
├── README.md
├── LICENSE.md
├── ARCHITECTURE.md          ← Bu dosya
│
├── core/                    ← Uygulama seviyesi mantık
│   ├── __init__.py
│   ├── utils.py             ← Paylaşılan yardımcılar: _clear_layout, _ClickFilter
│   ├── i18n.py              ← Türkçe / English çeviri sözlükleri
│   ├── patch.py             ← Model bazlı güç modu yamaları (G15/G16)
│   ├── acpi.py              ← ACPIMixin: ACPI kabuk çağrıları, model tespiti
│   ├── led_control.py       ← LEDMixin: apply_static/morph/color_and_morph, tray on/off
│   └── tray.py              ← TrayIcon (QSystemTrayIcon alt sınıfı)
│
├── hardware/                ← USB/HID LED sürücü kütüphanesi
│   ├── __init__.py
│   ├── awelc.py             ← Üst seviye LED API (set_static, set_morph, set_dim, …)
│   ├── elc.py               ← ELC protokol sınıfları ve USB iletişimi
│   ├── elc_constants.py     ← ELC protokol sabitleri
│   ├── hidreport.py         ← HID SetReport USB control transfer yardımcısı
│   └── rgbwheel.py          ← Eski PyQt5 renk tekerleği (arşiv; kullanımda değil)
│
├── widgets/                 ← Özel Qt bileşenleri
│   ├── __init__.py
│   ├── color_wheel.py       ← HSV renk tekerleği widget'ı (ColorWheel)
│   ├── fan_widget.py        ← Dönen fan animasyonu widget'ı (FanWidget)
│   └── temperature_gauge.py ← Dairesel sıcaklık göstergesi (TemperatureGauge)
│
├── pages/                   ← Sayfa Mixin sınıfları (TardixApp miras alır)
│   ├── __init__.py
│   ├── home_page.py         ← HomeMixin: _init_home_page, _toggle_leds
│   ├── rgb_page.py          ← RGBMixin: renk tekerleği, swatch seçimi, dim/duration
│   ├── fan_page.py          ← FanMixin: fan/güç sayfası, RPM polling
│   ├── settings_page.py     ← SettingsMixin: dil, turbo boost, sıcaklık limiti
│   ├── info_page.py         ← InfoMixin: hakkında/özellikler/desteklenen modeller
│   └── macro_page.py        ← MacroMixin: makro tuşu atamaları
│
├── assets/                  ← Statik dosyalar
│   ├── keyboard_preview.svg ← RGB sayfasında gösterilen klavye görseli
│   └── window.png           ← Uygulama ekran görüntüsü
│
├── Design/                  ← Tasarım kaynakları
│   ├── png/                 ← Uygulama ikonları
│   └── video/               ← Tanıtım videoları
│
└── tests/                   ← Geliştirici testleri
    ├── __init__.py
    └── test_widgets.py      ← Widget görsel testi (bağımsız çalıştırılabilir)
```

---

## Mimari Genel Bakış

```
main.py
└── TardixApp
    ├── Mixin sınıfları (çoklu miras)
    │   ├── pages/home_page.py   → HomeMixin
    │   ├── pages/rgb_page.py    → RGBMixin
    │   ├── pages/fan_page.py    → FanMixin
    │   ├── pages/settings_page.py → SettingsMixin
    │   ├── pages/info_page.py   → InfoMixin
    │   ├── pages/macro_page.py  → MacroMixin
    │   ├── core/led_control.py  → LEDMixin
    │   └── core/acpi.py         → ACPIMixin
    │
    ├── UI yükleme: main.ui (QUiLoader)
    ├── Çeviri: core/i18n.py → TRANSLATIONS
    ├── Ayarlar: QSettings("Tardix", "CommandCenter")
    └── Donanım erişimi:
        ├── hardware/awelc.py  ← USB LED (pyusb)
        └── core/acpi.py       ← ACPI kabuk (pexpect + pkexec)
```

### Mixin Deseni

`TardixApp`, tek tek sayfalara ait tüm yöntemleri Mixin sınıflarından miras alır. Her Mixin bir sayfanın başlatma (`_init_*`) ve olay işleyicilerini kapsüller. `main.py` yalnızca UI yükleme çekirdeğini ve `tr()` / `_retranslate_chrome()` metotlarını içerir.

### Dil Değişimi

Dil değiştiğinde `SettingsMixin._on_language_changed_handler()` tüm 6 sayfayı yeniden inşa eder ve `_retranslate_chrome()` ile kenar çubuğu araç ipuçlarını günceller. `core/i18n.py` içindeki `TRANSLATIONS` sözlüğü tüm UI metinlerini tutar.

### Donanım Katmanı

- **USB LED (awelc):** `hardware/awelc.py` → `hardware/elc.py` → `hardware/hidreport.py`. `pyusb` kurulu değilse `awelc = None` düşer ve tüm LED işlemleri sessizce devre dışı kalır.
- **ACPI:** `core/acpi.py`. `pexpect` kurulu değilse `is_root = False` olur ve fan/güç kontrolleri devre dışı kalır. Polkit ile `pkexec bash` aracılığıyla root erişimi kazanılır.

---

## Bağımlılıklar

| Paket | Kullanım | Zorunlu |
|-------|----------|---------|
| PySide6 | Tüm UI | ✅ |
| pexpect | ACPI/pkexec kabuk | ⚠️ (opsiyonel) |
| pyusb | USB LED kontrolü | ⚠️ (opsiyonel) |

Opsiyonel bağımlılıklar eksikse uygulama açılmaya devam eder; ilgili özellikler devre dışı kalır.

---

## Kurulum

```bash
# udev kuralını kopyala
sudo cp 00-aw-elc.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules

# Bağımlılıkları kur
pip install -r requirements.txt

# Çalıştır
python3 main.py
```
