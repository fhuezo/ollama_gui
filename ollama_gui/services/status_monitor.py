"""Background polling service that monitors Ollama server health."""

from __future__ import annotations

import threading
from typing import Callable

from ollama_gui.models.data_models import LocalModel, ServerStatus
from ollama_gui.services.ollama_client import OllamaClient
from ollama_gui.services.model_manager import ModelManager
from ollama_gui.utils import config


class StatusMonitor:
    """Periodically polls the Ollama server and notifies subscribers.

    Usage::

        monitor = StatusMonitor(on_status=update_ui)
        monitor.start()
        ...
        monitor.stop()
    """

    def __init__(
        self,
        client: OllamaClient | None = None,
        on_status: Callable[[ServerStatus], None] | None = None,
        interval: float | None = None,
    ) -> None:
        self.client = client or OllamaClient()
        self._manager = ModelManager(self.client)
        self._on_status = on_status
        self._interval = interval or config.get("refresh_interval")
        self._timer: threading.Timer | None = None
        self._running = False
        self._last_status: ServerStatus | None = None

    @property
    def last_status(self) -> ServerStatus | None:
        return self._last_status

    def start(self) -> None:
        """Begin polling."""
        self._running = True
        self._tick()

    def stop(self) -> None:
        """Stop polling."""
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def set_interval(self, seconds: float) -> None:
        """Change the polling interval (takes effect on next tick)."""
        self._interval = seconds

    def force_refresh(self) -> None:
        """Immediately trigger a poll (non-blocking)."""
        threading.Thread(target=self._poll, daemon=True).start()

    # ------------------------------------------------------------------

    def _tick(self) -> None:
        if not self._running:
            return
        self._poll()
        self._timer = threading.Timer(self._interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _poll(self) -> None:
        try:
            is_online = self.client.check_health()
            if not is_online:
                status = ServerStatus(is_online=False)
            else:
                version = self.client.get_version()
                models = self._manager.refresh_models()
                running = [m for m in models if m.is_running]
                disk_usage = self._manager.get_disk_usage()
                status = ServerStatus(
                    is_online=True,
                    version=version,
                    model_count=len(models),
                    running_count=len(running),
                    total_disk_usage=disk_usage,
                    running_models=running,
                )
        except Exception:
            status = ServerStatus(is_online=False)
        self._last_status = status
        if self._on_status:
            self._on_status(status)
