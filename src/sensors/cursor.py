"""Cursor movement and click event collection."""
from __future__ import annotations

import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque

try:
    from pynput import mouse
except Exception:  # pragma: no cover
    mouse = None


@dataclass
class CursorEvent:
    x: float
    y: float
    timestamp: float
    event_type: str


class CursorSensor:
    def __init__(self, window_size: int = 150) -> None:
        self.events: Deque[CursorEvent] = deque(maxlen=window_size)
        self._listener = None
        self._lock = threading.Lock()

    def _on_move(self, x, y) -> None:
        with self._lock:
            self.events.append(CursorEvent(x=x, y=y, timestamp=time.time(), event_type="move"))

    def _on_click(self, x, y, button, pressed) -> None:
        if pressed:
            with self._lock:
                self.events.append(CursorEvent(x=x, y=y, timestamp=time.time(), event_type="click"))

    def start(self) -> None:
        if mouse is None:
            return
        self._listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()

    def get_window(self) -> list[dict]:
        with self._lock:
            return [e.__dict__ for e in list(self.events)]

    def simulate(self, robotic: bool = False, count: int = 100) -> None:
        base = time.time()
        x, y = 500.0, 400.0
        for i in range(count):
            dt = 0.02 if robotic else random.uniform(0.01, 0.08)
            if robotic:
                x += 3
                y += 3
            else:
                x += random.uniform(-20, 20)
                y += random.uniform(-20, 20)
            self.events.append(CursorEvent(x, y, base + i * dt, "move"))
            if i % 20 == 0:
                self.events.append(CursorEvent(x, y, base + i * dt, "click"))
