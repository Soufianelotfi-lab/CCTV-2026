#!/bin/bash
# ═══════════════════════════════════════════════
#  start.sh — Lancement rapide depuis SSH
# ═══════════════════════════════════════════════
#
#  Usage :
#    ssh k-challenge@<IP_JETSON>
#    cd ~/multi_cam_display
#    ./start.sh
#
#    ou directement :
#    ssh k-challenge@<IP_JETSON> "cd ~/multi_cam_display && ./start.sh"
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Configuration X11 pour SSH ──
export DISPLAY=:1
export XAUTHORITY=/run/user/1000/gdm/Xauthority

# ── Autoriser l'affichage ──
xhost +local: 2>/dev/null

# ── Performance GPU ──
echo "Activation du mode performance GPU..."
sudo nvpmodel -m 0 2>/dev/null
sudo jetson_clocks 2>/dev/null

# ── Vérification rapide ──
echo ""
echo "═══ Vérification du système ═══"

# Écran
SCREEN=$(xrandr 2>/dev/null | grep " connected" | head -1)
if [ -z "$SCREEN" ]; then
    echo "ERREUR : Impossible d'accéder à l'affichage X11"
    echo "Vérifiez que la session graphique est active sur la Jetson"
    exit 1
fi
echo "Écran    : $SCREEN"

# Caméras
CAM_COUNT=$(ls /dev/video* 2>/dev/null | wc -l)
echo "Caméras  : $CAM_COUNT détectée(s)"

if [ "$CAM_COUNT" -eq 0 ]; then
    echo "ERREUR : Aucune caméra détectée !"
    echo "Vérifiez les connexions GMSL2 et les drivers"
    exit 1
fi

# GStreamer
GST_OK=$(gst-inspect-1.0 nv3dsink 2>/dev/null | head -1)
if [ -z "$GST_OK" ]; then
    echo "ERREUR : Plugin nv3dsink non disponible"
    exit 1
fi
echo "GStreamer : OK (nv3dsink disponible)"

echo ""
echo "═══ Lancement de l'application ═══"
echo "  ← PREV  |  → NEXT  |  r RELOAD  |  q QUIT"
echo ""

# ── Lancement ──
python3 main.py "$@"
