# Système d'affichage multi-caméras — K-Challenge

L'écran DP-0 de la Jetson affiche uniquement les flux caméra GStreamer en plein écran.
Le contrôle se fait entièrement depuis un terminal SSH sur le PC.

---

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
nv3dsink → fenêtre plein écran sur DP-0 (fond noir)
```

---

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
