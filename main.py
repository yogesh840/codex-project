"""Main entrypoint for HID Guardian."""
from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    host = os.getenv("HID_GUARDIAN_HOST", "127.0.0.1")
    port = int(os.getenv("HID_GUARDIAN_PORT", "8000"))
    reload_enabled = os.getenv("HID_GUARDIAN_RELOAD", "false").lower() == "true"
    uvicorn.run("src.ui.server:app", host=host, port=port, reload=reload_enabled)
