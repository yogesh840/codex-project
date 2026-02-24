"""Main entrypoint for HID Guardian."""
from __future__ import annotations

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.ui.server:app", host="127.0.0.1", port=8000, reload=False)
