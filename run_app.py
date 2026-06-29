from __future__ import annotations

import os
import sys
import threading
import webbrowser
from pathlib import Path

from app import app


def resource_path(relative_path: str) -> Path:
    """Return correct path both in normal Python and PyInstaller executable."""
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    return Path(base_path) / relative_path


if __name__ == "__main__":
    os.environ.setdefault("FLASK_ENV", "production")
    url = "http://127.0.0.1:5050"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=5050, debug=False)
