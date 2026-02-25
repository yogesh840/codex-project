"""Quick environment check for HID Guardian."""
from __future__ import annotations

import importlib
import platform
import sys

REQUIRED = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "pydantic",
    "sklearn",
    "numpy",
    "yaml",
    "pynput",
]


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.system()} {platform.release()}")
    if sys.version_info < (3, 11):
        print("[FAIL] Python 3.11+ is required")
        return 1

    missing = []
    for pkg in REQUIRED:
        try:
            importlib.import_module(pkg)
            print(f"[OK] {pkg}")
        except Exception:
            missing.append(pkg)
            print(f"[MISSING] {pkg}")

    if missing:
        print("\nInstall missing packages with: pip install -r requirements.txt")
        return 1

    print("\nEnvironment looks ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
