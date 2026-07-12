"""Connection status badge widget."""

from __future__ import annotations

import customtkinter as ctk


class StatusBadge(ctk.CTkFrame):
    """Small colored dot + text label showing server connection state."""

    COLORS = {
        "online": "#4ade80",
        "offline": "#f87171",
        "loading": "#facc15",
    }

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._dot = ctk.CTkLabel(
            self, text="●", width=16,
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS["offline"],
        )
        self._dot.pack(side="left")

        self._label = ctk.CTkLabel(
            self, text="Offline",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        self._label.pack(side="left", padx=(4, 0))

    def set_status(self, state: str, text: str | None = None) -> None:
        """Update badge.  *state* is 'online', 'offline', or 'loading'."""
        color = self.COLORS.get(state, self.COLORS["offline"])
        self._dot.configure(text_color=color)
        self._label.configure(text=text or state.capitalize())
