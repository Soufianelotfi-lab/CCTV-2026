#!/usr/bin/env python3
"""GPIO button listener for scene navigation — Jetson AGX Orin GPIO08 (board pin 16)."""

import logging
import Jetson.GPIO as GPIO

logger = logging.getLogger("gpio_listener")

# Physical board pin 16 = GPIO08 on Jetson AGX Orin 40-pin header
# Pin 17 = 3.3V powers the button → RISING edge when pressed
GPIO_PIN = 16
DEBOUNCE_MS = 300


class GPIOListener:
    def __init__(self, on_next=None):
        self.on_next = on_next
        self._running = False

    def start(self):
        GPIO.setmode(GPIO.BOARD)
        # Pull-down: pin is LOW at rest, goes HIGH (3.3V) when button pressed
        GPIO.setup(GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(
            GPIO_PIN,
            GPIO.RISING,
            callback=self._on_press,
            bouncetime=DEBOUNCE_MS,
        )
        self._running = True
        logger.info(f"GPIO listener started — BOARD pin {GPIO_PIN} (GPIO08), debounce {DEBOUNCE_MS}ms")

    def stop(self):
        self._running = False
        try:
            GPIO.remove_event_detect(GPIO_PIN)
            GPIO.cleanup(GPIO_PIN)
            logger.info("GPIO listener stopped and pin cleaned up")
        except Exception as e:
            logger.warning(f"GPIO cleanup error: {e}")

    def _on_press(self, channel):
        if not self._running:
            return
        logger.debug(f"GPIO press on pin {channel} → NEXT scene")
        if self.on_next:
            self.on_next()
