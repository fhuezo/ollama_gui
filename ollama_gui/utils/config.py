"""Application configuration — load/save from ~/.ollama_gui/config.json."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_CONFIG_DIR = Path.home() / ".ollama_gui"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

_DEFAULTS: dict[str, Any] = {
    "server_url": "http://localhost:11434",
    "theme": "dark",
    "refresh_interval": 5,  # seconds
    "connect_timeout": 5,  # seconds
    "read_timeout": 30,  # seconds
    "window_width": 1100,
    "window_height": 700,
}

_lock = threading.Lock()
_config: dict[str, Any] | None = None


def _ensure_dir() -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    """Load configuration from disk, falling back to defaults."""
    global _config
    with _lock:
        if _config is not None:
            return _config.copy()
        _ensure_dir()
        if _CONFIG_FILE.exists():
            try:
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    disk = json.load(f)
            except (json.JSONDecodeError, OSError):
                disk = {}
        else:
            disk = {}
        # Merge defaults with saved values
        _config = {**_DEFAULTS, **disk}
        return _config.copy()


def save(updates: dict[str, Any] | None = None) -> None:
    """Persist configuration to disk. Optionally merge *updates* first."""
    global _config
    with _lock:
        if _config is None:
            _config = {**_DEFAULTS}
        if updates:
            _config.update(updates)
        _ensure_dir()
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(_config, f, indent=2)


def get(key: str) -> Any:
    """Get a single config value (loads lazily)."""
    cfg = load()
    return cfg.get(key, _DEFAULTS.get(key))


def reset() -> None:
    """Reset configuration to defaults and save."""
    global _config
    with _lock:
        _config = {**_DEFAULTS}
    save()
