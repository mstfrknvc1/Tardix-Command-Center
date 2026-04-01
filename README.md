# Tardix Command Center

Modern Linux control panel for supported Dell G-series and Alienware systems.

This project is a fork and continuation of:
- https://github.com/cemkaya-mpi/Dell-G-Series-Controller

## What It Does
- Keyboard RGB control (Static, Morph, Color and Morph, Off)
- Power mode controls (ACPI or platform_profile backend)
- Fan boost controls (supported models and permissions required)
- Live CPU/GPU temperature and RPM monitoring
- Tray integration, Turkish/English UI, persistent settings

## New in This Fork
- Modular architecture (`core`, `pages`, `widgets`, `hardware`)
- Background sensor polling (smooth UI, less stutter)
- Backend visibility and switching in Fan/Power page
- XDG-style install flow with `tcc` launcher, desktop integration, and uninstall support

## Version and Metadata
- Application version and desktop metadata are centralized in `core/app_meta.py`.
- The current version is exposed in the app info page and generated desktop metadata from that single source.
- Installer, autostart entry, Qt app metadata, and info page read from the same metadata source.

## Supported Hardware Notes
- ACPI power/fan controls are model and firmware dependent.
- RGB support depends on Alienware LED USB controller availability.
- Even if model is not listed, RGB may still work if USB controller is present.

## Quick Setup
Run:

```bash
./setup.sh
```

`setup.sh` will:
- install missing dependencies (Debian/Ubuntu and Arch)
- create/update virtual environment and Python packages
- install udev rule and polkit rule
- load/persist `acpi_call` module (if available)
- build executable with PyInstaller (fallback to venv launcher)
- install the app under `~/.local/share/tardix-command-center`
- create launcher script: `~/.local/bin/tcc`
- create desktop entry and a disabled user service
- generate `uninstall.sh`

## Start Application
```bash
tcc
```

Alternative:
```bash
tcc --background
```

Development run from repo:

```bash
python3 main.py
```

## Remove / Uninstall
```bash
./uninstall.sh
```

This removes local integration files (service, desktop, autostart, venv/build artifacts, and installed Tardix integration rules).

Installed files are primarily located under:

```text
~/.local/share/tardix-command-center
~/.local/bin/tcc
~/.local/share/applications/tardix-command-center.desktop
```

## Power Backend Behavior
Fan/Power page shows active backend source:
- Dell ACPI (WMAX)
- Linux `platform_profile` (kernel/distro policy path)

Backend can be switched from the page using the backend button.

## Documentation
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Legal notice: [LEGAL_NOTICE.md](LEGAL_NOTICE.md)
- Safety notes: [SAFETY.md](SAFETY.md)
- License: [LICENSE.md](LICENSE.md)

## Credits
- Original project and base implementation: @cemkaya-mpi
- Upstream references: trackmastersteve/alienfx issue discussions
- ACPI guidance acknowledgements: @AlexIII, @T-Troll

## Disclaimer
This tool can change power/thermal/LED behavior. Use at your own risk.
Read [LEGAL_NOTICE.md](LEGAL_NOTICE.md) and [SAFETY.md](SAFETY.md) before production use.
