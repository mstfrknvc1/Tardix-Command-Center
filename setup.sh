#!/bin/bash
# Tardix Command Center setup script
# - Installs dependencies (Debian/Arch)
# - Creates virtualenv and installs Python requirements
# - Installs udev + polkit + acpi_call setup
# - Builds app (PyInstaller + compileall fallback)
# - Creates XDG launcher + desktop entry
# - Installs a disabled user service for optional background launch
# - Generates uninstall script

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()  { echo -e "\n${BLUE}==>${NC} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

load_app_meta() {
    local meta_output
    meta_output="$(python3 - "$SCRIPT_DIR" <<'PY'
import pathlib
import sys

app_meta_path = pathlib.Path(sys.argv[1]) / "core" / "app_meta.py"
namespace = {}
exec(app_meta_path.read_text(encoding="utf-8"), namespace)

for key in (
    "APP_ID",
    "APP_NAME",
    "APP_CLI",
    "APP_GENERIC_NAME",
    "APP_DESCRIPTION",
    "APP_DEVELOPER",
    "APP_VERSION",
):
    print(namespace[key])
PY
)" || error "Failed to load metadata from core/app_meta.py"

    mapfile -t meta_lines <<< "$meta_output"
    [ "${#meta_lines[@]}" -eq 7 ] || error "Unexpected metadata payload from core/app_meta.py"

    APP_ID="${meta_lines[0]}"
    APP_NAME="${meta_lines[1]}"
    APP_CLI="${meta_lines[2]}"
    APP_GENERIC_NAME="${meta_lines[3]}"
    APP_DESCRIPTION="${meta_lines[4]}"
    APP_DEVELOPER="${meta_lines[5]}"
    APP_VERSION="${meta_lines[6]}"
}

load_app_meta

INSTALL_DIR="$HOME/.local/share/$APP_ID"
APP_DIR="$INSTALL_DIR/app"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"
LAUNCHER="$BIN_DIR/$APP_CLI"
ICON_PATH="$APP_DIR/Design/png/logo.png"
UNINSTALL_PATH="$INSTALL_DIR/uninstall.sh"
DESKTOP_FILE="$HOME/.local/share/applications/$APP_ID.desktop"
AUTOSTART_FILE="$HOME/.config/autostart/$APP_ID.desktop"
DISTRO="unknown"

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

detect_distro() {
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        case "${ID_LIKE:-} ${ID:-}" in
            *debian*|*ubuntu*) DISTRO="debian" ;;
            *arch*) DISTRO="arch" ;;
        esac
    fi
    if [ "$DISTRO" = "unknown" ]; then
        has_cmd apt-get && DISTRO="debian"
        has_cmd pacman && DISTRO="arch"
    fi
}

install_system_deps() {
    step "Installing system dependencies ($DISTRO)"
    case "$DISTRO" in
        debian)
            sudo apt-get update -qq
            sudo apt-get install -y \
                python3 python3-pip python3-venv \
                polkit libxcb-cursor0 libxcb-xinerama0 \
                acpi-call-dkms "linux-headers-$(uname -r)" || \
            sudo apt-get install -y \
                python3 python3-pip python3-venv \
                polkit libxcb-cursor0 libxcb-xinerama0
            ;;
        arch)
            sudo pacman -Sy --noconfirm --needed \
                python python-pip polkit acpi_call || true
            ;;
        *)
            warn "Unknown distro; skipping package manager install."
            warn "Ensure python3, pip, venv, polkit, udev and acpi_call are installed."
            ;;
    esac
}

setup_venv() {
    step "Setting up Python virtual environment"
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi

    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"
    "$VENV_DIR/bin/pip" install pyusb pyinstaller

    # Fast sanity compile for project sources only.
    "$VENV_DIR/bin/python3" -m compileall -q \
        "$APP_DIR/main.py" \
        "$APP_DIR/core" \
        "$APP_DIR/hardware" \
        "$APP_DIR/pages" \
        "$APP_DIR/widgets" \
        "$APP_DIR/tests"
    info "Python environment and packages are ready."
}

sync_app_files() {
    step "Syncing application files"
    rm -rf "$APP_DIR"
    mkdir -p "$APP_DIR"

    cp -a "$SCRIPT_DIR/main.py" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/main.ui" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/requirements.txt" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/core" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/hardware" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/pages" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/widgets" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/assets" "$APP_DIR/"
    cp -a "$SCRIPT_DIR/Design" "$APP_DIR/"
    info "Application synced to $APP_DIR"
}

install_udev() {
    step "Installing udev rules"
    sudo cp "$SCRIPT_DIR/00-aw-elc.rules" /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
}

setup_acpi() {
    step "Configuring acpi_call"
    if sudo modprobe acpi_call 2>/dev/null; then
        info "acpi_call loaded"
    else
        warn "acpi_call not loaded; power/fan controls may not work on unsupported kernels."
    fi

    if [ -d /etc/modules-load.d ]; then
        echo "acpi_call" | sudo tee /etc/modules-load.d/tardix.conf >/dev/null
    fi
}

install_polkit() {
    step "Installing polkit rule"
    local grp="wheel"
    [ "$DISTRO" = "debian" ] && grp="sudo"
    local bash_path
    bash_path="$(command -v bash || echo /bin/bash)"

    sudo mkdir -p /etc/polkit-1/rules.d
    cat <<EOF | sudo tee /etc/polkit-1/rules.d/50-tardix.rules >/dev/null
polkit.addRule(function(action, subject) {
    if (action.id === "org.freedesktop.policykit.exec" &&
        (action.lookup("program") === "${bash_path}" ||
         action.lookup("program") === "/bin/bash" ||
         action.lookup("program") === "/usr/bin/bash") &&
        subject.isInGroup("${grp}")) {
        return polkit.Result.YES;
    }
});
EOF
}

build_program() {
    step "Building executable"
    local py="$VENV_DIR/bin/python3"
    local pyinstaller="$VENV_DIR/bin/pyinstaller"

    if [ -x "$pyinstaller" ]; then
        (
            cd "$APP_DIR"
            rm -rf build dist "$APP_ID.spec" 2>/dev/null || true
            "$pyinstaller" \
                --noconfirm \
                --clean \
                --name "$APP_ID" \
                --add-data "main.ui:." \
                --add-data "assets:assets" \
                --add-data "Design:Design" \
                main.py || true
        )
    fi

    if [ -x "$APP_DIR/dist/$APP_ID/$APP_ID" ]; then
        info "Build output: $APP_DIR/dist/$APP_ID/$APP_ID"
    else
        warn "PyInstaller build not produced; launcher will use venv python."
    fi
}

create_launcher() {
    step "Creating launcher script"
    mkdir -p "$BIN_DIR"
    cat > "$LAUNCHER" <<EOF
#!/bin/bash
set -e
exec "$VENV_DIR/bin/python3" "$APP_DIR/main.py" "\$@"
EOF
    chmod +x "$LAUNCHER"
}

create_desktop_files() {
    step "Creating desktop entries"
    mkdir -p "$HOME/.local/share/applications"

    rm -f "$AUTOSTART_FILE"

    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
GenericName=$APP_GENERIC_NAME
Exec=$LAUNCHER
TryExec=$LAUNCHER
Terminal=false
Icon=$ICON_PATH
Categories=Utility;System;
Comment=$APP_DESCRIPTION
X-Developer=$APP_DEVELOPER
X-AppVersion=$APP_VERSION
EOF
}

create_user_service() {
    step "Installing user service"
    mkdir -p "$HOME/.config/systemd/user"

    cat > "$HOME/.config/systemd/user/$APP_ID.service" <<EOF
[Unit]
Description=$APP_NAME
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=$LAUNCHER
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

    if has_cmd systemctl; then
        systemctl --user disable --now "$APP_ID.service" >/dev/null 2>&1 || true
        systemctl --user daemon-reload || true
    fi
}

create_uninstall_script() {
    step "Generating uninstall script"
    mkdir -p "$INSTALL_DIR"
    cat > "$UNINSTALL_PATH" <<EOF
#!/bin/bash
set -euo pipefail

APP_ID="$APP_ID"
INSTALL_DIR="$INSTALL_DIR"
LAUNCHER="$LAUNCHER"
DESKTOP_FILE="$DESKTOP_FILE"
AUTOSTART_FILE="$AUTOSTART_FILE"

echo "Removing $APP_NAME..."

if command -v systemctl >/dev/null 2>&1; then
    systemctl --user disable --now "$APP_ID.service" >/dev/null 2>&1 || true
    rm -f "$HOME/.config/systemd/user/$APP_ID.service"
  systemctl --user daemon-reload >/dev/null 2>&1 || true
fi

rm -f "$AUTOSTART_FILE"
rm -f "$DESKTOP_FILE"
rm -f "$LAUNCHER"
rm -f "$INSTALL_DIR/.tardix-install-state"
rm -rf "$INSTALL_DIR"

if [ -f /etc/udev/rules.d/00-aw-elc.rules ]; then
  sudo rm -f /etc/udev/rules.d/00-aw-elc.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
fi

if [ -f /etc/polkit-1/rules.d/50-tardix.rules ]; then
  sudo rm -f /etc/polkit-1/rules.d/50-tardix.rules
fi

if [ -f /etc/modules-load.d/tardix.conf ]; then
  sudo rm -f /etc/modules-load.d/tardix.conf
fi

echo "Uninstall completed."
EOF
    chmod +x "$UNINSTALL_PATH"

        cat > "$SCRIPT_DIR/uninstall.sh" <<EOF
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
APP_ID="$APP_ID"
INSTALL_DIR="$INSTALL_DIR"
LAUNCHER="$LAUNCHER"
DESKTOP_FILE="$DESKTOP_FILE"
AUTOSTART_FILE="$AUTOSTART_FILE"
INSTALLED_UNINSTALL="$UNINSTALL_PATH"

echo "Removing $APP_NAME..."

if [ -x "\$INSTALLED_UNINSTALL" ] && [ "\$INSTALLED_UNINSTALL" != "\$0" ]; then
    "\$INSTALLED_UNINSTALL" || true
fi

if command -v systemctl >/dev/null 2>&1; then
    systemctl --user disable --now "$APP_ID.service" >/dev/null 2>&1 || true
    rm -f "$HOME/.config/systemd/user/$APP_ID.service"
    systemctl --user daemon-reload >/dev/null 2>&1 || true
fi

rm -f "$AUTOSTART_FILE"
rm -f "$DESKTOP_FILE"
rm -f "$LAUNCHER"
rm -rf "$INSTALL_DIR"

rm -f "\$SCRIPT_DIR/tardix"
rm -f "\$SCRIPT_DIR/.tardix-install-state"
rm -rf "\$SCRIPT_DIR/dist" "\$SCRIPT_DIR/build" "\$SCRIPT_DIR/tardix-command-center.spec"
rm -rf "\$SCRIPT_DIR/tcc"

if [ -f /etc/udev/rules.d/00-aw-elc.rules ]; then
    sudo rm -f /etc/udev/rules.d/00-aw-elc.rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

if [ -f /etc/polkit-1/rules.d/50-tardix.rules ]; then
    sudo rm -f /etc/polkit-1/rules.d/50-tardix.rules
fi

if [ -f /etc/modules-load.d/tardix.conf ]; then
    sudo rm -f /etc/modules-load.d/tardix.conf
fi

echo "Uninstall completed."
EOF
        chmod +x "$SCRIPT_DIR/uninstall.sh"
}

write_install_state() {
    cat > "$INSTALL_DIR/.tardix-install-state" <<EOF
installed_at=$(date -Iseconds)
distro=$DISTRO
launcher=$LAUNCHER
install_dir=$INSTALL_DIR
app_dir=$APP_DIR
venv_dir=$VENV_DIR
EOF
}

warn_path_if_needed() {
    case ":$PATH:" in
        *":$BIN_DIR:"*) ;;
        *) warn "$BIN_DIR PATH içinde görünmüyor. Komut bulunmazsa shell profilinize ekleyin: export PATH=\"$BIN_DIR:\$PATH\"" ;;
    esac
}

main() {
    echo "============================================="
    echo "  Tardix Command Center Setup"
    echo "============================================="

    detect_distro
    info "Detected distro: $DISTRO"

    install_system_deps
    sync_app_files
    setup_venv
    install_udev
    setup_acpi
    install_polkit
    build_program
    create_launcher
    create_desktop_files
    create_user_service
    create_uninstall_script
    write_install_state
    warn_path_if_needed

    echo ""
    info "Setup complete"
    info "Run app: $LAUNCHER"
    info "Command: $APP_CLI"
    info "Install dir: $INSTALL_DIR"
    info "Desktop entry: $DESKTOP_FILE"
    info "Autostart: disabled by default; enable from Settings in the app"
    info "Uninstall: $UNINSTALL_PATH"
}

main "$@"
