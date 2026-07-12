"""Running models view — live monitor of models loaded in memory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ollama_gui.models.data_models import LocalModel, ServerStatus
from ollama_gui.utils.formatting import format_bytes
from ollama_gui.utils.threading_utils import run_in_thread

if TYPE_CHECKING:
    from ollama_gui.app import OllamaGUI


class RunningView(ctk.CTkFrame):
    """Live view of models currently loaded in memory with stop controls."""

    BG = "#0f0f0f"
    CARD_BG = "#1a1a2e"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    GREEN = "#4ade80"
    YELLOW = "#facc15"
    RED = "#f87171"

    def __init__(self, master, app: "OllamaGUI", **kwargs) -> None:
        super().__init__(master, fg_color=self.BG, **kwargs)
        self._app = app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header row
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="Running Models",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            top, text="⏹  Stop All", width=120, height=36,
            corner_radius=8, font=ctk.CTkFont(size=13),
            fg_color=self.RED, hover_color="#ef4444",
            command=self._stop_all,
        ).grid(row=0, column=1, sticky="e")

        # Scrollable list
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#334155",
            scrollbar_button_hover_color="#475569",
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="No models currently loaded in memory",
            font=ctk.CTkFont(size=14), text_color=self.TEXT_DIM,
        )
        self._empty_label.pack(pady=40)

    def update_status(self, status: ServerStatus) -> None:
        """Called by the app when StatusMonitor fires."""
        # Clear
        for w in self._scroll.winfo_children():
            w.destroy()

        if not status.is_online:
            ctk.CTkLabel(
                self._scroll, text="Ollama server is offline",
                font=ctk.CTkFont(size=14), text_color=self.RED,
            ).pack(pady=40)
            return

        if not status.running_models:
            ctk.CTkLabel(
                self._scroll, text="No models currently loaded in memory",
                font=ctk.CTkFont(size=14), text_color=self.TEXT_DIM,
            ).pack(pady=40)
            return

        # Table header
        hdr = ctk.CTkFrame(self._scroll, fg_color="#334155", corner_radius=8, height=36)
        hdr.pack(fill="x", padx=4, pady=(0, 4))
        hdr.grid_columnconfigure(0, weight=2)
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_columnconfigure(2, weight=1)
        hdr.grid_columnconfigure(3, weight=1)
        hdr.grid_columnconfigure(4, weight=0)

        for col, text in enumerate(["Model", "Size", "VRAM", "Processor", ""]):
            ctk.CTkLabel(
                hdr, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.TEXT_DIM, anchor="w",
            ).grid(row=0, column=col, padx=12, pady=8, sticky="w")

        # Rows
        for rm in status.running_models:
            self._add_row(rm)

    def _add_row(self, model: LocalModel) -> None:
        row = ctk.CTkFrame(self._scroll, fg_color=self.CARD_BG, corner_radius=8, height=44)
        row.pack(fill="x", padx=4, pady=2)
        row.grid_columnconfigure(0, weight=2)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=1)
        row.grid_columnconfigure(4, weight=0)

        ctk.CTkLabel(
            row, text=f"  ⚡ {model.name}",
            font=ctk.CTkFont(size=13), text_color=self.GREEN, anchor="w",
        ).grid(row=0, column=0, padx=12, pady=8, sticky="w")

        ctk.CTkLabel(
            row, text=model.size_display,
            font=ctk.CTkFont(size=12), text_color=self.TEXT, anchor="w",
        ).grid(row=0, column=1, padx=12, pady=8, sticky="w")

        vram = format_bytes(model.vram_size) if model.vram_size else "N/A"
        ctk.CTkLabel(
            row, text=vram,
            font=ctk.CTkFont(size=12), text_color=self.TEXT, anchor="w",
        ).grid(row=0, column=2, padx=12, pady=8, sticky="w")

        ctk.CTkLabel(
            row, text=model.processor or "—",
            font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM, anchor="w",
        ).grid(row=0, column=3, padx=12, pady=8, sticky="w")

        ctk.CTkButton(
            row, text="Stop", width=60, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="#334155", hover_color=self.YELLOW,
            command=lambda n=model.name: self._stop_model(n),
        ).grid(row=0, column=4, padx=12, pady=8)

    def _stop_model(self, name: str) -> None:
        def _stop():
            self._app.model_manager.stop_model(name)
        def _on_done(_):
            self.after(0, lambda: self._app.refresh_status())
        run_in_thread(_stop, on_success=_on_done)

    def _stop_all(self) -> None:
        status = self._app.monitor.last_status
        if not status or not status.running_models:
            return
        for rm in status.running_models:
            self._stop_model(rm.name)
