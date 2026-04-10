#!/usr/bin/env python3
"""Multi-camera display system entry point."""

import os
import sys
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
    logging.basicConfig(level=level, format=fmt, datefmt='%H:%M:%S')


logger = logging.getLogger("main")


class MultiCamApp:
    def __init__(self, config_path, display=":0"):
        self.config_path = config_path
        self.display = display
        self.loop = None
        self.scene_manager = None
        self.keyboard = None

    def run(self):
        Gst.init(None)

        self.scene_manager = SceneManager(self.config_path, self.display)
        self.loop = GLib.MainLoop()

        self.keyboard = KeyboardListener(
            on_next=self._on_next,
            on_prev=self._on_prev,
            on_reload=self._on_reload,
            on_quit=self._on_quit
        )

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.keyboard.start()
        GLib.timeout_add(500, self._start_first_scene)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _start_first_scene(self):
        self.scene_manager.start_current()
        status = self.scene_manager.get_status()
        logger.info(
            f"Scene started: [{status['scene_index']}/{status['total_scenes']-1}] "
            f"{status['scene_name']}"
        )
        return False

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
        self._log_status()
        return False

    def _do_prev(self):
        self.scene_manager.prev_scene()
        self._log_status()
        return False

    def _do_reload(self):
        self.scene_manager.stop()
        self.scene_manager.reload_config()
        self.scene_manager.start_current()
        self._log_status()
        return False

    def _do_quit(self):
        logger.info("Shutting down...")
        self.loop.quit()
        return False

    def _log_status(self):
        status = self.scene_manager.get_status()
        logger.info(
            f"Active scene: [{status['scene_index']}/{status['total_scenes']-1}] "
            f"{status['scene_name']}"
        )

    def _signal_handler(self, signum, frame):
        GLib.idle_add(self._do_quit)

    def _cleanup(self):
        if self.keyboard:
            self.keyboard.stop()
            self.keyboard.restore_terminal()
        if self.scene_manager:
            self.scene_manager.stop()
        logger.info("Application stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-camera display system — K-Challenge"
    )
    parser.add_argument(
        '--config', '-c',
        default='config/scenes_screen1.json',
        help='Path to the scenes JSON config file'
    )
    parser.add_argument(
        '--display', '-d',
        default=':0',
        help='X display to use (default: :0)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose/debug logging'
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    os.environ["DISPLAY"] = args.display
    os.environ.setdefault("XAUTHORITY", "/tmp/.Xauthority-jetson")

    if not os.path.exists(args.config):
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    app = MultiCamApp(args.config, args.display)
    app.run()


if __name__ == '__main__':
    main()
