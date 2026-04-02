#!/bin/bash
# Script de configuration SSH pour X11 forwarding
# Activation de X11 forwarding sur la Jetson pour permettre les connexions SSH graphiques

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  Configuration SSH pour X11 Forwarding — Multi-Cam Display            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo "✗ Ce script doit être lancé avec sudo"
    echo ""
    echo "  Exécutez:"
    echo "    sudo bash ~/multi_cam_display/setup_ssh.sh"
    exit 1
fi

SSHD_CONFIG="/etc/ssh/sshd_config"

echo "📝 Vérification de la configuration SSH..."
echo ""

# Vérifier X11Forwarding
if grep -q "^X11Forwarding yes" "$SSHD_CONFIG"; then
    echo "  ✓ X11Forwarding yes — déjà activé"
else
    echo "  ⚠ X11Forwarding — configuration manquante ou désactivée"
    if grep -q "^#X11Forwarding" "$SSHD_CONFIG"; then
        echo "    → Décommentage..."
        sed -i 's/^#X11Forwarding.*/X11Forwarding yes/' "$SSHD_CONFIG"
    else
        echo "    → Ajout de la ligne..."
        echo "X11Forwarding yes" >> "$SSHD_CONFIG"
    fi
    echo "    ✓ Fait"
fi

# Vérifier X11DisplayOffset
if grep -q "^X11DisplayOffset 10" "$SSHD_CONFIG"; then
    echo "  ✓ X11DisplayOffset 10 — déjà activé"
else
    echo "  ⚠ X11DisplayOffset — configuration manquante"
    if grep -q "^#X11DisplayOffset" "$SSHD_CONFIG"; then
        echo "    → Décommentage..."
        sed -i 's/^#X11DisplayOffset.*/X11DisplayOffset 10/' "$SSHD_CONFIG"
    else
        echo "    → Ajout de la ligne..."
        echo "X11DisplayOffset 10" >> "$SSHD_CONFIG"
    fi
    echo "    ✓ Fait"
fi

# Vérifier X11UseLocalhost
if grep -q "^X11UseLocalhost yes" "$SSHD_CONFIG"; then
    echo "  ✓ X11UseLocalhost yes — déjà activé"
else
    echo "  ⚠ X11UseLocalhost — configuration manquante"
    if grep -q "^#X11UseLocalhost" "$SSHD_CONFIG"; then
        echo "    → Décommentage..."
        sed -i 's/^#X11UseLocalhost.*/X11UseLocalhost yes/' "$SSHD_CONFIG"
    else
        echo "    → Ajout de la ligne..."
        echo "X11UseLocalhost yes" >> "$SSHD_CONFIG"
    fi
    echo "    ✓ Fait"
fi

echo ""
echo "🔄 Redémarrage du service SSH..."
systemctl restart ssh 2>/dev/null || systemctl restart sshd 2>/dev/null

if systemctl is-active --quiet ssh 2>/dev/null || systemctl is-active --quiet sshd 2>/dev/null; then
    echo "  ✓ SSH redémarré avec succès"
else
    echo "  ⚠ Erreur lors du redémarrage de SSH"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  Configuration terminée !                                             ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📌 Prochaines étapes (depuis votre PC):"
echo ""
echo "  1. Fermez et ouvrez une nouvelle session SSH:"
echo ""
echo "     ssh -X k-challenge@JETSON_IP"
echo ""
echo "  2. Vérifiez que DISPLAY est correctement défini:"
echo ""
echo "     echo \$DISPLAY"
echo "     # Doit afficher: localhost:10.0"
echo ""
echo "  3. Lancez l'application:"
echo ""
echo "     ./start.sh"
echo ""
