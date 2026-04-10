#!/usr/bin/env python3
"""Raw terminal keyboard listener for scene navigation (← → r q)."""

import sys
import os
import tty
import termios
import threading
import logging

logger = logging.getLogger("keyboard_listener")


class KeyboardListener:
    def __init__(self, on_next=None, on_prev=None, on_reload=None, on_quit=None):
        self.on_next = on_next
        self.on_prev = on_prev
        self.on_reload = on_reload
        self.on_quit = on_quit
        self._running = False
        self._thread = None
        self._old_settings = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _read_key(self, fd):
        ch = os.read(fd, 1).decode('utf-8', errors='ignore')

        if ch == '\x1b':
            ch2 = os.read(fd, 1).decode('utf-8', errors='ignore')
            if ch2 == '[':
                ch3 = os.read(fd, 1).decode('utf-8', errors='ignore')
                if ch3 == 'C':
                    return 'RIGHT'
                elif ch3 == 'D':
                    return 'LEFT'
                elif ch3 == 'A':
                    return 'UP'
                elif ch3 == 'B':
                    return 'DOWN'
            return 'ESC'

        return ch

    def _listen(self):
        fd = sys.stdin.fileno()

        try:
            self._old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

            while self._running:
                key = self._read_key(fd)

                if key == 'RIGHT':
                    logger.debug("Key → (NEXT)")
                    if self.on_next:
                        self.on_next()

                elif key == 'LEFT':
                    logger.debug("Key ← (PREV)")
                    if self.on_prev:
                        self.on_prev()

                elif key in ('r', 'R'):
                    logger.debug("Key R (RELOAD)")
                    if self.on_reload:
                        self.on_reload()

                elif key in ('q', 'Q', '\x03'):
                    logger.debug("Key Q (QUIT)")
                    if self.on_quit:
                        self.on_quit()
                    self._running = False

        except Exception as e:
            logger.error(f"Keyboard listener error: {e}")

        finally:
            if self._old_settings:
                termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)

    def restore_terminal(self):
        if self._old_settings:
            fd = sys.stdin.fileno()
            termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)
