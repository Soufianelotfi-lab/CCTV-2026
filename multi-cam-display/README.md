# Système d'affichage multi-caméras — K-Challenge

L'écran DP-0 de la Jetson affiche uniquement les flux caméra GStreamer en plein écran.
<<<<<<< HEAD
Le PC se connecte en SSH et pilote la navigation entre les scènes via le clavier.
=======
Le contrôle se fait entièrement depuis un terminal SSH sur le PC.

---
>>>>>>> V_H

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
<<<<<<< HEAD
xdotool → fenêtre sans bord + plein écran
        │
        ▼
DP-0 affiche uniquement les scènes caméra (fond noir)
=======
nv3dsink → fenêtre plein écran sur DP-0 (fond noir)
>>>>>>> V_H
```

---

<<<<<<< HEAD
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
=======
## Commandes dans l'ordre

### Étape 1 — Installation initiale (une seule fois)

```bash
# Se connecter à la Jetson
ssh user@jetson

# Aller dans le dossier du projet
cd ~/multi_cam_display

# Lancer le script de configuration (désactive le bureau, installe les paquets, copie xorg-jetson.conf)
sudo bash jetson_setup.sh

# Redémarrer la Jetson
sudo reboot
```

Après le redémarrage : l'écran DP-0 est noir. C'est normal.

---

### Étape 2 — Lancement quotidien depuis le PC

```bash
# Se connecter à la Jetson
ssh user@jetson

# Aller dans le dossier du projet
cd ~/multi_cam_display

# Démarrer le serveur X (SANS sudo)
bash start_display.sh

# Lancer l'affichage caméra
python3 main.py
```

> **Important :** toujours lancer `bash start_display.sh` sans `sudo`.
> Le script gère lui-même le sudo pour Xorg en interne.
> Avec `sudo bash`, le fichier xauth devient inaccessible → `No protocol specified`.

---

### Étape 3 — Arrêter l'affichage

```bash
# Depuis le terminal SSH où python3 main.py tourne :
q                          # touche Q pour quitter proprement

# Ou forcer l'arrêt depuis un autre terminal :
kill $(pgrep -f main.py)

# Arrêter Xorg :
sudo pkill Xorg
```

---

### Étape 4 — Réactiver le bureau graphique (si besoin)

```bash
# Remettre le bureau GNOME au démarrage
sudo systemctl set-default graphical.target

# Redémarrer
sudo reboot
```

Après le redémarrage : l'écran affiche à nouveau le bureau GNOME.

---

### Revenir en mode caméra après avoir réactivé le bureau

```bash
# Désactiver à nouveau le bureau
sudo systemctl set-default multi-user.target
sudo systemctl stop gdm3

# Relancer sans reboot (ou rebooter pour être propre)
# start_display.sh recopie automatiquement xorg-jetson.conf si besoin
sudo reboot
```

---

## Ce que fait chaque fichier

### `jetson_setup.sh`
Script de configuration initiale à exécuter **une seule fois** avec sudo.
- Désactive le bureau graphique (`multi-user.target`)
- Arrête et désactive `gdm3` / `lightdm`
- Installe les paquets requis (`xorg`, `xdotool`, `python3-gi`, `gir1.2-gstreamer-1.0`, etc.)
- Installe `/etc/X11/xorg-jetson.conf`
- Configure `Xwrapper.config` pour autoriser Xorg depuis SSH

### `xorg-jetson.conf`
Configuration Xorg minimale pour la Jetson.
- Pilote `nvidia`, sortie `DP-0`, résolution `2560x1440 @ 60 Hz`
- Aucun clavier, aucune souris (entrée uniquement via SSH)
- DPMS et screen saver désactivés (empêche l'écran de s'éteindre après 10 min)
- Référencé par `start_display.sh` au démarrage de Xorg

### `start_display.sh`
Démarre le serveur X minimal sur DP-0 depuis la session SSH.
- Vérifie si Xorg tourne déjà (idempotent, sûr à relancer)
- Génère un cookie xauth dans `/tmp/.Xauthority-jetson` (lisible par tous les utilisateurs)
- Lance `sudo Xorg :0` avec la config minimale
- Vérifie via `xrandr` que DP-0 est détecté
- Désactive le screen saver avec `xset s off -dpms`
- Affiche `Display :0 ready on DP-0` si tout est OK

### `main.py`
Point d'entrée de l'application.
- Parse les arguments CLI (`--config`, `--display`, `--verbose`)
- Définit `DISPLAY` et `XAUTHORITY` dans l'environnement avant GStreamer
- Initialise GStreamer, le `SceneManager`, le `KeyboardListener`
- Lance la boucle principale GLib
- Gère les signaux `SIGINT` / `SIGTERM` pour un arrêt propre

### `scene_manager.py`
Charge la configuration JSON et gère la navigation entre les scènes.
- Lit `config/scenes_screen1.json` et instancie le `ScreenWorker`
- `next_scene()` / `prev_scene()` : changent la scène active
- `_switch_to()` : arrête le pipeline courant puis démarre le nouveau
- Verrou `_switching` : ignore les changements concurrent

### `screen_worker.py`
Construit et pilote les pipelines GStreamer.
- `_build_camera_source()` : construit la source pour une caméra (`v4l2src → nvvidconv → queue`)
- `_build_fullscreen_pipeline()` : une caméra → `nv3dsink` plein écran
- `_build_grid_pipeline()` : plusieurs caméras → `nvcompositor` → `nv3dsink`
- `start()` : parse le pipeline, connecte les callbacks bus, démarre en `PLAYING`
- `stop()` : initie l'arrêt en background (thread daemon) pour ne pas bloquer la GLib main loop pendant le teardown EGL de nv3dsink

### `keyboard_listener.py`
Écoute le clavier en mode raw depuis le terminal SSH.
- Tourne dans un thread dédié (daemon)
- Lit les séquences ANSI (`\x1b[C` = →, `\x1b[D` = ←)
- Appelle les callbacks `on_next`, `on_prev`, `on_reload`, `on_quit`
- Restaure le terminal à la fermeture

### `config/scenes_screen1.json`
Définit les scènes disponibles et les paramètres caméra.
- `display` : résolution de l'écran
- `camera_defaults` : format, résolution, framerate par défaut
- `scenes` : liste des scènes (type `fullscreen` ou `grid`, caméras, flip, crop)

---

## Arguments CLI

| Argument | Court | Défaut | Description |
|---|---|---|---|
| `--config` | `-c` | `config/scenes_screen1.json` | Fichier JSON des scènes |
| `--display` | `-d` | `:0` | Serveur X cible |
| `--verbose` | `-v` | désactivé | Logs DEBUG |

---

## Commandes clavier (terminal SSH)

| Touche | Action |
|---|---|
| `→` | Scène suivante |
| `←` | Scène précédente |
| `r` | Recharger la config JSON |
| `q` | Quitter |

---

## Dépannage

| Erreur | Solution |
|---|---|
| `No protocol specified` | Lancer `bash start_display.sh` sans `sudo`. Vérifier `ls -la /tmp/.Xauthority-jetson` |
| `DP-0 not detected` | Vérifier le câble DisplayPort, relancer `bash start_display.sh` |
| `Failed to start pipeline` | Tester `ls /dev/video*`. Vérifier les droits : `sudo usermod -aG video $USER` |
| `io-mode=4` erreur | Caméra sans DMA-Buf : remplacer `io-mode=4` par `io-mode=2` dans `screen_worker.py` |
| `Config file not found` | Vérifier le répertoire courant : `cd ~/multi_cam_display` |
| Écran noir après 10 min | Relancer `bash start_display.sh` (recopie `xorg-jetson.conf` automatiquement si besoin) |
| Vérifier Xorg | `ps aux \| grep Xorg` ou `ls /tmp/.X0-lock` |
| FPS faible | `sudo nvpmodel -m 0 && sudo jetson_clocks` |
>>>>>>> V_H
