"""Low-level HTTP client wrapping every Ollama REST API endpoint."""

from __future__ import annotations

import json
from typing import Any, Callable

import requests

from ollama_gui.utils import config


class OllamaError(Exception):
    """Raised when an Ollama API call fails."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OllamaClient:
    """Thin wrapper around the Ollama REST API.

    Every public method maps 1-to-1 to an API endpoint documented at
    https://docs.ollama.com/api.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or config.get("server_url")).rstrip("/")
        self._session = requests.Session()
        self._connect_timeout: int = config.get("connect_timeout")
        self._read_timeout: int = config.get("read_timeout")

    @property
    def _timeout(self) -> tuple[int, int]:
        return (self._connect_timeout, self._read_timeout)

    # ------------------------------------------------------------------
    # Health / meta
    # ------------------------------------------------------------------

    def check_health(self) -> bool:
        """Return True if the Ollama server is reachable."""
        try:
            r = self._session.get(self.base_url, timeout=(self._connect_timeout, 5))
            return r.status_code == 200
        except requests.ConnectionError:
            return False
        except Exception:
            return False

    def get_version(self) -> str | None:
        """Return the Ollama server version string, or None on failure."""
        try:
            r = self._session.get(
                f"{self.base_url}/api/version", timeout=self._timeout
            )
            r.raise_for_status()
            return r.json().get("version")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Model listing
    # ------------------------------------------------------------------

    def list_models(self) -> list[dict[str, Any]]:
        """GET /api/tags — list all locally stored models."""
        r = self._session.get(f"{self.base_url}/api/tags", timeout=self._timeout)
        self._check(r)
        return r.json().get("models", [])

    def list_running(self) -> list[dict[str, Any]]:
        """GET /api/ps — list models currently loaded in memory."""
        r = self._session.get(f"{self.base_url}/api/ps", timeout=self._timeout)
        self._check(r)
        return r.json().get("models", [])

    # ------------------------------------------------------------------
    # Model details
    # ------------------------------------------------------------------

    def show_model(self, name: str) -> dict[str, Any]:
        """POST /api/show — return full model details."""
        r = self._session.post(
            f"{self.base_url}/api/show",
            json={"name": name},
            timeout=self._timeout,
        )
        self._check(r)
        return r.json()

    # ------------------------------------------------------------------
    # Pull / download
    # ------------------------------------------------------------------

    def pull_model(
        self,
        name: str,
        callback: Callable[[str, int, int], None] | None = None,
    ) -> None:
        """POST /api/pull — stream-download a model.

        *callback(status, completed_bytes, total_bytes)* is called for
        every progress line received from the server.
        """
        r = self._session.post(
            f"{self.base_url}/api/pull",
            json={"name": name, "stream": True},
            stream=True,
            timeout=(self._connect_timeout, 600),  # pulls can be very slow
        )
        self._check(r)
        for line in r.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            status = data.get("status", "")
            completed = data.get("completed", 0)
            total = data.get("total", 0)
            if callback:
                callback(status, completed, total)
            if "error" in data:
                raise OllamaError(data["error"])

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_model(self, name: str) -> None:
        """DELETE /api/delete — remove a model from local storage."""
        r = self._session.delete(
            f"{self.base_url}/api/delete",
            json={"name": name},
            timeout=self._timeout,
        )
        self._check(r)

    # ------------------------------------------------------------------
    # Copy / rename
    # ------------------------------------------------------------------

    def copy_model(self, source: str, destination: str) -> None:
        """POST /api/copy — duplicate a model under a new name."""
        r = self._session.post(
            f"{self.base_url}/api/copy",
            json={"source": source, "destination": destination},
            timeout=self._timeout,
        )
        self._check(r)

    # ------------------------------------------------------------------
    # Create (from Modelfile)
    # ------------------------------------------------------------------

    def create_model(
        self,
        name: str,
        modelfile: str,
        callback: Callable[[str], None] | None = None,
    ) -> None:
        """POST /api/create — create a custom model from a Modelfile string."""
        r = self._session.post(
            f"{self.base_url}/api/create",
            json={"name": name, "modelfile": modelfile, "stream": True},
            stream=True,
            timeout=(self._connect_timeout, 600),
        )
        self._check(r)
        for line in r.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if callback:
                callback(data.get("status", ""))
            if "error" in data:
                raise OllamaError(data["error"])

    # ------------------------------------------------------------------
    # Generate (for the chat/test panel)
    # ------------------------------------------------------------------

    def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        options: dict[str, Any] | None = None,
        callback: Callable[[str, bool], None] | None = None,
    ) -> str:
        """POST /api/generate — stream a completion.

        *callback(token, is_done)* is called for each token chunk.
        Returns the full concatenated response.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options
        r = self._session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            stream=True,
            timeout=(self._connect_timeout, 300),
        )
        self._check(r)
        full_response = ""
        for line in r.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "error" in data:
                raise OllamaError(data["error"])
            token = data.get("response", "")
            done = data.get("done", False)
            full_response += token
            if callback:
                callback(token, done)
        return full_response

    # ------------------------------------------------------------------
    # Stop (unload from memory)
    # ------------------------------------------------------------------

    def stop_model(self, name: str) -> None:
        """Unload a model from memory by setting keep_alive to 0."""
        r = self._session.post(
            f"{self.base_url}/api/generate",
            json={"model": name, "keep_alive": 0},
            timeout=self._timeout,
        )
        self._check(r)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _check(self, response: requests.Response) -> None:
        """Raise OllamaError on non-2xx status codes."""
        if response.status_code >= 400:
            try:
                msg = response.json().get("error", response.text)
            except Exception:
                msg = response.text
            raise OllamaError(msg, status_code=response.status_code)
