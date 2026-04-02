#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
keyboard_listener.py
--------------------
Écoute les touches clavier depuis le terminal SSH pour naviguer les scènes.

Touches :
  ← (flèche gauche)  : scène précédente (PREV)
  → (flèche droite)  : scène suivante   (NEXT)
  r                   : recharger la config JSON
  q / Ctrl+C          : quitter

Sur le bateau, ce module sera remplacé par gpio_listener.py
qui lit les boutons physiques via Jetson.GPIO.

Auteur  : K-Challenge
Date    : 2026
"""

import sys
import os
import tty
import termios
import threading
import logging

logger = logging.getLogger("keyboard_listener")


class KeyboardListener:
    """Écoute les touches clavier dans un thread séparé."""

    def __init__(self, on_next=None, on_prev=None, on_reload=None, on_quit=None):
        self.on_next = on_next
        self.on_prev = on_prev
        self.on_reload = on_reload
        self.on_quit = on_quit
        self._running = False
        self._thread = None
        self._old_settings = None

    def start(self):
        """Démarre l'écoute clavier dans un thread dédié."""
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        logger.info("Keyboard listener démarré")
        logger.info("  ← PREV  |  → NEXT  |  r RELOAD  |  q QUIT")

    def stop(self):
        """Arrête l'écoute clavier."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Keyboard listener arrêté")

    def _read_key(self, fd):
        """
        Lit une touche ou séquence d'échappement.
        Flèches = ESC [ C (droite) / ESC [ D (gauche)
        """
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
        """Boucle principale d'écoute en mode raw."""
        fd = sys.stdin.fileno()

        try:
            self._old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)

            while self._running:
                key = self._read_key(fd)

                if key == 'RIGHT':
                    logger.debug("→ NEXT")
                    if self.on_next:
                        self.on_next()

                elif key == 'LEFT':
                    logger.debug("← PREV")
                    if self.on_prev:
                        self.on_prev()

                elif key in ('r', 'R'):
                    logger.debug("R — RELOAD")
                    if self.on_reload:
                        self.on_reload()

                elif key in ('q', 'Q', '\x03'):
                    logger.info("Q — QUIT")
                    if self.on_quit:
                        self.on_quit()
                    self._running = False

        except Exception as e:
            logger.error(f"Erreur keyboard listener : {e}")

        finally:
            if self._old_settings:
                termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)

    def restore_terminal(self):
        """Restaure le terminal en mode normal."""
        if self._old_settings:
            fd = sys.stdin.fileno()
            termios.tcsetattr(fd, termios.TCSADRAIN, self._old_settings)
