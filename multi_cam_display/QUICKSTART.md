# 🚀 Démarrage rapide — Multi-Cam Display

## Prérequis

- Jetson AGX Orin avec L4T 35.4.1 / JetPack 5.1.2
- 8 caméras STURDeCAM31 (Sony ISX031) connectées via GMSL2
- Écran DP-0 (2560×1440) branché à la Jetson
- PC/Mac pour connexion SSH (**important**)

## 1️⃣ Sur la Jetson — Configuration SSH (UNE FOIS)

```bash
# Configurer SSH pour X11 forwarding
sudo bash ~/multi_cam_display/setup_ssh.sh

# Vérifier l'état du système
bash ~/multi_cam_display/check_system.sh
```

## 2️⃣ Sur votre PC — Connexion SSH

```bash
# ⚠️ IMPORTANT: Utilisez -X ou -Y pour le X11 forwarding!
ssh -X k-challenge@192.168.1.XXX
# ou
ssh -Y k-challenge@192.168.1.XXX
```

Remplacez `192.168.1.XXX` par l'IP de votre Jetson.

## 3️⃣ Vérification DISPLAY

```bash
echo $DISPLAY
# ✓ Doit afficher: localhost:10.0 (ou similaire)
```

Si DISPLAY est vide → Reconnectez-vous avec `ssh -X`.

## 4️⃣ Lancer l'application

```bash
cd ~/multi_cam_display
./start.sh
```

L'écran DP-0 **affichera le flux vidéo** de la première scène.

## 🎮 Contrôles

| Touche | Action |
|--------|--------|
| `→` | Scène suivante |
| `←` | Scène précédente |
| `r` | Recharger le JSON |
| `q` | Quitter |

## 📹 Scènes disponibles

1. Plein écran — Caméra 0
2. Grille 2 caméras
3. Grille 4 caméras
4. Cam 0 — Rotation 90°
5. Cam 0 — Zoom x2
6. Grille **8 caméras** (toutes!)
7. Plein écran — Caméra 1
8. Plein écran — Caméra 2

## ❌ Ça ne marche pas?

### "unable to open display" ou "Could not open DRM failed"

```bash
# Quittez
exit

# Reconnectez-vous AVEC -X:
ssh -X k-challenge@jetson-ip

# Vérifiez:
echo $DISPLAY
```

### "Aucune caméra détectée"

```bash
# Vérifiez les caméras:
ls /dev/video*
dmesg | grep ISX031
```

### Plugins GStreamer manquants

```bash
sudo apt install gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0
```

## 📚 Docs complètes

- [README.md](README.md) — Architecture détaillée
- [INSTALLATION_SSH.md](INSTALLATION_SSH.md) — Configuration SSH avancée
- [config/scenes_screen1.json](config/scenes_screen1.json) — Scènes disponibles

## ✅ Checklist de confirmation

- [ ] SSH connecté avec `ssh -X`
- [ ] `echo $DISPLAY` retourne `localhost:10.0`
- [ ] `bash check_system.sh` sans erreurs critiques
- [ ] 8 caméras détectées (`ls /dev/video0-7`)
- [ ] `./start.sh` lance sans erreurs
- [ ] L'écran DP-0 affiche le flux vidéo

C'est tout! 🎉
