# ✅ Checklist pré-lancement — Multi-Cam Display

Cette checklist garantit que tout fonctionne avant le lancement.

## 🔧 Sur la Jetson (une seule fois)

- [ ] **SSH configuré pour X11 forwarding**
  ```bash
  sudo bash ~/multi_cam_display/setup_ssh.sh
  ```
  
- [ ] **Mode performance GPU activé**
  ```bash
  sudo nvpmodel -m 0
  sudo jetson_clocks
  ```

- [ ] **Fichiers vérifié**
  ```bash
  ls -la ~/multi_cam_display/*.py
  ls -la ~/multi_cam_display/config/scenes_screen1.json
  ```

- [ ] **Caméras détectées**
  ```bash
  ls /dev/video* | wc -l
  # Doit afficher: 8
  ```

## 💻 Sur votre PC (avant chaque lancement)

### Avant la connexion SSH

- [ ] Jetson branché en réseau et allumée
- [ ] Écran DP-0 branché et détecté sur Jetson
- [ ] Connectivité réseau OK (ping possible vers IP Jetson)

### Connexion SSH avec X11 Forwarding

- [ ] **Déconnectez** les anciennes sessions SSH
  ```bash
  exit
  ```

- [ ] **Reconnectez-vous AVEC X11 forwarding**
  ```bash
  ssh -X k-challenge@192.168.1.XXX
  # OU
  ssh -Y k-challenge@192.168.1.XXX
  ```
  
  ⚠️ **OBLIGATOIRE** — Sinon l'écran n'affichera rien!

### Vérification de DISPLAY

- [ ] **Vérifiez que DISPLAY est défini**
  ```bash
  echo $DISPLAY
  # Doit afficher: localhost:10.0
  # ou: :10
  # N'importe quoi SAUF vide
  ```

- [ ] **Si DISPLAY est vide:**
  - Vous n'avez probablement pas utilisé `-X` ou `-Y`
  - Reconnectez avec: `ssh -X k-challenge@192.168.1.XXX`

## 🔍 Vérifications système (sur la Jetson)

- [ ] **Vérification système complète**
  ```bash
  bash ~/multi_cam_display/check_system.sh
  ```
  
  Doit retourner ≥ 15+ tests réussis, < 5 échecs

- [ ] **Caméras totalement opérationnelles**
  ```bash
  for i in {0..7}; do v4l2-ctl -d /dev/video$i --get-fmt-video 2>&1 | grep -q "Width" && echo "✓ video$i" || echo "✗ video$i"; done
  ```

- [ ] **GStreamer prêt**
  ```bash
  gst-inspect-1.0 nvvidconv nvcompositor nvdrmvideosink 2>&1 | grep -c "Factory"
  # Doit afficher: 3
  ```

## 🚀 Lancement final

- [ ] **Changez dans le répertoire correct**
  ```bash
  cd ~/multi_cam_display
  ```

- [ ] **Lancez l'application**
  ```bash
  ./start.sh
  ```

- [ ] **Vérifiez que:**
  - ✓ Aucune erreur au lancement
  - ✓ L'écran DP-0 affiche un flux vidéo
  - ✓ L'image ne gèle pas (fluide 30 FPS)
  - ✓ Les contrôles (← → r q) fonctionnent

## 🎮 Test des contrôles

Une fois l'app lancée:

- [ ] **Testez → (scène suivante)**
  - L'écran change vers la prochaine scène
  - Pas de lag perceptible

- [ ] **Testez ← (scène précédente)**
  - Revient à la scène précédente
  - Transition fluide

- [ ] **Testez r (recharger JSON)**
  - L'app recharge le fichier config/scenes_screen1.json
  - Pas de crash

- [ ] **Testez q (quitter)**
  - L'application se ferme proprement
  - Terminal retourne à l'invite

## ❌ Si quelque chose échoue

### "unable to open display" ou "Could not open DRM"

```bash
# EXIT SSH
exit

# Reconnectez AVEC -X
ssh -X k-challenge@jetson-ip

# Vérifiez
echo $DISPLAY
```

### Caméra gèle ou image saccadée

```bash
# Réduisez le nombre de caméras: testez une scène avec 1 caméra
# Ou baissez la résolution dans config/scenes_screen1.json
# Ou activez le mode perf:
sudo nvpmodel -m 0
sudo jetson_clocks
```

### "Plugin nvvidconv not found"

```bash
# Réinstallez les plugins:
sudo apt install gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0
```

### Caméras non détectées

```bash
# Vérifiez les drivers
dmesg | grep -i ISX031
# Sinon, rebootez la Jetson
```

## 📊 Performances attendues

```
┌─────────────────┬─────────────────────────────────────────────┐
│ Scène           │ Performance attendue (2560×1440)            │
├─────────────────┼─────────────────────────────────────────────┤
│ 1 caméra (FS)   │ ✓ 60 FPS facilement                         │
│ 2 caméras       │ ✓ 30+ FPS stable                            │
│ 4 caméras       │ ✓ 20-30 FPS acceptable                      │
│ 8 caméras       │ ✓ 15-20 FPS (performance GPU requise)       │
└─────────────────┴─────────────────────────────────────────────┘
```

## ✅ Vous êtes prêt!

Une fois cette checklist complète:

1. ✓ Système vérifié
2. ✓ SSH avec X11 OK
3. ✓ DISPLAY défini
4. ✓ Caméras détectées
5. ✓ App lancée avec succès
6. ✓ Contrôles testés

**L'application est opérationelle pour la production !** 🎉

---

*Garder cette checklist à proximité pour les lancements futurs.*
