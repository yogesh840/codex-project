"""USB HID monitoring abstraction.

Windows-specific integrations (WMI/pywin32) can be inserted into `_enumerate_windows`.
"""
from __future__ import annotations

import platform
import random
import threading
import time
from dataclasses import dataclass


@dataclass
class USBEvent:
    action: str
    vid: str
    pid: str
    product: str
    klass: str
    trusted: bool


class USBMonitor:
    def __init__(self, whitelist: set[str] | None = None) -> None:
        self.whitelist = whitelist or {"046D:C52B", "045E:07FD"}
        self.connected: dict[str, dict] = {}
        self._events: list[dict] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def _enumerate(self) -> dict[str, dict]:
        if platform.system() == "Windows":
            return self._enumerate_windows()
        return self._enumerate_stub()

    def _enumerate_windows(self) -> dict[str, dict]:
        # Placeholder: swap with WMI-backed enumeration in production.
        return self._enumerate_stub()

    def _enumerate_stub(self) -> dict[str, dict]:
        return {
            "046D:C52B": {"vid": "046D", "pid": "C52B", "product": "USB Receiver", "class": "HID"},
        }

    def _poll_loop(self) -> None:
        while self._running:
            new_state = self._enumerate()
            with self._lock:
                prev_keys = set(self.connected)
                curr_keys = set(new_state)
                for key in curr_keys - prev_keys:
                    dev = new_state[key]
                    evt = {
                        "action": "connect",
                        "vid": dev["vid"],
                        "pid": dev["pid"],
                        "product": dev["product"],
                        "class": dev["class"],
                        "trusted": key in self.whitelist,
                    }
                    self._events.append(evt)
                for key in prev_keys - curr_keys:
                    dev = self.connected[key]
                    evt = {
                        "action": "disconnect",
                        "vid": dev["vid"],
                        "pid": dev["pid"],
                        "product": dev["product"],
                        "class": dev["class"],
                        "trusted": key in self.whitelist,
                    }
                    self._events.append(evt)
                self.connected = new_state
            time.sleep(2)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def get_events(self) -> list[dict]:
        with self._lock:
            events = self._events[:]
            self._events.clear()
            return events

    def get_connected(self) -> list[dict]:
        with self._lock:
            return [{**v, "trusted": f"{v['vid']}:{v['pid']}" in self.whitelist} for v in self.connected.values()]

    def simulate_untrusted(self) -> None:
        with self._lock:
            vid = f"1BAD"
            pid = f"{random.randint(1000,9999)}"
            self._events.append(
                {
                    "action": "connect",
                    "vid": vid,
                    "pid": pid,
                    "product": "Unknown HID Injector",
                    "class": "HID",
                    "trusted": False,
                }
            )
