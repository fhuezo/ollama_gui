"""Confirmation dialog for destructive actions."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk


class ConfirmationDialog(ctk.CTkToplevel):
    """Modal "Are you sure?" dialog with Cancel / Confirm buttons."""

    def __init__(
        self,
        master,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_text: str = "Delete",
        on_confirm: Callable[[], None] | None = None,
        danger: bool = True,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.configure(fg_color="#0f0f0f")
        self.grab_set()  # modal

        self._on_confirm = on_confirm

        # Center the dialog
        self.transient(master)

        # Message
        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="#f1f5f9",
            wraplength=360,
        ).pack(pady=(30, 20), padx=20)

        # Button row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            height=36,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            command=self.destroy,
        ).pack(side="left", padx=8)

        confirm_color = "#dc2626" if danger else "#2563eb"
        confirm_hover = "#ef4444" if danger else "#3b82f6"
        ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            width=100,
            height=36,
            corner_radius=8,
            fg_color=confirm_color,
            hover_color=confirm_hover,
            command=self._confirm,
        ).pack(side="left", padx=8)

    def _confirm(self) -> None:
        if self._on_confirm:
            self._on_confirm()
        self.destroy()
