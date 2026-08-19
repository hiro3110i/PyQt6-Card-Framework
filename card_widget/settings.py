"""Per-card window settings loaded from the user's config directory."""

from __future__ import annotations

import json
from pathlib import Path


def settings_path(script_path: str) -> Path:
    """Return the configuration path for a directly executed Python script."""
    script_name = Path(script_path).stem
    return Path.home() / "config" / "pyqt6-cards" / f"{script_name}.json"


def load_window_settings(script_path: str) -> dict:
    """Load a card's JSON settings, returning defaults on missing or invalid input."""
    path = settings_path(script_path)
    try:
        with path.open(encoding="utf-8") as config_file:
            settings = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return settings if isinstance(settings, dict) else {}