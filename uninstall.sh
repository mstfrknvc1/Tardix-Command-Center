#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ID="tardix-command-center"
INSTALL_DIR="/home/mstfrknvc/.local/share/tardix-command-center"
LAUNCHER="/home/mstfrknvc/.local/bin/tcc"
DESKTOP_FILE="/home/mstfrknvc/.local/share/applications/tardix-command-center.desktop"
AUTOSTART_FILE="/home/mstfrknvc/.config/autostart/tardix-command-center.desktop"
INSTALLED_UNINSTALL="/home/mstfrknvc/.local/share/tardix-command-center/uninstall.sh"

echo "Removing Tardix Command Center..."

if [ -x "$INSTALLED_UNINSTALL" ] && [ "$INSTALLED_UNINSTALL" != "$0" ]; then
    "$INSTALLED_UNINSTALL" || true
fi

if command -v systemctl >/dev/null 2>&1; then
    systemctl --user disable --now "tardix-command-center.service" >/dev/null 2>&1 || true
    rm -f "/home/mstfrknvc/.config/systemd/user/tardix-command-center.service"
    systemctl --user daemon-reload >/dev/null 2>&1 || true
fi

rm -f "/home/mstfrknvc/.config/autostart/tardix-command-center.desktop"
rm -f "/home/mstfrknvc/.local/share/applications/tardix-command-center.desktop"
rm -f "/home/mstfrknvc/.local/bin/tcc"
rm -rf "/home/mstfrknvc/.local/share/tardix-command-center"

rm -f "$SCRIPT_DIR/tardix"
rm -f "$SCRIPT_DIR/.tardix-install-state"
rm -rf "$SCRIPT_DIR/dist" "$SCRIPT_DIR/build" "$SCRIPT_DIR/tardix-command-center.spec"
rm -rf "$SCRIPT_DIR/tcc"

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
