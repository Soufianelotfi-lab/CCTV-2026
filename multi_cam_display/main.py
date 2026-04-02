#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
-------
Point d'entrée du système d'affichage multi-caméras.

IMPORTANT : Ce script configure automatiquement DISPLAY=:1 et XAUTHORITY
pour fonctionner depuis SSH. L'écran DP-0 de la Jetson affiche les flux
caméras en plein écran, le contrôle se fait depuis le terminal SSH.

Architecture :
  keyboard_listener  →  scene_manager  →  screen_worker  →  Écran DP-0
  (← → dans SSH)        (JSON config)     (GStreamer GPU)    (conducteur)

Utilisation depuis SSH :
  ssh k-challenge@<IP_JETSON>
  cd ~/multi_cam_display
  python3 main.py

  ou directement :
  ./start.sh

Touches :
  ←  scène précédente
  →  scène suivante
  r  recharger la config JSON
  q  quitter

Auteur  : K-Challenge
Date    : 2026
"""

import os
import sys

# ──────────────────────────────────────────────
#  Configuration X11 pour SSH
#  DOIT être fait AVANT tout import GStreamer
# ──────────────────────────────────────────────
os.environ["DISPLAY"] = ":1"
os.environ["XAUTHORITY"] = "/run/user/1000/gdm/Xauthority"

import signal
import argparse
import logging

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

from scene_manager import SceneManager
from keyboard_listener import KeyboardListener


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = '%(asctime)s [%(name)s] %(levelname)s — %(message)s'
    datefmt = '%H:%M:%S'
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt)

logger = logging.getLogger("main")


class MultiCamApp:
    """Application principale d'affichage multi-caméras."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.loop = None
        self.scene_manager = None
        self.keyboard = None

    def run(self):
        """Lance l'application."""

        # 1. Vérifier l'accès X11
        logger.info(f"DISPLAY={os.environ.get('DISPLAY')}")
        logger.info(f"XAUTHORITY={os.environ.get('XAUTHORITY')}")

        # Autoriser l'accès X11
        os.system("xhost +local: 2>/dev/null")

        # 2. Initialiser GStreamer
        Gst.init(None)
        logger.info("GStreamer initialisé")

        # 3. Créer le gestionnaire de scènes
        self.scene_manager = SceneManager(self.config_path)

        # 4. Boucle GLib
        self.loop = GLib.MainLoop()

        # 5. Keyboard listener
        self.keyboard = KeyboardListener(
            on_next=self._on_next,
            on_prev=self._on_prev,
            on_reload=self._on_reload,
            on_quit=self._on_quit
        )

        # 6. Signaux système
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 7. Démarrage
        logger.info("╔══════════════════════════════════════════════╗")
        logger.info("║   Système d'affichage multi-caméras         ║")
        logger.info("║   K-Challenge — Écran conducteur            ║")
        logger.info("║                                             ║")
        logger.info("║   ← PREV  │  → NEXT  │  r RELOAD  │  q QUIT║")
        logger.info("╚══════════════════════════════════════════════╝")

        self.keyboard.start()

        # Démarrer la première scène après un court délai
        GLib.timeout_add(500, self._start_first_scene)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _start_first_scene(self):
        """Démarre la première scène."""
        self.scene_manager.start_current()
        status = self.scene_manager.get_status()
        logger.info(
            f"Scène initiale : [{status['scene_index']}/{status['total_scenes']-1}] "
            f"{status['scene_name']}"
        )
        return False

    # ── Callbacks ──

    def _on_next(self):
        GLib.idle_add(self._do_next)

    def _on_prev(self):
        GLib.idle_add(self._do_prev)

    def _on_reload(self):
        GLib.idle_add(self._do_reload)

    def _on_quit(self):
        GLib.idle_add(self._do_quit)

    def _do_next(self):
        self.scene_manager.next_scene()
        self._print_status()
        return False

    def _do_prev(self):
        self.scene_manager.prev_scene()
        self._print_status()
        return False

    def _do_reload(self):
        logger.info("Rechargement config...")
        self.scene_manager.stop()
        self.scene_manager.reload_config()
        self.scene_manager.start_current()
        self._print_status()
        return False

    def _do_quit(self):
        logger.info("Arrêt demandé...")
        self.loop.quit()
        return False

    def _print_status(self):
        status = self.scene_manager.get_status()
        logger.info(
            f"Scène active : [{status['scene_index']}/{status['total_scenes']-1}] "
            f"{status['scene_name']}"
        )

    def _signal_handler(self, signum, frame):
        GLib.idle_add(self._do_quit)

    def _cleanup(self):
        logger.info("Nettoyage...")
        if self.keyboard:
            self.keyboard.stop()
            self.keyboard.restore_terminal()
        if self.scene_manager:
            self.scene_manager.stop()
        logger.info("Application terminée")


def main():
    parser = argparse.ArgumentParser(
        description="Système d'affichage multi-caméras — K-Challenge"
    )
    parser.add_argument(
        '--config', '-c',
        default='config/scenes_screen1.json',
        help='Chemin vers le fichier JSON de config'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbose (debug)'
    )
    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    if not os.path.exists(args.config):
        logger.error(f"Config introuvable : {args.config}")
        sys.exit(1)

    app = MultiCamApp(args.config)
    app.run()


if __name__ == '__main__':
    main()
