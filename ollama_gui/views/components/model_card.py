"""Single model row/card used in the models list view."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ollama_gui.models.data_models import LocalModel
from ollama_gui.utils.formatting import format_relative_time


class ModelCard(ctk.CTkFrame):
    """A row representing one local model with action buttons."""

    BG = "#1a1a2e"
    BG_HOVER = "#16213e"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    GREEN = "#4ade80"
    RED = "#f87171"
    BLUE = "#60a5fa"

    def __init__(
        self,
        master,
        model: LocalModel,
        on_details: Callable[[str], None] | None = None,
        on_delete: Callable[[str], None] | None = None,
        on_stop: Callable[[str], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, fg_color=self.BG, corner_radius=10, height=64, **kwargs)
        self.grid_propagate(False)
        self._model = model
        self._on_details = on_details
        self._on_delete = on_delete
        self._on_stop = on_stop

        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)

        # Running indicator dot
        dot = ctk.CTkLabel(
            self, text="●" if self._model.is_running else " ", width=20,
            font=ctk.CTkFont(size=10),
            text_color=self.GREEN,
        )
        dot.grid(row=0, column=0, rowspan=2, padx=(12, 0), sticky="w")

        # Model name
        name_lbl = ctk.CTkLabel(
            self,
            text=self._model.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.TEXT,
            anchor="w",
        )
        name_lbl.grid(row=0, column=1, padx=(8, 0), pady=(10, 0), sticky="w")

        # Metadata line: size · modified · digest
        modified = format_relative_time(self._model.modified_at)
        meta_text = f"{self._model.size_display}  ·  {modified}  ·  {self._model.digest}"
        meta_lbl = ctk.CTkLabel(
            self,
            text=meta_text,
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_DIM,
            anchor="w",
        )
        meta_lbl.grid(row=1, column=1, padx=(8, 0), pady=(0, 10), sticky="w")

        # Action buttons frame
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=(0, 12), sticky="e")

        ctk.CTkButton(
            actions, text="Details", width=70, height=28,
            corner_radius=6, font=ctk.CTkFont(size=12),
            fg_color="#334155", hover_color=self.BLUE,
            command=lambda: self._on_details and self._on_details(self._model.name),
        ).pack(side="left", padx=2)

        if self._model.is_running:
            ctk.CTkButton(
                actions, text="Stop", width=60, height=28,
                corner_radius=6, font=ctk.CTkFont(size=12),
                fg_color="#334155", hover_color="#facc15",
                command=lambda: self._on_stop and self._on_stop(self._model.name),
            ).pack(side="left", padx=2)

        ctk.CTkButton(
            actions, text="Delete", width=65, height=28,
            corner_radius=6, font=ctk.CTkFont(size=12),
            fg_color="#334155", hover_color=self.RED,
            command=lambda: self._on_delete and self._on_delete(self._model.name),
        ).pack(side="left", padx=2)
