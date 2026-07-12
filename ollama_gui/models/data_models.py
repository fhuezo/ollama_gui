"""Data models for Ollama GUI."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LocalModel:
    """Represents a model stored locally by Ollama."""

    name: str
    size: int  # bytes
    size_display: str  # "4.1 GB"
    digest: str
    modified_at: str
    is_running: bool = False
    vram_size: int | None = None
    expires_at: str | None = None
    processor: str | None = None  # "GPU", "CPU", etc.


@dataclass
class ModelDetails:
    """Full details for a single model (from /api/show)."""

    name: str
    family: str  # e.g. "llama"
    parameter_size: str  # e.g. "8B"
    quantization: str  # e.g. "Q4_0"
    template: str = ""
    system_prompt: str = ""
    license: str = ""
    modelfile: str = ""
    format: str = ""
    parent_model: str = ""


@dataclass
class PullProgress:
    """Progress state for a model pull/download operation."""

    status: str  # "pulling manifest", "pulling abc123..."
    completed: int = 0  # bytes downloaded so far
    total: int = 0  # total bytes
    percent: float = 0.0  # 0.0 - 100.0


@dataclass
class ServerStatus:
    """Overall Ollama server health snapshot."""

    is_online: bool
    version: str | None = None
    model_count: int = 0
    running_count: int = 0
    total_disk_usage: str = "0 B"
    running_models: list[LocalModel] = field(default_factory=list)
