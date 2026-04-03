#!/usr/bin/env python3
"""GStreamer pipeline management for fullscreen camera display on DP-0."""

import os
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import subprocess
import threading
import time
import logging

logger = logging.getLogger("screen_worker")


class ScreenWorker:
    def __init__(self, display_config, camera_defaults, display=":0"):
        self.cam_defaults = camera_defaults
        self.display = display
        self.pipeline = None

        self.disp_w = display_config.get("width", 2560)
        self.disp_h = display_config.get("height", 1440)

    def _sink(self):
        return (
            f'nv3dsink '
            f'window-x=0 window-y=0 '
            f'window-width={self.disp_w} window-height={self.disp_h} '
            f'sync=false'
        )

    def _xenv(self):
        return {
            **os.environ,
            "DISPLAY": self.display,
            "XAUTHORITY": os.environ.get("XAUTHORITY", "")
        }

    def _remove_decorations(self):
        time.sleep(1.5)
        env = self._xenv()
        try:
            for name in ["nv3dsink", "GStreamer", "gst-launch", "EGLSink"]:
                result = subprocess.run(
                    ["xdotool", "search", "--name", name],
                    capture_output=True, text=True, timeout=3, env=env
                )
                ids = result.stdout.strip().split('\n')
                if ids and ids[0]:
                    wid = ids[-1]
                    subprocess.run(
                        ["xdotool", "set_window", "--overrideredirect", "1", wid],
                        timeout=3, env=env
                    )
                    return
        except FileNotFoundError:
            logger.warning("xdotool not installed — window may show title bar")
        except Exception as e:
            logger.warning(f"Could not remove window decorations: {e}")

    def _build_camera_source(self, cam_config):
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

    def _build_fullscreen_pipeline(self, scene):
        cam = scene["cameras"][0]
        src = self._build_camera_source(cam)
        return f'{src} ! {self._sink()}'

    def _build_grid_pipeline(self, scene):
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
        pipeline += f' ! {self._sink()}'

        for i, cam in enumerate(cameras):
            src = self._build_camera_source(cam)
            pipeline += f' {src} ! comp.sink_{i}'

        return pipeline

    def build_pipeline_string(self, scene):
        scene_type = scene.get("type", "fullscreen")
        if scene_type == "fullscreen":
            return self._build_fullscreen_pipeline(scene)
        elif scene_type == "grid":
            return self._build_grid_pipeline(scene)
        else:
            raise ValueError(f"Unknown scene type: {scene_type}")

    def start(self, scene):
        pipeline_str = self.build_pipeline_string(scene)
        logger.info(f"Pipeline: {pipeline_str}")

        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
        except GLib.Error as e:
            logger.error(f"Pipeline parse error: {e}")
            return False

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self._on_error)
        bus.connect("message::eos", self._on_eos)
        bus.connect("message::warning", self._on_warning)

        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            logger.error("Failed to start pipeline")
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            return False

        logger.info("Pipeline started")
        threading.Thread(target=self._remove_decorations, daemon=True).start()

        return True

    def stop(self):
        if self.pipeline is None:
            return
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
        self.pipeline = None

    def is_running(self):
        if self.pipeline is None:
            return False
        _, state, _ = self.pipeline.get_state(0)
        return state == Gst.State.PLAYING

    def _on_error(self, bus, msg):
        err, _ = msg.parse_error()
        logger.error(f"GStreamer error: {err.message}")
        self.stop()

    def _on_warning(self, bus, msg):
        warn, _ = msg.parse_warning()
        logger.warning(f"GStreamer warning: {warn.message}")

    def _on_eos(self, bus, msg):
        logger.info("EOS received")
        self.stop()
