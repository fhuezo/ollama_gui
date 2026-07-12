"""Enhanced progress bar with percentage label and status text."""

from __future__ import annotations

import customtkinter as ctk


class ProgressBarWithLabel(ctk.CTkFrame):
    """A progress bar with a percentage label above and status text below."""

    def __init__(self, master, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)

        self._pct_label = ctk.CTkLabel(
            self, text="0%",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f1f5f9",
        )
        self._pct_label.pack(anchor="e", padx=4)

        self._bar = ctk.CTkProgressBar(
            self, height=14, corner_radius=7,
            progress_color="#60a5fa",
            fg_color="#334155",
        )
        self._bar.pack(fill="x", pady=(4, 4))
        self._bar.set(0)

        self._status_label = ctk.CTkLabel(
            self, text="Waiting...",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            anchor="w",
        )
        self._status_label.pack(anchor="w", padx=4)

    def update_progress(self, percent: float, status: str = "") -> None:
        """Set progress (0-100) and optional status text."""
        clamped = max(0.0, min(100.0, percent))
        self._bar.set(clamped / 100.0)
        self._pct_label.configure(text=f"{clamped:.1f}%")
        if status:
            self._status_label.configure(text=status)

    def reset(self) -> None:
        """Reset to initial state."""
        self._bar.set(0)
        self._pct_label.configure(text="0%")
        self._status_label.configure(text="Waiting...")
