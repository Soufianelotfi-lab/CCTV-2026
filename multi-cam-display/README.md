# Système d'affichage multi-caméras — K-Challenge

L'écran DP-0 de la Jetson affiche uniquement les flux caméra GStreamer en plein écran.
Le PC se connecte en SSH et pilote la navigation entre les scènes via le clavier.

## Architecture

```
Démarrage Jetson → multi-user.target (console, pas de bureau)
        │
        ▼
SSH depuis PC → bash start_display.sh → Xorg :0 démarre sur DP-0
        │
        ▼
python3 main.py → pipeline GStreamer s'ouvre sur DISPLAY=:0
        │
        ▼
xdotool → fenêtre sans bord + plein écran
        │
        ▼
DP-0 affiche uniquement les scènes caméra (fond noir)
```

---

## Configuration initiale (une seule fois sur la Jetson)

### 1. Exécuter le script de configuration

```bash
sudo bash jetson_setup.sh
```

Ce script :
- Désactive définitivement le bureau graphique (`multi-user.target`)
- Arrête et désactive `gdm3` ou `lightdm` s'ils sont présents
- Installe les paquets requis : `xorg`, `xserver-xorg-core`, `xdotool`, `python3-gi`, `gir1.2-gstreamer-1.0`, `gir1.2-gst-plugins-base-1.0`
- Installe `/etc/X11/xorg-jetson.conf`

### 2. Installer manuellement la config Xorg (si nécessaire)

```bash
sudo cp xorg-jetson.conf /etc/X11/xorg-jetson.conf
```

### 3. Redémarrer la Jetson

```bash
sudo reboot
```

Après le redémarrage : l'écran DP-0 est noir. Aucun bureau, aucun login.

---

## Lancement quotidien depuis le PC

```bash
ssh user@jetson
cd ~/multi_cam_display
bash start_display.sh
python3 main.py
```

`start_display.sh` est idempotent : sûr à exécuter plusieurs fois (vérifie si Xorg tourne déjà).

---

## Arguments de la ligne de commande

| Argument | Abréviation | Défaut | Description |
|---|---|---|---|
| `--config` | `-c` | `config/scenes_screen1.json` | Chemin vers le fichier JSON des scènes |
| `--display` | `-d` | `:0` | Serveur X cible (ex. `:0`, `:1`) |
| `--verbose` | `-v` | désactivé | Active les logs DEBUG |

Exemple :

```bash
python3 main.py --config config/scenes_screen1.json --display :0 --verbose
```

---

## Commandes clavier (depuis le terminal SSH)

| Touche | Action |
|---|---|
| `→` | Scène suivante |
| `←` | Scène précédente |
| `r` | Recharger la config JSON |
| `q` | Quitter |

---

## Réactiver le bureau graphique

```bash
sudo systemctl set-default graphical.target && sudo reboot
```

---

## Dépannage

### DISPLAY non défini

`main.py` définit `DISPLAY` automatiquement via `--display` (défaut `:0`).
Si vous lancez manuellement sans passer par `main.py` :

```bash
export DISPLAY=:0
export XAUTHORITY=/tmp/.Xauthority-jetson
```

### xdotool : fenêtre introuvable

xdotool cherche la fenêtre 1,5 s après le démarrage du pipeline. Si la fenêtre n'est pas encore visible :

```bash
xdotool search --name nv3dsink
```

Si la commande ne retourne rien, le pipeline n'a pas ouvert de fenêtre. Vérifiez les logs GStreamer.

### nv3dsink : cannot open display

Le pipeline ne peut pas accéder au serveur X. Vérifiez que :
1. `start_display.sh` a été exécuté et a affiché `Display :0 ready on DP-0`
2. `DISPLAY=:0` et `XAUTHORITY=/tmp/.Xauthority-jetson` sont définis dans l'environnement

```bash
echo $DISPLAY
echo $XAUTHORITY
DISPLAY=:0 XAUTHORITY=/tmp/.Xauthority-jetson xrandr
```

### Permission refusée sur Xorg

Xorg doit être lancé avec `sudo` (géré par `start_display.sh`).
Vérifiez également `/etc/X11/Xwrapper.config` :

```bash
cat /etc/X11/Xwrapper.config
# doit contenir : allowed_users=anybody
```

### Vérifier que Xorg tourne

```bash
ps aux | grep Xorg
# ou
ls -la /tmp/.X0-lock
```

### Le pipeline ne démarre pas

Tester manuellement :

```bash
DISPLAY=:0 XAUTHORITY=/tmp/.Xauthority-jetson \
gst-launch-1.0 v4l2src device=/dev/video0 ! \
  "video/x-raw, format=UYVY, width=1920, height=1080, framerate=30/1" ! \
  nvvidconv ! "video/x-raw(memory:NVMM), format=I420" ! \
  nv3dsink sync=false
```

### FPS faible

```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```
