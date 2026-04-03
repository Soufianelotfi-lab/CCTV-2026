#!/usr/bin/env python3
"""Scene orchestration: loads JSON config and manages pipeline switching."""

import json
import os
import logging
import time
from screen_worker import ScreenWorker

logger = logging.getLogger("scene_manager")


class SceneManager:
    def __init__(self, config_path, display=":0"):
        self.config_path = config_path
        self.display = display
        self.config = None
        self.scenes = []
        self.current_index = 0
        self.worker = None
        self._switching = False

        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.scenes = self.config.get("scenes", [])
        if not self.scenes:
            raise ValueError("No scenes defined in config")

        display_config = self.config.get("display", {"width": 2560, "height": 1440})
        camera_defaults = self.config.get("camera_defaults", {
            "format": "UYVY",
            "capture_width": 1920,
            "capture_height": 1080,
            "framerate": 30
        })

        self.worker = ScreenWorker(display_config, camera_defaults, self.display)
        logger.info(
            f"Config loaded: {len(self.scenes)} scenes, "
            f"display {display_config['width']}x{display_config['height']}"
        )

    def reload_config(self):
        old_index = self.current_index
        self._load_config()
        self.current_index = old_index if old_index < len(self.scenes) else 0

    def _switch_to(self, index):
        if self._switching:
            logger.warning("Scene switch already in progress, ignoring")
            return

        self._switching = True
        try:
            scene = self.scenes[index]

            if self.worker.is_running():
                self.worker.stop()
                time.sleep(0.3)

            success = self.worker.start(scene)
            if success:
                self.current_index = index
                logger.info(f"Scene switch: [{index}/{len(self.scenes)-1}] {scene['name']}")
            else:
                logger.error(f"Failed to start scene {index}: {scene['name']}")
        finally:
            self._switching = False

    def start_current(self):
        self._switch_to(self.current_index)

    def next_scene(self):
        self._switch_to((self.current_index + 1) % len(self.scenes))

    def prev_scene(self):
        self._switch_to((self.current_index - 1) % len(self.scenes))

    def go_to_scene(self, index):
        if 0 <= index < len(self.scenes):
            self._switch_to(index)
        else:
            logger.warning(f"Invalid scene index: {index} (max: {len(self.scenes)-1})")

    def stop(self):
        if self.worker:
            self.worker.stop()

    def get_current_scene_name(self):
        if self.scenes:
            return self.scenes[self.current_index]["name"]
        return "No scene"

    def get_scene_count(self):
        return len(self.scenes)

    def get_status(self):
        return {
            "scene_index": self.current_index,
            "scene_name": self.get_current_scene_name(),
            "total_scenes": len(self.scenes),
            "pipeline_running": self.worker.is_running() if self.worker else False
        }
