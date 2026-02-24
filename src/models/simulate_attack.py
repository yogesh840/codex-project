"""Utility to push synthetic robotic events into HID Guardian runtime DB.

This script writes synthetic events directly for quick testing.
"""
from __future__ import annotations

import argparse
import time

from src.storage.db import Database


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="robotic", choices=["robotic", "normal"])
    parser.add_argument("--count", type=int, default=80)
    args = parser.parse_args()

    db = Database()
    base = time.time()
    for i in range(args.count):
        interval = 0.03 if args.mode == "robotic" else 0.14
        dwell = 0.03 if args.mode == "robotic" else 0.1
        evt = {"key": f"s{i%26}", "pressed_at": base + interval * i, "released_at": base + interval * i + dwell, "timestamp": base + interval * i}
        db.log_sensor_event("keystroke", evt)
    print(f"Inserted {args.count} {args.mode} synthetic keystrokes")


if __name__ == "__main__":
    main()
