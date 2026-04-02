#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
screen_worker.py
----------------
Construit et gère les pipelines GStreamer pour afficher les scènes
en plein écran sur l'écran DP-0 de la Jetson.

Lancé depuis SSH avec DISPLAY=:1, l'écran affiche uniquement
les flux caméras sans aucune décoration (pas de barre de titre,
pas de bordures, pas de bureau visible).

Auteur  : K-Challenge
Date    : 2026
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import subprocess
import threading
import time
import logging

logger = logging.getLogger("screen_worker")


class ScreenWorker:
    """Gère un pipeline GStreamer en plein écran."""

    def __init__(self, display_config, camera_defaults):
        self.display = display_config
        self.cam_defaults = camera_defaults
        self.pipeline = None

        self.disp_w = display_config.get("width", 2560)
        self.disp_h = display_config.get("height", 1440)
        self.x_offset = display_config.get("x_offset", 0)
        self.y_offset = display_config.get("y_offset", 0)

        logger.info(f"Écran cible : {self.disp_w}x{self.disp_h}")

    # ──────────────────────────────────────────────
    #  Plein écran sans décorations
    # ──────────────────────────────────────────────

    def _make_fullscreen(self):
        """
        Trouve la fenêtre GStreamer et la met en plein écran sans décorations.
        Lancé dans un thread séparé pour ne pas bloquer GStreamer.
        """
        time.sleep(1.5)

        try:
            # Chercher la fenêtre nv3dsink
            wid = None
            for name in ["nv3dsink", "GStreamer", "gst-launch", "EGLSink"]:
                result = subprocess.run(
                    ["xdotool", "search", "--name", name],
                    capture_output=True, text=True, timeout=3
                )
                ids = result.stdout.strip().split('\n')
                if ids and ids[0] != '':
                    wid = ids[-1]
                    break

            if not wid:
                logger.warning("Fenêtre GStreamer non trouvée — plein écran impossible")
                return

            logger.info(f"Fenêtre GStreamer trouvée : {wid}")

            # Enlever les décorations (borderless)
            subprocess.run(
                ["xdotool", "set_window", "--overrideredirect", "1", wid],
                timeout=3
            )

            # Redimensionner à la taille de l'écran
            subprocess.run(
                ["xdotool", "windowsize", wid, str(self.disp_w), str(self.disp_h)],
                timeout=3
            )

            # Positionner en (0,0)
            subprocess.run(
                ["xdotool", "windowmove", wid, str(self.x_offset), str(self.y_offset)],
                timeout=3
            )

            # Mettre au premier plan
            subprocess.run(["xdotool", "windowactivate", wid], timeout=3)

            time.sleep(0.2)
            subprocess.run(
                ["xdotool", "windowmove", wid, str(self.x_offset), str(self.y_offset)],
                timeout=3
            )

            logger.info(f"Fenêtre plein écran : {self.disp_w}x{self.disp_h}")

        except FileNotFoundError:
            logger.error("xdotool non installé ! → sudo apt install xdotool")
        except Exception as e:
            logger.error(f"Erreur plein écran : {e}")

    # ──────────────────────────────────────────────
    #  Construction de la source caméra
    # ──────────────────────────────────────────────

    def _build_camera_source(self, cam_config):
        """v4l2src → [videocrop] → nvvidconv → I420 NVMM"""
        dev = cam_config["device"]
        fmt = self.cam_defaults["format"]
        w = self.cam_defaults["capture_width"]
        h = self.cam_defaults["capture_height"]
        fps = self.cam_defaults["framerate"]
        flip = cam_config.get("flip_method", 0)
        crop = cam_config.get("crop", None)

        src = (
            f'v4l2src device=/dev/video{dev} ! '
            f'video/x-raw, format=(string){fmt}, '
            f'width=(int){w}, height=(int){h}, '
            f'framerate={fps}/1'
        )

        if crop:
            src += (
                f' ! videocrop '
                f'left={crop.get("left", 0)} '
                f'right={crop.get("right", 0)} '
                f'top={crop.get("top", 0)} '
                f'bottom={crop.get("bottom", 0)}'
            )

        src += (
            f' ! nvvidconv flip-method={flip} ! '
            f'video/x-raw(memory:NVMM), format=(string)I420'
        )

        return src

    # ──────────────────────────────────────────────
    #  Construction des pipelines
    # ──────────────────────────────────────────────

    def _build_fullscreen_pipeline(self, scene):
        """1 caméra → nv3dsink."""
        cam = scene["cameras"][0]
        src = self._build_camera_source(cam)
        return f'{src} ! nv3dsink sync=false'

    def _build_grid_pipeline(self, scene):
        """N caméras → nvcompositor → nv3dsink."""
        layout = scene["layout"]
        cols = layout["cols"]
        rows = layout["rows"]
        cameras = scene["cameras"]

        cell_w = self.disp_w // cols
        cell_h = self.disp_h // rows

        comp_props = []
        for i, cam in enumerate(cameras):
            row = i // cols
            col = i % cols
            comp_props.append(
                f'sink_{i}::xpos={col * cell_w} '
                f'sink_{i}::ypos={row * cell_h} '
                f'sink_{i}::width={cell_w} '
                f'sink_{i}::height={cell_h}'
            )

        pipeline = 'nvcompositor name=comp ' + ' '.join(comp_props)
        pipeline += ' ! nv3dsink sync=false'

        for i, cam in enumerate(cameras):
            src = self._build_camera_source(cam)
            pipeline += f' {src} ! comp.sink_{i}'

        return pipeline

    def build_pipeline_string(self, scene):
        """Construit la chaîne de pipeline selon le type de scène."""
        scene_type = scene.get("type", "fullscreen")
        if scene_type == "fullscreen":
            return self._build_fullscreen_pipeline(scene)
        elif scene_type == "grid":
            return self._build_grid_pipeline(scene)
        else:
            raise ValueError(f"Type de scène inconnu : {scene_type}")

    # ──────────────────────────────────────────────
    #  API publique
    # ──────────────────────────────────────────────

    def start(self, scene):
        """Démarre le pipeline et met la fenêtre en plein écran."""
        pipeline_str = self.build_pipeline_string(scene)
        logger.info(f"Pipeline : {pipeline_str}")

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
        except GLib.Error as e:
            logger.error(f"Erreur parse pipeline : {e}")
            return False

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)
        bus.connect("message::warning", self._on_warning)

        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            logger.error("Impossible de démarrer le pipeline")
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            return False

        logger.info("Pipeline démarré — mise en plein écran...")
        threading.Thread(target=self._make_fullscreen, daemon=True).start()

        return True

    def stop(self):
        """Arrête le pipeline."""
        if self.pipeline is None:
            return
        logger.info("Arrêt du pipeline...")
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
        self.pipeline = None
        logger.info("Pipeline arrêté")

    def is_running(self):
        if self.pipeline is None:
            return False
        _, state, _ = self.pipeline.get_state(0)
        return state == Gst.State.PLAYING

    def _on_error(self, bus, msg):
        err, debug = msg.parse_error()
        logger.error(f"Erreur GStreamer : {err.message}")
        self.stop()

    def _on_warning(self, bus, msg):
        warn, _ = msg.parse_warning()
        logger.warning(f"Warning GStreamer : {warn.message}")

    def _on_eos(self, bus, msg):
        logger.info("EOS")
        self.stop()
