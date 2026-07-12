"""Navigation sidebar component."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class Sidebar(ctk.CTkFrame):
    """Fixed-width navigation sidebar with icon-labeled buttons."""

    # Color tokens
    BG = "#1a1a2e"
    BG_HOVER = "#16213e"
    BG_ACTIVE = "#0f3460"
    TEXT = "#94a3b8"
    TEXT_ACTIVE = "#f1f5f9"
    ACCENT = "#60a5fa"

    NAV_ITEMS = [
        ("📊", "Dashboard"),
        ("📦", "Models"),
        ("⚡", "Running"),
        ("💬", "Chat"),
        ("⚙️", "Settings"),
    ]

    def __init__(
        self,
        master: ctk.CTk,
        on_navigate: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, width=220, corner_radius=0, fg_color=self.BG, **kwargs)
        self.grid_propagate(False)
        self._on_navigate = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active: str = "Dashboard"

        self._build()

    def _build(self) -> None:
        # Logo / title area
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(24, 8))

        ctk.CTkLabel(
            title_frame,
            text="🦙 Ollama GUI",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.TEXT_ACTIVE,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Model Manager",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT,
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        sep = ctk.CTkFrame(self, height=1, fg_color="#334155")
        sep.pack(fill="x", padx=16, pady=(16, 8))

        # Nav buttons
        for icon, label in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {label}",
                anchor="w",
                height=40,
                corner_radius=8,
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                text_color=self.TEXT,
                hover_color=self.BG_HOVER,
                command=lambda l=label: self._navigate(l),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._buttons[label] = btn

        self._set_active("Dashboard")

    def _navigate(self, label: str) -> None:
        self._set_active(label)
        self._on_navigate(label)

    def _set_active(self, label: str) -> None:
        # Reset previous
        if self._active in self._buttons:
            self._buttons[self._active].configure(
                fg_color="transparent", text_color=self.TEXT
            )
        # Highlight new
        if label in self._buttons:
            self._buttons[label].configure(
                fg_color=self.BG_ACTIVE, text_color=self.TEXT_ACTIVE
            )
        self._active = label
