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
        "tips_title":                    "İpuçları",
        "tips_text": (
            "💡 İpuçları:\n"
            "• Renk karelerine tıklayarak rengi seç\n"
            "• RGB sekmesinde parlaklığı ayarla\n"
            "• Fan hızlarını gerçek zamanlı izle\n"
            "• Sıcaklık limitlerini akıllıca kullan\n\n"
            "📖 Daha fazla bilgi için üzerine gel"
        ),
        # ── RGB page ─────────────────────────────────────────
        "duration": "Süre",
        "apply":    "Uygula",
        # ── Fan / Power page ─────────────────────────────────
        "power_and_fans":  "Güç ve Fanlar",
        "power_mode_label":"Güç Modu: ",
        "cpu_fan_boost":   "CPU Fan Güçlendirme",
        "gpu_fan_boost":   "GPU Fan Güçlendirme",
        "fan_root_warn":   "⚠️  Güç/Fan kontrolleri için root yetkisi gerekebilir (pkexec).",
        "fan_demo_warn":   "ℹ️  Demo Modu: Gerçek sıcaklık için root gerekiyor (pkexec python3 main.py)",
        "fan_manual_info": "ℹ️ Fan kontrolü 'Manual' modunda aktif olur.",
        # ── Settings page ────────────────────────────────────
        "performance":    "Performans",
        "disable_turbo":  "Turbo Boost'u Devre Dışı Bırak (deneysel)",
        "turbo_note":     "Henüz işlevsel değil (yalnızca UI). Daha sonra bağlanacak.",
        "thermals":       "Termal",
        "temp_limit":     "Sıcaklık Limiti",
        "language":       "Dil",
        "select_language":"Dil Seç:",
        # ── Info page ─────────────────────────────────────────
        "about_title":   "Tardix Komuta Merkezi Hakkında",
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
        "tips_title":                    "Tips & Info",
        "tips_text": (
            "💡 Tips:\n"
            "• Click color swatches to select a target\n"
            "• Adjust brightness in the RGB tab\n"
            "• Monitor fan speeds in real-time\n"
            "• Use temperature limits wisely\n\n"
            "📖 Hover over elements for more info"
        ),
        # ── RGB page ─────────────────────────────────────────
        "duration": "Duration",
        "apply":    "Apply",
        # ── Fan / Power page ─────────────────────────────────
        "power_and_fans":  "Power and Fans",
        "power_mode_label":"Power Mode: ",
        "cpu_fan_boost":   "CPU Fan Boost",
        "gpu_fan_boost":   "GPU Fan Boost",
        "fan_root_warn":   "⚠️  Power/Fan controls may require root (pkexec).",
        "fan_demo_warn":   "ℹ️  Demo Mode: Root required for real temperatures (pkexec python3 main.py)",
        "fan_manual_info": "ℹ️ Fan control is active in 'Manual' mode.",
        # ── Settings page ────────────────────────────────────
        "performance":    "Performance",
        "disable_turbo":  "Disable Turbo Boost (experimental)",
        "turbo_note":     "Not functional yet (UI only). This will be wired later.",
        "thermals":       "Thermals",
        "temp_limit":     "Temperature Limit",
        "language":       "Language",
        "select_language":"Select Language:",
        # ── Info page ─────────────────────────────────────────
        "about_title":   "About Tardix Command Center",
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
