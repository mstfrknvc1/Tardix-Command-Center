"""
Tardix Command Center – UI translations.
Add / edit strings here; the app calls self.tr(key) to look them up.
List values (features_list, models_list) are returned as-is by tr().
"""

TRANSLATIONS: dict[str, dict] = {
    "Türkçe": {
        # ── Sidebar tooltips ──────────────────────────────────
        "btn_home_tooltip":     "Ana Sayfa",
        "btn_fan_tooltip":      "Fan / Güç",
        "btn_rgb_tooltip":      "RGB Işıklandırma",
        "btn_macro_tooltip":    "Makrolar",
        "btn_settings_tooltip": "Ayarlar",
        "btn_info_tooltip":     "Hakkında",
        # ── Window ───────────────────────────────────────────
        "window_title": "Tardix Komuta Merkezi",
        # ── Home page ────────────────────────────────────────
        "home_title":                    "Tardix Komuta Merkezi",
        "system_status":                 "Sistem Durumu",
        "laptop_model_label":            "Laptop Modeli: {model}",
        "keyboard_backlight_supported":  "Klavye Arka Işığı: ✓ Destekleniyor",
        "keyboard_backlight_unsupported":"Klavye Arka Işığı: ✗ Desteklenmiyor",
        "power_mode_status":             "Güç Modu: {mode}",
        "led_status":                    "LED Durumu: {state} ({action})",
        "quick_actions":                 "Hızlı İşlemler",
        "toggle_leds":                   "LED Aç/Kapat",
        "go_rgb":                        "RGB Kontrole Git",
        "go_fan":                        "Fan Kontrole Git",
        "go_settings":                   "Ayarlara Git",
        # ── News widget ───────────────────────────────────────
        "news_title":      "Oyun & Teknoloji Haberleri",
        "news_loading":    "⏳ Haberler yükleniyor...",
        "news_unavailable": "⚠️  Haberler şu an kullanılamıyor (internet bağlantısı gerekli).",
        "news_disclaimer": (
            "ⓘ  Bu başlıklar herkese açık RSS akışlarından otomatik olarak alınmaktadır. "
            "Tüm içerikler ilgili yayıncıların mülküdür. "
            "Tardix Command Center içeriğin doğruluğundan ya da erişilebilirliğinden sorumlu değildir."
        ),
        # ── RGB page ─────────────────────────────────────────
        "duration": "Süre",
        "speed": "Hız",
        "apply":    "Uygula",
        "rgb_mode_static": "Sabit Renk",
        "rgb_mode_morph": "Geçişli",
        "rgb_mode_rgb": "RGB Döngü",
        "rgb_mode_dual_morph": "Çift Renk Geçişi",
        "rgb_mode_windows_setting": "Windows Ayarını Kullan",
        "rgb_mode_off": "Kapalı",
        "rgb_target_static": "Sabit",
        "rgb_target_morph": "Geçiş",
        # ── Fan / Power page ─────────────────────────────────
        "power_and_fans":  "Güç ve Fanlar",
        "power_mode_label":"Güç Modu: ",
        "apply_power_profile": "Güç Profilini Onayla",
        "power_mode_ustt_balanced": "Dengeli",
        "power_mode_ustt_performance": "Performans",
        "power_mode_ustt_quiet": "Sessiz",
        "power_mode_ustt_fullspeed": "Tam Hız",
        "power_mode_ustt_batterysaver": "Pil Tasarrufu",
        "power_mode_g_mode": "G Modu",
        "power_mode_manual": "Manuel",
        "cpu_fan_boost":   "CPU Fan Güçlendirme",
        "gpu_fan_boost":   "GPU Fan Güçlendirme",
        "fan_root_warn":   "⚠️  Güç/Fan kontrolleri için root yetkisi gerekebilir (pkexec).",
        "fan_demo_warn":   "ℹ️  Demo Modu: Gerçek sıcaklık için root gerekiyor (pkexec python3 main.py)",
        "fan_manual_info": "ℹ️ Fan kontrolü 'Manual' modunda aktif olur.",
        "switch_power_backend": "Backend Değiştir",
        "power_backend_current": "Aktif güç backend'i: {backend}",
        "power_backend_acpi": "Dell ACPI (WMAX)",
        "power_backend_platform_profile": "Linux platform_profile (dağıtım/çekirdek kuralları)",
        "power_backend_none": "Özel backend bulunamadı",
        "power_backend_switched": "Güç backend değişti: {backend}",
        "power_backend_switch_unavailable": "Kullanılabilir başka güç backend'i bulunamadı.",
        "power_backend_apply_ok": "Güç modu ayarlandı: {mode} (platform_profile={mapped})",
        "power_backend_apply_fail": "Güç modu uygulanamadı: {mode} (platform_profile={mapped})",
        # ── Settings page ────────────────────────────────────
        "performance":    "Performans",
        "disable_turbo":  "Turbo Boost'u Devre Dışı Bırak",
        "turbo_note":     "Desteklenen modellerde sysfs üzerinden çalışır (root gerekli).",
        "autostart":      "Açılışta Otomatik Başlat",
        "autostart_note": "Masaüstü oturumu açıldığında otomatik başlar (~/.config/autostart/).",
        "autostart_section": "Başlangıç",
        "unsupported_model_title": "Desteklenmeyen Model",
        "unsupported_model_msg": (
            "Bu laptop modeli desteklenen listesinde değil.\n\n"
            "Klavye arka ışığı Alienware USB LED varsa çalışabilir, "
            "ancak güç/fan kontrolleri çalışmayabilir.\n\n"
            "Kendi sorumluluğunuzda kullanın."
        ),
        "thermals":       "Termal",
        "temp_limit":     "Sıcaklık Limiti",
        "language":       "Dil",
        "select_language":"Dil Seç:",
        # ── Info page ─────────────────────────────────────────
        "about_title":   "Tardix Komuta Merkezi Hakkında",
        "version_group": "Sürüm",
        "version_text": "<b>Sürüm:</b> {version}<br><b>Adlandırma:</b> {scheme}",
        "description":   "Açıklama",
        "description_text": (
            "Tardix Komuta Merkezi, Dell G Series laptoplar için "
            "klavye arka ışığını, güç modunu ve fan hızını kontrol etmek için "
            "tasarlanmış kullanıcı dostu bir GUI uygulamasıdır."
        ),
        "features": "Özellikler",
        "features_list": [
            "🎨 RGB Klavye Arka Işığı (Static, Morph modu)",
            "⚡ Güç Modu Ayarı (Balanced, Performance, Quiet)",
            "❄️ Fan Hızı ve Boost Kontrolü",
            "🌡️ Gerçek-Zamanlı CPU/GPU Sıcaklık",
            "📊 Fan RPM Animasyonu",
            "⚙️ Sıcaklık Limiti (85-100°C)",
            "💾 Ayarları Otomatik Kaydet",
        ],
        "supported_models": "Desteklenen Modeller",
        "models_list": [
            "✓ Dell G15 5530 (Intel)",
            "✓ Dell G15 5520 (Intel)",
            "✓ Dell G15 5511 (Intel)",
            "✓ Dell G15 5525 (AMD)",
            "✓ Dell G16 7630 (Intel)",
            "✓ Alienware M16 R1",
        ],
        "credits": "Bilgi & Lisans",
        "credits_text": (
            "<b>Orijinal Proje:</b> Cem Kaya<br>"
            "<b>Bu Sürüm:</b> Furkan Avcı<br>"
            "<b>Lisans:</b> GPL-3.0<br><br>"
            "<b>⚠️ Sorumluluk Reddi:</b><br>"
            "Bu yazılım test edilmiş olsa da, hatalı kullanım "
            "durumunda cihazınıza zarar verebilir. "
            "Kendi sorumluluğunuzda kullanın."
        ),
        # ── Macro page ────────────────────────────────────────
        "macro_title":       "Makro Ayarları (F2-F6)",
        "macro_group":       "Fonksiyon Tuşlarına Makro Ata",
        "macro_placeholder": "Makro komutunu girin (şu an işlevsel değil)",
        "macro_info": (
            "ℹ️ Not: Makro sistemi şu an işlevsel olmayabilir. "
            "F2-F6 tuşlarına komut ataması yapabilirsiniz."
        ),
        # ── Messages ─────────────────────────────────────────
        "lang_changed_title": "Dil",
        "lang_changed_msg":   "Dil {lang} olarak değiştirildi.",
    },

    "English": {
        # ── Sidebar tooltips ──────────────────────────────────
        "btn_home_tooltip":     "Home",
        "btn_fan_tooltip":      "Fan / Power",
        "btn_rgb_tooltip":      "RGB Lighting",
        "btn_macro_tooltip":    "Macros",
        "btn_settings_tooltip": "Settings",
        "btn_info_tooltip":     "About",
        # ── Window ───────────────────────────────────────────
        "window_title": "Tardix Command Center",
        # ── Home page ────────────────────────────────────────
        "home_title":                    "Tardix Command Center",
        "system_status":                 "System Status",
        "laptop_model_label":            "Laptop Model: {model}",
        "keyboard_backlight_supported":  "Keyboard Backlight: ✓ Supported",
        "keyboard_backlight_unsupported":"Keyboard Backlight: ✗ Not Supported",
        "power_mode_status":             "Power Mode: {mode}",
        "led_status":                    "LED Status: {state} ({action})",
        "quick_actions":                 "Quick Actions",
        "toggle_leds":                   "Toggle LEDs",
        "go_rgb":                        "Go to RGB Control",
        "go_fan":                        "Go to Fan Control",
        "go_settings":                   "Go to Settings",
        # ── News widget ───────────────────────────────────────
        "news_title":      "Gaming & Technology News",
        "news_loading":    "⏳ Loading news...",
        "news_unavailable": "⚠️  News is currently unavailable (internet connection required).",
        "news_disclaimer": (
            "ⓘ  Headlines are fetched automatically from publicly available RSS feeds. "
            "All content remains the property of the respective publishers. "
            "Tardix Command Center is not responsible for the accuracy or availability of third-party content."
        ),
        # ── RGB page ─────────────────────────────────────────
        "duration": "Duration",
        "speed": "Speed",
        "apply":    "Apply",
        "rgb_mode_static": "Static Color",
        "rgb_mode_morph": "Morph",
        "rgb_mode_rgb": "RGB Cycle",
        "rgb_mode_dual_morph": "Dual Morph",
        "rgb_mode_windows_setting": "Use Windows Setting",
        "rgb_mode_off": "Off",
        "rgb_target_static": "Static",
        "rgb_target_morph": "Morph",
        # ── Fan / Power page ─────────────────────────────────
        "power_and_fans":  "Power and Fans",
        "power_mode_label":"Power Mode: ",
        "apply_power_profile": "Apply Power Profile",
        "power_mode_ustt_balanced": "Balanced",
        "power_mode_ustt_performance": "Performance",
        "power_mode_ustt_quiet": "Quiet",
        "power_mode_ustt_fullspeed": "Full Speed",
        "power_mode_ustt_batterysaver": "Battery Saver",
        "power_mode_g_mode": "G Mode",
        "power_mode_manual": "Manual",
        "cpu_fan_boost":   "CPU Fan Boost",
        "gpu_fan_boost":   "GPU Fan Boost",
        "fan_root_warn":   "⚠️  Power/Fan controls may require root (pkexec).",
        "fan_demo_warn":   "ℹ️  Demo Mode: Root required for real temperatures (pkexec python3 main.py)",
        "fan_manual_info": "ℹ️ Fan control is active in 'Manual' mode.",
        "switch_power_backend": "Switch Backend",
        "power_backend_current": "Active power backend: {backend}",
        "power_backend_acpi": "Dell ACPI (WMAX)",
        "power_backend_platform_profile": "Linux platform_profile (distro/kernel rules)",
        "power_backend_none": "No special backend detected",
        "power_backend_switched": "Power backend switched: {backend}",
        "power_backend_switch_unavailable": "No alternate power backend is available.",
        "power_backend_apply_ok": "Power mode applied: {mode} (platform_profile={mapped})",
        "power_backend_apply_fail": "Failed to apply power mode: {mode} (platform_profile={mapped})",
        # ── Settings page ────────────────────────────────────
        "performance":    "Performance",
        "disable_turbo":  "Disable Turbo Boost",
        "turbo_note":     "Works via sysfs on supported models (requires root).",
        "autostart":      "Start on Boot",
        "autostart_note": "Auto-starts on desktop login (creates .desktop in ~/.config/autostart/).",
        "autostart_section": "Startup",
        "unsupported_model_title": "Unsupported Model",
        "unsupported_model_msg": (
            "This laptop model is not on the supported list.\n\n"
            "Keyboard backlight may work if your device has an Alienware USB LED. "
            "Power/fan controls may not function.\n\n"
            "Use at your own risk."
        ),
        "thermals":       "Thermals",
        "temp_limit":     "Temperature Limit",
        "language":       "Language",
        "select_language":"Select Language:",
        # ── Info page ─────────────────────────────────────────
        "about_title":   "About Tardix Command Center",
        "version_group": "Version",
        "version_text": "<b>Version:</b> {version}<br><b>Scheme:</b> {scheme}",
        "description":   "Description",
        "description_text": (
            "Tardix Command Center is a user-friendly GUI application "
            "designed to control keyboard backlight, power mode, and fan speed "
            "for Dell G Series laptops."
        ),
        "features": "Features",
        "features_list": [
            "🎨 RGB Keyboard Backlight (Static, Morph mode)",
            "⚡ Power Mode Setting (Balanced, Performance, Quiet)",
            "❄️ Fan Speed and Boost Control",
            "🌡️ Real-Time CPU/GPU Temperature",
            "📊 Fan RPM Animation",
            "⚙️ Temperature Limit (85-100°C)",
            "💾 Auto-Save Settings",
        ],
        "supported_models": "Supported Models",
        "models_list": [
            "✓ Dell G15 5530 (Intel)",
            "✓ Dell G15 5520 (Intel)",
            "✓ Dell G15 5511 (Intel)",
            "✓ Dell G15 5525 (AMD)",
            "✓ Dell G16 7630 (Intel)",
            "✓ Alienware M16 R1",
        ],
        "credits": "Info & License",
        "credits_text": (
            "<b>Original Project:</b> Cem Kaya<br>"
            "<b>This Version:</b> Furkan Avcı<br>"
            "<b>License:</b> GPL-3.0<br><br>"
            "<b>⚠️ Disclaimer:</b><br>"
            "Although this software has been tested, improper use "
            "may damage your device. "
            "Use at your own risk."
        ),
        # ── Macro page ────────────────────────────────────────
        "macro_title":       "Macro Settings (F2-F6)",
        "macro_group":       "Assign Macros to Function Keys",
        "macro_placeholder": "Enter macro command (not functional yet)",
        "macro_info": (
            "ℹ️ Note: Macro system may not be functional yet. "
            "You can assign commands to F2-F6 keys."
        ),
        # ── Messages ─────────────────────────────────────────
        "lang_changed_title": "Language",
        "lang_changed_msg":   "Language changed to {lang}.",
    },
}
