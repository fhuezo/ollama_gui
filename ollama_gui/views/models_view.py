"""Models list view — list, search, delete, and navigate to model details."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ollama_gui.models.data_models import LocalModel
from ollama_gui.services.model_manager import ModelManager
from ollama_gui.utils.threading_utils import run_in_thread
from ollama_gui.views.components.confirmation_dialog import ConfirmationDialog
from ollama_gui.views.components.model_card import ModelCard
from ollama_gui.views.pull_dialog import PullDialog

if TYPE_CHECKING:
    from ollama_gui.app import OllamaGUI


class ModelsView(ctk.CTkFrame):
    """Primary model management screen with search, list, and pull."""

    BG = "#0f0f0f"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    BLUE = "#60a5fa"

    def __init__(self, master, app: "OllamaGUI", **kwargs) -> None:
        super().__init__(master, fg_color=self.BG, **kwargs)
        self._app = app
        self._manager: ModelManager = app.model_manager
        self._models: list[LocalModel] = []
        self._filter_text = ""
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top bar: title + search + pull button
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="Models",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.TEXT,
        ).grid(row=0, column=0, sticky="w")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        search = ctk.CTkEntry(
            top, placeholder_text="🔍 Filter models...",
            textvariable=self._search_var,
            height=36, corner_radius=8,
            fg_color="#1a1a2e", border_color="#334155",
            text_color=self.TEXT, placeholder_text_color=self.TEXT_DIM,
        )
        search.grid(row=0, column=1, padx=16, sticky="ew")

        ctk.CTkButton(
            top, text="📥  Pull Model", width=140, height=36,
            corner_radius=8, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.BLUE, hover_color="#3b82f6",
            command=self._open_pull_dialog,
        ).grid(row=0, column=2, sticky="e")

        # Scrollable model list
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#334155",
            scrollbar_button_hover_color="#475569",
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._scroll.grid_columnconfigure(0, weight=1)

        # Empty state
        self._empty_label = ctk.CTkLabel(
            self._scroll,
            text="No models found. Pull one to get started!",
            font=ctk.CTkFont(size=14), text_color=self.TEXT_DIM,
        )

    def refresh(self) -> None:
        """Reload the model list from Ollama."""
        def _fetch():
            return self._manager.refresh_models()

        def _on_done(models):
            self.after(0, lambda: self._set_models(models))

        def _on_error(exc):
            self.after(0, lambda: self._set_models([]))

        run_in_thread(_fetch, on_success=_on_done, on_error=_on_error)

    def _set_models(self, models: list[LocalModel]) -> None:
        self._models = models
        self._apply_filter()

    def _apply_filter(self) -> None:
        self._filter_text = self._search_var.get().lower().strip()
        filtered = [
            m for m in self._models
            if self._filter_text in m.name.lower()
        ] if self._filter_text else self._models

        # Clear existing cards
        for w in self._scroll.winfo_children():
            w.destroy()

        if not filtered:
            self._empty_label = ctk.CTkLabel(
                self._scroll,
                text="No models found." if self._filter_text else "No models installed. Pull one to get started!",
                font=ctk.CTkFont(size=14), text_color=self.TEXT_DIM,
            )
            self._empty_label.pack(pady=40)
            return

        for i, model in enumerate(filtered):
            card = ModelCard(
                self._scroll,
                model=model,
                on_details=self._show_details,
                on_delete=self._confirm_delete,
                on_stop=self._stop_model,
            )
            card.pack(fill="x", pady=4, padx=4)

    def _show_details(self, name: str) -> None:
        self._app.show_model_detail(name)

    def _confirm_delete(self, name: str) -> None:
        ConfirmationDialog(
            self,
            title="Delete Model",
            message=f"Are you sure you want to delete '{name}'?\n\nThis action cannot be undone.",
            confirm_text="Delete",
            on_confirm=lambda: self._do_delete(name),
            danger=True,
        )

    def _do_delete(self, name: str) -> None:
        def _delete():
            self._manager.delete_model(name)

        def _on_done(_):
            self.after(0, self.refresh)

        run_in_thread(_delete, on_success=_on_done)

    def _stop_model(self, name: str) -> None:
        def _stop():
            self._manager.stop_model(name)

        def _on_done(_):
            self.after(0, self.refresh)

        run_in_thread(_stop, on_success=_on_done)

    def _open_pull_dialog(self) -> None:
        PullDialog(self, self._manager, on_complete=self.refresh)
