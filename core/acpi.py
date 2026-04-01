import os

try:
    import pexpect  # type: ignore
except ModuleNotFoundError:
    pexpect = None

from .patch import (
    g15_5511_patch,
    g15_5515_patch,
    g15_5520_patch,
    g15_5530_patch,
    g16_7630_patch,
)


class ACPIMixin:
    """ACPI/hardware control and laptop model detection."""

    def _has_awelc_usb(self) -> bool:
        """Return True if an Alienware LED USB controller is present."""
        usb_root = "/sys/bus/usb/devices"
        if not os.path.isdir(usb_root):
            return False

        for entry in os.listdir(usb_root):
            base = os.path.join(usb_root, entry)
            vendor_p = os.path.join(base, "idVendor")
            product_p = os.path.join(base, "idProduct")
            try:
                with open(vendor_p, "r", encoding="utf-8", errors="ignore") as f:
                    vendor = f.read().strip().lower()
                with open(product_p, "r", encoding="utf-8", errors="ignore") as f:
                    product = f.read().strip().lower()
            except OSError:
                continue

            if vendor == "187c" and product in {"0550", "0551"}:
                return True
        return False

    def _detect_model_fallback(self):
        """Best-effort model detection from DMI for non-root startup paths."""
        paths = [
            "/sys/class/dmi/id/sys_vendor",
            "/sys/class/dmi/id/product_name",
            "/sys/class/dmi/id/product_version",
            "/sys/class/dmi/id/board_name",
        ]
        text_parts = []
        for p in paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text_parts.append(f.read().strip())
            except OSError:
                pass

        text = " ".join(text_parts).lower()
        if not text:
            return

        model_map = {
            "g15 5530": ("G15 5530", True, True),
            "g15 5525": ("G15 5525", True, True),
            "g15 5520": ("G15 5520", True, True),
            "g15 5511": ("G15 5511", True, True),
            "g15 5515": ("G15 5515", True, True),
            "g16 7630": ("G16 7630", True, False),
            "g16 7620": ("G16 7620", True, True),
            "alienware m16": ("Alienware M16", True, True),
        }
        for key, (model, supported, kb) in model_map.items():
            if key in text:
                self.model = model
                self.is_dell_g_series = supported
                self.is_keyboard_supported = kb
                return

        # If it is a Dell/Alienware machine but exact model is unknown.
        if "dell" in text or "alienware" in text:
            self.is_dell_g_series = False
            if self.model == "Unknown":
                product = next((p for p in text_parts if p), "Unknown")
                self.model = product

    def init_acpi_call(self):
        # Try detection early so Home page can show a meaningful model even without root.
        self._detect_model_fallback()
        # RGB support is hardware-USB based and can be true even on unsupported models.
        if self._has_awelc_usb():
            self.is_keyboard_supported = True

        if pexpect is None:
            self.is_root = False
            return

        self.acpi_call_dict = {
            "get_laptop_model": ["0x1a", "0x02", "0x02"],
            "get_power_mode":   ["0x14", "0x0b", "0x00"],
            "set_power_mode":   ["0x15", "0x01"],
            "toggle_G_mode":    ["0x25", "0x01"],
            "get_G_mode":       ["0x25", "0x02"],
            "set_fan1_boost":   ["0x15", "0x02", "0x32"],
            "get_fan1_boost":   ["0x14", "0x0c", "0x32"],
            "get_fan1_rpm":     ["0x14", "0x05", "0x32"],
            "get_cpu_temp":     ["0x14", "0x04", "0x01"],
            "set_fan2_boost":   ["0x15", "0x02", "0x33"],
            "get_fan2_boost":   ["0x14", "0x0c", "0x33"],
            "get_fan2_rpm":     ["0x14", "0x05", "0x33"],
            "get_gpu_temp":     ["0x14", "0x04", "0x06"],
        }

        self.is_root = False
        try:
            self.shell = pexpect.spawn(
                "bash",
                encoding="utf-8",
                logfile=self.logfile,
                env=None,
                args=["--noprofile", "--norc"],
            )
            self.shell.expect("[#$] ")
            self.shell_exec(" export HISTFILE=/dev/null; history -c")
            self.shell_exec("pkexec bash --noprofile --norc")
            self.shell_exec(" export HISTFILE=/dev/null; history -c")
            self.is_root = self.shell_exec("whoami")[1].find("root") != -1
            if not self.is_root:
                return
        except Exception:
            return

        self._check_laptop_model()
        if self.model == "Unknown":
            self._detect_model_fallback()
        if self._has_awelc_usb():
            self.is_keyboard_supported = True

    def _check_laptop_model(self):
        # Intel
        self.acpi_cmd = (
            'echo "\\\\_SB.AMWW.WMAX 0 {} {{{}, {}, {}, 0x00}}"'
            " | tee /proc/acpi/call; cat /proc/acpi/call"
        )
        laptop_model = self.acpi_call("get_laptop_model")

        if laptop_model == "0x0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5530"
            g15_5530_patch(self)
            return

        if laptop_model == "0x12c0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5520"
            g15_5520_patch(self)
            return

        if laptop_model == "0xc80":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5511"
            g15_5511_patch(self)
            return

        # G16 7630 check (orijinal davranış korunuyor)
        if laptop_model == "0x0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = False
            self.model = "G16 7630"
            g16_7630_patch(self)
            return

        # AMD
        self.acpi_cmd = (
            'echo "\\\\_SB.AMW3.WMAX 0 {} {{{}, {}, {}, 0x00}}"'
            " | tee /proc/acpi/call; cat /proc/acpi/call"
        )
        laptop_model = self.acpi_call("get_laptop_model")

        if laptop_model == "0x12c0":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5525"
            return

        if laptop_model == "0xc80":
            self.is_dell_g_series = True
            self.is_keyboard_supported = True
            self.model = "G15 5515"
            g15_5515_patch(self)

    def acpi_call(self, cmd, arg1="0x00", arg2="0x00"):
        args = self.acpi_call_dict[cmd]
        if len(args) == 4:
            cmd_current = self.acpi_cmd.format(args[0], args[1], args[2], args[3])
        elif len(args) == 3:
            cmd_current = self.acpi_cmd.format(args[0], args[1], args[2], arg1)
        elif len(args) == 2:
            cmd_current = self.acpi_cmd.format(args[0], args[1], arg1, arg2)
        else:
            cmd_current = ""
        return self.parse_shell_exec(self.shell_exec(cmd_current)[2])

    def shell_exec(self, cmd: str):
        self.shell.sendline(cmd)
        self.shell.expect("[#$] ")
        return self.shell.before.split("\n")

    def parse_shell_exec(self, line: str):
        return line[line.find("\r") + 1 : line.find("\x00")]
