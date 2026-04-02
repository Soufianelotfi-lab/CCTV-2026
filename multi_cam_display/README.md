# Système d'affichage multi-caméras — K-Challenge

## Configuration

- **Jetson AGX Orin** — L4T 35.4.1 / JetPack 5.1.2
- **8 caméras** STURDeCAM31 (ISX031) via GMSL2
- **Écran** DP-0 2560×1440 = écran conducteur (flux caméras uniquement)
- **Contrôle** depuis SSH (← → pour switcher les scènes)
- **X11** DISPLAY=:1 / XAUTHORITY=/run/user/1000/gdm/Xauthority

## Architecture

```
SSH (terminal)          Jetson                         Écran DP-0
┌──────────────┐   ┌──────────────────────┐   ┌─────────────────────┐
│ ← → r q     │──▶│ keyboard_listener    │   │                     │
│              │   │        ↓             │   │   Flux caméra(s)    │
│              │   │ scene_manager        │   │   plein écran       │
│              │   │        ↓             │   │   sans décorations  │
│              │   │ screen_worker        │──▶│                     │
│              │   │ (GStreamer GPU)       │   │                     │
└──────────────┘   └──────────────────────┘   └─────────────────────┘
```

## Installation

```bash
sudo apt install -y python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 xdotool
```

## Lancement

```bash
ssh k-challenge@<IP_JETSON>
cd ~/multi_cam_display
./start.sh
```

## Commandes

| Touche | Action |
|---|---|
| `→` | Scène suivante |
| `←` | Scène précédente |
| `r` | Recharger le JSON |
| `q` | Quitter |

## Scènes

Configurer dans `config/scenes_screen1.json`.

| # | Nom | Type |
|---|---|---|
| 0 | Plein écran — Cam 0 | fullscreen |
| 1 | Grille 2 caméras | grid 2×1 |
| 2 | Grille 4 caméras | grid 2×2 |
| 3 | Cam 0 rotation 90° | fullscreen + flip |
| 4 | Cam 0 zoom ×2 | fullscreen + crop |
| 5 | Grille 8 caméras | grid 4×2 |
| 6 | Plein écran — Cam 1 | fullscreen |
| 7 | Plein écran — Cam 2 | fullscreen |

## Dépannage

```bash
# Tester l'accès X11 depuis SSH
export DISPLAY=:1
export XAUTHORITY=/run/user/1000/gdm/Xauthority
xrandr

# Tester GStreamer seul
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  "video/x-raw, format=UYVY, width=1920, height=1080, framerate=30/1" ! \
  nvvidconv ! "video/x-raw(memory:NVMM), format=I420" ! nv3dsink sync=false

# Trouver le bon DISPLAY si :1 ne marche plus
ps aux | grep Xorg
```
