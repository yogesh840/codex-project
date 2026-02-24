"""Keystroke collection with pynput and simulation fallback."""
from __future__ import annotations

import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque

try:
    from pynput import keyboard
except Exception:  # pragma: no cover - optional runtime dependency behavior
    keyboard = None


@dataclass
class KeyEvent:
    key: str
    pressed_at: float
    released_at: float


class KeystrokeSensor:
    def __init__(self, window_size: int = 80) -> None:
        self.window_size = window_size
        self.events: Deque[KeyEvent] = deque(maxlen=window_size)
        self._pressed: dict[str, float] = {}
        self._listener = None
        self._lock = threading.Lock()

    def _on_press(self, key) -> None:
        k = str(key)
        with self._lock:
            self._pressed[k] = time.time()

    def _on_release(self, key) -> None:
        k = str(key)
        now = time.time()
        with self._lock:
            pressed = self._pressed.pop(k, now)
            self.events.append(KeyEvent(k, pressed_at=pressed, released_at=now))

    def start(self) -> None:
        if keyboard is None:
            return
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()

    def get_window(self) -> list[dict]:
        with self._lock:
            return [e.__dict__ for e in list(self.events)]

    def simulate(self, robotic: bool = False, count: int = 30) -> None:
        now = time.time()
        for i in range(count):
            dwell = 0.03 if robotic else random.uniform(0.06, 0.18)
            gap = 0.03 if robotic else random.uniform(0.04, 0.2)
            press_t = now + i * gap
            release_t = press_t + dwell
            self.events.append(KeyEvent(f"k{i % 26}", press_t, release_t))
