"""Pull dialog — modal for downloading a new model with progress tracking."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ollama_gui.models.data_models import PullProgress
from ollama_gui.services.model_manager import ModelManager
from ollama_gui.utils.formatting import format_bytes
from ollama_gui.utils.threading_utils import run_in_thread
from ollama_gui.views.components.progress_bar import ProgressBarWithLabel


class PullDialog(ctk.CTkToplevel):
    """Modal dialog to pull/download a model with live progress."""

    def __init__(
        self,
        master,
        manager: ModelManager,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.title("Pull Model")
        self.geometry("500x280")
        self.resizable(False, False)
        self.configure(fg_color="#0f0f0f")
        self.grab_set()
        self.transient(master)

        self._manager = manager
        self._on_complete = on_complete
        self._pulling = False

        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self, text="Download a Model",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#f1f5f9",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self, text="Enter a model name from ollama.com (e.g. llama3.2, gemma4:2b)",
            font=ctk.CTkFont(size=12), text_color="#94a3b8",
        ).pack(pady=(0, 16))

        self._name_var = ctk.StringVar()
        self._entry = ctk.CTkEntry(
            self, textvariable=self._name_var,
            placeholder_text="Model name...",
            width=400, height=38, corner_radius=8,
            fg_color="#1a1a2e", border_color="#334155",
            text_color="#f1f5f9", placeholder_text_color="#64748b",
        )
        self._entry.pack()
        self._entry.bind("<Return>", lambda _: self._start_pull())

        # Progress (hidden initially)
        self._progress = ProgressBarWithLabel(self)

        # Buttons
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._btn_frame.pack(pady=16)

        self._cancel_btn = ctk.CTkButton(
            self._btn_frame, text="Cancel", width=100, height=36,
            corner_radius=8, fg_color="#334155", hover_color="#475569",
            command=self._cancel,
        )
        self._cancel_btn.pack(side="left", padx=8)

        self._pull_btn = ctk.CTkButton(
            self._btn_frame, text="Pull", width=100, height=36,
            corner_radius=8, fg_color="#60a5fa", hover_color="#3b82f6",
            font=ctk.CTkFont(weight="bold"),
            command=self._start_pull,
        )
        self._pull_btn.pack(side="left", padx=8)

    def _start_pull(self) -> None:
        name = self._name_var.get().strip()
        if not name or self._pulling:
            return

        self._pulling = True
        self._pull_btn.configure(state="disabled", text="Pulling...")
        self._entry.configure(state="disabled")
        self._progress.pack(fill="x", padx=40, pady=(8, 0))
        self._progress.reset()

        def _pull():
            self._manager.pull_with_progress(name, self._on_progress)

        def _on_done(_):
            self.after(0, self._pull_complete)

        def _on_error(exc):
            self.after(0, lambda: self._pull_error(str(exc)))

        run_in_thread(_pull, on_success=_on_done, on_error=_on_error)

    def _on_progress(self, progress: PullProgress) -> None:
        """Called from the worker thread — marshal to main thread."""
        status = progress.status
        if progress.total > 0:
            dl = format_bytes(progress.completed)
            tot = format_bytes(progress.total)
            status = f"{progress.status}  ({dl} / {tot})"
        self.after(0, lambda: self._progress.update_progress(progress.percent, status))

    def _pull_complete(self) -> None:
        self._pulling = False
        self._progress.update_progress(100.0, "✅ Complete!")
        self._pull_btn.configure(text="Done", state="normal", fg_color="#4ade80")
        self._pull_btn.configure(command=self._close_and_refresh)

    def _pull_error(self, msg: str) -> None:
        self._pulling = False
        self._progress.update_progress(0, f"❌ Error: {msg}")
        self._pull_btn.configure(text="Retry", state="normal", fg_color="#f87171")
        self._pull_btn.configure(command=self._reset)
        self._entry.configure(state="normal")

    def _reset(self) -> None:
        self._progress.reset()
        self._pull_btn.configure(text="Pull", fg_color="#60a5fa", command=self._start_pull)

    def _cancel(self) -> None:
        if not self._pulling:
            self.destroy()

    def _close_and_refresh(self) -> None:
        if self._on_complete:
            self._on_complete()
        self.destroy()
