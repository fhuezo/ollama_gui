"""Dashboard view — landing page with server status, model summary, and quick actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ollama_gui.models.data_models import ServerStatus
from ollama_gui.utils.formatting import format_bytes

if TYPE_CHECKING:
    from ollama_gui.app import OllamaGUI


class DashboardView(ctk.CTkFrame):
    """Birds-eye overview: server health, model counts, disk usage, running models."""

    BG = "#0f0f0f"
    CARD_BG = "#1a1a2e"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    GREEN = "#4ade80"
    RED = "#f87171"
    BLUE = "#60a5fa"

    def __init__(self, master, app: "OllamaGUI", **kwargs) -> None:
        super().__init__(master, fg_color=self.BG, **kwargs)
        self._app = app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Header
        header = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.TEXT,
            anchor="w",
        )
        header.grid(row=0, column=0, columnspan=2, sticky="w", padx=24, pady=(24, 16))

        # Row 1: Server Status + Models Summary
        self._server_card = self._create_card(self, row=1, col=0)
        self._models_card = self._create_card(self, row=1, col=1)

        # Row 2: Running Models + Quick Actions
        self._running_card = self._create_card(self, row=2, col=0)
        self._actions_card = self._create_card(self, row=2, col=1)

        # Default content
        self._populate_offline()
        self._populate_quick_actions()

    def _create_card(self, parent, row: int, col: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=self.CARD_BG, corner_radius=12)
        card.grid(row=row, column=col, padx=12, pady=8, sticky="nsew")
        parent.grid_rowconfigure(row, weight=1)
        return card

    def _clear_card(self, card: ctk.CTkFrame) -> None:
        for w in card.winfo_children():
            w.destroy()

    def _populate_offline(self) -> None:
        """Show offline state for server and empty cards."""
        self._clear_card(self._server_card)
        ctk.CTkLabel(
            self._server_card, text="Server Status",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            self._server_card, text="●  Offline",
            font=ctk.CTkFont(size=14), text_color=self.RED,
        ).pack(anchor="w", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            self._server_card, text="Make sure Ollama is running (ollama serve)",
            font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM, wraplength=300,
        ).pack(anchor="w", padx=16, pady=(0, 16))

        self._clear_card(self._models_card)
        ctk.CTkLabel(
            self._models_card, text="Models",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            self._models_card, text="—",
            font=ctk.CTkFont(size=14), text_color=self.TEXT_DIM,
        ).pack(anchor="w", padx=16, pady=(0, 16))

        self._clear_card(self._running_card)
        ctk.CTkLabel(
            self._running_card, text="Running Models",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            self._running_card, text="No models loaded",
            font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
        ).pack(anchor="w", padx=16, pady=(0, 16))

    def _populate_quick_actions(self) -> None:
        self._clear_card(self._actions_card)
        ctk.CTkLabel(
            self._actions_card, text="Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 12))

        ctk.CTkButton(
            self._actions_card, text="📥  Pull New Model",
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            fg_color=self.BLUE, hover_color="#3b82f6",
            command=lambda: self._app.navigate("Models"),
        ).pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            self._actions_card, text="🔄  Refresh",
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            fg_color="#334155", hover_color="#475569",
            command=lambda: self._app.refresh_status(),
        ).pack(fill="x", padx=16, pady=4)

        ctk.CTkButton(
            self._actions_card, text="💬  Test a Model",
            height=36, corner_radius=8, font=ctk.CTkFont(size=13),
            fg_color="#334155", hover_color="#475569",
            command=lambda: self._app.navigate("Chat"),
        ).pack(fill="x", padx=16, pady=(4, 16))

    def update_status(self, status: ServerStatus) -> None:
        """Called by the app whenever the StatusMonitor fires."""
        # --- Server card ---
        self._clear_card(self._server_card)
        ctk.CTkLabel(
            self._server_card, text="Server Status",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        if status.is_online:
            ctk.CTkLabel(
                self._server_card, text="●  Online",
                font=ctk.CTkFont(size=14), text_color=self.GREEN,
            ).pack(anchor="w", padx=16, pady=(0, 4))
            ver = status.version or "unknown"
            ctk.CTkLabel(
                self._server_card, text=f"Version: {ver}",
                font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
            ).pack(anchor="w", padx=16, pady=(0, 16))
        else:
            ctk.CTkLabel(
                self._server_card, text="●  Offline",
                font=ctk.CTkFont(size=14), text_color=self.RED,
            ).pack(anchor="w", padx=16, pady=(0, 4))
            ctk.CTkLabel(
                self._server_card, text="Make sure Ollama is running",
                font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
            ).pack(anchor="w", padx=16, pady=(0, 16))

        # --- Models summary card ---
        self._clear_card(self._models_card)
        ctk.CTkLabel(
            self._models_card, text="Models",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        if status.is_online:
            ctk.CTkLabel(
                self._models_card,
                text=f"{status.model_count} model{'s' if status.model_count != 1 else ''} installed",
                font=ctk.CTkFont(size=14), text_color=self.TEXT,
            ).pack(anchor="w", padx=16, pady=(0, 4))
            ctk.CTkLabel(
                self._models_card, text=f"Disk usage: {status.total_disk_usage}",
                font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
            ).pack(anchor="w", padx=16, pady=(0, 16))
        else:
            ctk.CTkLabel(
                self._models_card, text="—",
                font=ctk.CTkFont(size=14), text_color=self.TEXT_DIM,
            ).pack(anchor="w", padx=16, pady=(0, 16))

        # --- Running models card ---
        self._clear_card(self._running_card)
        ctk.CTkLabel(
            self._running_card, text="Running Models",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        if status.is_online and status.running_models:
            for rm in status.running_models:
                vram_str = format_bytes(rm.vram_size) if rm.vram_size else "N/A"
                ctk.CTkLabel(
                    self._running_card,
                    text=f"  ⚡ {rm.name}  —  VRAM: {vram_str}",
                    font=ctk.CTkFont(size=12), text_color=self.GREEN, anchor="w",
                ).pack(anchor="w", padx=16, pady=1)
            # spacer
            ctk.CTkLabel(self._running_card, text="", height=8).pack()
        else:
            ctk.CTkLabel(
                self._running_card, text="No models loaded",
                font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
            ).pack(anchor="w", padx=16, pady=(0, 16))
