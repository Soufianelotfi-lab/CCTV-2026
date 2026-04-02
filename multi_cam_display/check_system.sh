#!/bin/bash
# Vérification complète du système pour multi_cam_display

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  Vérification système — Multi-Cam Display K-Challenge                 ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
WARN=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    local expect="$3"
    
    echo -n "  $name ... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✓"
        ((PASS++))
    else
        if [ "$expect" = "WARN" ]; then
            echo "⚠ (optionnel)"
            ((WARN++))
        else
            echo "✗"
            ((FAIL++))
        fi
    fi
}

echo "═══════════════════════════════════════════════════════════════════════════"
echo "JETSON & SYSTÈME"
echo "═══════════════════════════════════════════════════════════════════════════"

check "Jetson detectée" "grep -q Jetson /proc/device-tree/model 2>/dev/null"
check "L4T 35.4+ detecté" "apt-show-versions nvidia-l4t-core 2>/dev/null | grep -q 35.4"
check "Sudo disponible" "sudo -n true 2>/dev/null" WARN

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "CAMÉRAS & I/O"
echo "═══════════════════════════════════════════════════════════════════════════"

CAMS=$(ls /dev/video* 2>/dev/null | wc -l)
echo "  Caméras trouvées: /dev/video0 à /dev/video$((CAMS-1)) ($CAMS caméras)"
if [ $CAMS -ge 8 ]; then
    echo "  ✓ 8 caméras détectées"
    ((PASS++))
elif [ $CAMS -gt 0 ]; then
    echo "  ⚠ Seulement $CAMS caméras (attendu: 8)"
    ((WARN++))
else
    echo "  ✗ Aucune caméra détectée"
    ((FAIL++))
fi

check "Drivers ISX031" "dmesg | grep -q 'Detected ISX031 sensor'"
check "/dev/dri disponible" "ls /dev/dri 2>/dev/null"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "GSTREAMER & PLUGINS"
echo "═══════════════════════════════════════════════════════════════════════════"

check "GStreamer 1.0" "gst-inspect-1.0 -v >/dev/null 2>&1"
check "Plugin nvvidconv" "gst-inspect-1.0 nvvidconv >/dev/null 2>&1"
check "Plugin nvcompositor" "gst-inspect-1.0 nvcompositor >/dev/null 2>&1"
check "Plugin nvdrmvideosink" "gst-inspect-1.0 nvdrmvideosink >/dev/null 2>&1"
check "v4l2src plugin" "gst-inspect-1.0 v4l2src >/dev/null 2>&1"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "PYTHON & BINDINGS"
echo "═══════════════════════════════════════════════════════════════════════════"

check "Python 3" "python3 --version"
check "python3-gi" "python3 -c 'import gi' 2>/dev/null"
check "GStreamer bindings" "python3 -c 'gi.require_version(\"Gst\", \"1.0\"); from gi.repository import Gst' 2>/dev/null"
check "GLib bindings" "python3 -c 'from gi.repository import GLib' 2>/dev/null"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "AFFICHAGE & X11"
echo "═══════════════════════════════════════════════════════════════════════════"

if [ -z "$DISPLAY" ]; then
    echo "  ✗ DISPLAY non défini (connectez-vous avec ssh -X)"
    ((FAIL++))
else
    check "DISPLAY accessible" "xset -display $DISPLAY q" WARN
    echo "  ✓ DISPLAY=$DISPLAY"
    ((PASS++))
fi

check "xdotool" "which xdotool"
check "xhost" "which xhost"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "FICHIERS APPLICATION"
echo "═══════════════════════════════════════════════════════════════════════════"

check "main.py" "test -f ~/multi_cam_display/main.py"
check "scene_manager.py" "test -f ~/multi_cam_display/scene_manager.py"
check "screen_worker.py" "test -f ~/multi_cam_display/screen_worker.py"
check "keyboard_listener.py" "test -f ~/multi_cam_display/keyboard_listener.py"
check "config/scenes_screen1.json" "test -f ~/multi_cam_display/config/scenes_screen1.json"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "RÉSUMÉ"
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  ✓ Réussi: $PASS"
echo "  ⚠ Avertissements: $WARN"
echo "  ✗ Échoué: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    if [ $WARN -eq 0 ]; then
        echo "✓ Système prêt ! Lancez: ~/multi_cam_display/start.sh"
    else
        echo "⚠ Système quasi-prêt (quelques avertissements)"
        echo "  Lancez: ~/multi_cam_display/start.sh"
    fi
else
    echo "✗ Problèmes détectés - corrigez avant de lancer l'app"
fi
echo ""
