#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scene_manager.py
----------------
Gestionnaire de scènes pour un écran donné.
Charge la config JSON, maintient l'index courant,
orchestre les switchs (arrêt ancien pipeline → démarrage nouveau).

Auteur  : K-Challenge
Date    : 2026
"""

import json
import os
import logging
import time
from screen_worker import ScreenWorker

logger = logging.getLogger("scene_manager")


class SceneManager:
    """Orchestre le switch de scènes pour un écran."""

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = None
        self.scenes = []
        self.current_index = 0
        self.worker = None
        self._switching = False

        self._load_config()

    def _load_config(self):
        """Charge le fichier JSON de configuration."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config introuvable : {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.scenes = self.config.get("scenes", [])
        if not self.scenes:
            raise ValueError("Aucune scène définie dans la config")

        display_config = self.config.get("display", {"width": 2560, "height": 1440})
        camera_defaults = self.config.get("camera_defaults", {
            "format": "UYVY",
            "capture_width": 1920,
            "capture_height": 1080,
            "framerate": 30
        })

        self.worker = ScreenWorker(display_config, camera_defaults)

        logger.info(
            f"Config chargée : {len(self.scenes)} scènes, "
            f"écran {display_config['width']}x{display_config['height']}"
        )
        for i, s in enumerate(self.scenes):
            logger.info(f"  Scène {i} : {s['name']}")

    def reload_config(self):
        """Recharge la config JSON à chaud."""
        logger.info("Rechargement de la config...")
        old_index = self.current_index
        self._load_config()
        if old_index >= len(self.scenes):
            self.current_index = 0
        else:
            self.current_index = old_index

    def _switch_to(self, index):
        """Switch vers la scène à l'index donné."""
        if self._switching:
            logger.warning("Switch déjà en cours, ignoré")
            return

        self._switching = True
        try:
            scene = self.scenes[index]
            logger.info(f"═══ Switch vers scène {index} : {scene['name']} ═══")

            if self.worker.is_running():
                self.worker.stop()
                time.sleep(0.3)

            success = self.worker.start(scene)
            if success:
                self.current_index = index
                logger.info(f"Scène active : [{index}/{len(self.scenes)-1}] {scene['name']}")
            else:
                logger.error(f"Échec du démarrage de la scène {index}")
        finally:
            self._switching = False

    def start_current(self):
        """Démarre la scène courante."""
        self._switch_to(self.current_index)

    def next_scene(self):
        """Scène suivante (boucle cyclique)."""
        next_idx = (self.current_index + 1) % len(self.scenes)
        self._switch_to(next_idx)

    def prev_scene(self):
        """Scène précédente (boucle cyclique)."""
        prev_idx = (self.current_index - 1) % len(self.scenes)
        self._switch_to(prev_idx)

    def go_to_scene(self, index):
        """Saute directement à une scène."""
        if 0 <= index < len(self.scenes):
            self._switch_to(index)
        else:
            logger.warning(f"Index invalide : {index} (max: {len(self.scenes)-1})")

    def stop(self):
        """Arrête le pipeline en cours."""
        if self.worker:
            self.worker.stop()
        logger.info("Scene manager arrêté")

    def get_current_scene_name(self):
        if self.scenes:
            return self.scenes[self.current_index]["name"]
        return "Aucune scène"

    def get_scene_count(self):
        return len(self.scenes)

    def get_status(self):
        return {
            "scene_index": self.current_index,
            "scene_name": self.get_current_scene_name(),
            "total_scenes": len(self.scenes),
            "pipeline_running": self.worker.is_running() if self.worker else False
        }
