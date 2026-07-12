"""Higher-level business logic for model operations."""

from __future__ import annotations

from typing import Any, Callable

from ollama_gui.models.data_models import LocalModel, ModelDetails, PullProgress
from ollama_gui.services.ollama_client import OllamaClient
from ollama_gui.utils.formatting import format_bytes


class ModelManager:
    """Orchestrates model CRUD operations on top of :class:`OllamaClient`."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def refresh_models(self) -> list[LocalModel]:
        """Fetch the full model list, enriching each entry with running state."""
        raw_models = self.client.list_models()
        try:
            running_raw = self.client.list_running()
        except Exception:
            running_raw = []

        # Build a set of running model names for O(1) lookup
        running_map: dict[str, dict[str, Any]] = {}
        for rm in running_raw:
            running_map[rm.get("name", "")] = rm

        models: list[LocalModel] = []
        for m in raw_models:
            name = m.get("name", m.get("model", ""))
            size = m.get("size", 0)
            running_info = running_map.get(name)
            
            processor = None
            if running_info:
                vram = running_info.get("size_vram", 0)
                model_size = running_info.get("size", size)
                if model_size > 0:
                    gpu_pct = int((vram / model_size) * 100)
                    gpu_pct = min(100, max(0, gpu_pct))
                    cpu_pct = 100 - gpu_pct
                    if gpu_pct == 100:
                        processor = "100% GPU"
                    elif gpu_pct == 0:
                        processor = "100% CPU"
                    else:
                        processor = f"{gpu_pct}% GPU / {cpu_pct}% CPU"
                else:
                    processor = "100% GPU" if vram > 0 else "100% CPU"

            models.append(
                LocalModel(
                    name=name,
                    size=size,
                    size_display=format_bytes(size),
                    digest=m.get("digest", "")[:12],
                    modified_at=m.get("modified_at", ""),
                    is_running=name in running_map,
                    vram_size=running_info.get("size_vram") if running_info else None,
                    expires_at=running_info.get("expires_at") if running_info else None,
                    processor=processor,
                )
            )
        return models

    # ------------------------------------------------------------------
    # Details
    # ------------------------------------------------------------------

    def get_model_details(self, name: str) -> ModelDetails:
        """Fetch and parse full model info into a :class:`ModelDetails`."""
        raw = self.client.show_model(name)
        details = raw.get("details", {})
        return ModelDetails(
            name=name,
            family=details.get("family", "unknown"),
            parameter_size=details.get("parameter_size", "?"),
            quantization=details.get("quantization_level", "?"),
            template=raw.get("template", ""),
            system_prompt=raw.get("system", ""),
            license=raw.get("license", ""),
            modelfile=raw.get("modelfile", ""),
            format=details.get("format", ""),
            parent_model=details.get("parent_model", ""),
        )

    # ------------------------------------------------------------------
    # Pull with progress
    # ------------------------------------------------------------------

    def pull_with_progress(
        self,
        name: str,
        progress_callback: Callable[[PullProgress], None] | None = None,
    ) -> None:
        """Download a model, reporting progress via *progress_callback*."""

        def _on_progress(status: str, completed: int, total: int) -> None:
            pct = (completed / total * 100) if total > 0 else 0.0
            if progress_callback:
                progress_callback(
                    PullProgress(
                        status=status,
                        completed=completed,
                        total=total,
                        percent=pct,
                    )
                )

        self.client.pull_model(name, callback=_on_progress)

    # ------------------------------------------------------------------
    # Delete / Copy / Stop
    # ------------------------------------------------------------------

    def delete_model(self, name: str) -> None:
        """Delete a model from local storage."""
        self.client.delete_model(name)

    def copy_model(self, source: str, destination: str) -> None:
        """Duplicate a model under a new name."""
        self.client.copy_model(source, destination)

    def stop_model(self, name: str) -> None:
        """Unload a model from memory."""
        self.client.stop_model(name)

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    def get_disk_usage(self) -> str:
        """Return total disk usage across all local models as a display string."""
        models = self.client.list_models()
        total = sum(m.get("size", 0) for m in models)
        return format_bytes(total)
