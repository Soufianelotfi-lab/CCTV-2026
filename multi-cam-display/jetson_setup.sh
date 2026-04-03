#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Run this script with sudo." >&2
    exit 1
fi

echo "=== Désactivation de l'interface graphique ==="
systemctl set-default multi-user.target

for dm in gdm3 lightdm; do
    if systemctl list-unit-files "${dm}.service" &>/dev/null; then
        systemctl stop "${dm}" 2>/dev/null || true
        systemctl disable "${dm}" 2>/dev/null || true
        echo "  ${dm} désactivé"
    fi
done

echo "=== Installation des paquets requis ==="
apt-get update -qq
apt-get install -y \
    xorg \
    xserver-xorg-core \
    xdotool \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0

echo "=== Configuration de Xwrapper ==="
echo "allowed_users=anybody" > /etc/X11/Xwrapper.config

echo "=== Installation de xorg-jetson.conf ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/xorg-jetson.conf" ]; then
    cp "${SCRIPT_DIR}/xorg-jetson.conf" /etc/X11/xorg-jetson.conf
    echo "  /etc/X11/xorg-jetson.conf installé"
else
    echo "  AVERTISSEMENT: xorg-jetson.conf introuvable dans ${SCRIPT_DIR}" >&2
fi

echo ""
echo "Configuration terminée. Redémarrez la Jetson :"
echo "  sudo reboot"
