"""Model detail view — full info panel with tabs for a single model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ollama_gui.models.data_models import ModelDetails
from ollama_gui.services.model_manager import ModelManager
from ollama_gui.utils.threading_utils import run_in_thread

if TYPE_CHECKING:
    from ollama_gui.app import OllamaGUI


class ModelDetailView(ctk.CTkFrame):
    """Shows full details for a single model in a tabbed layout."""

    BG = "#0f0f0f"
    CARD_BG = "#1a1a2e"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    BLUE = "#60a5fa"
    GREEN = "#4ade80"

    def __init__(self, master, app: "OllamaGUI", **kwargs) -> None:
        super().__init__(master, fg_color=self.BG, **kwargs)
        self._app = app
        self._manager: ModelManager = app.model_manager
        self._model_name: str = ""
        self._details: ModelDetails | None = None
        self._build_skeleton()

    def _build_skeleton(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Back button + title row
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))

        ctk.CTkButton(
            top, text="← Back", width=80, height=32,
            corner_radius=8, font=ctk.CTkFont(size=13),
            fg_color="#334155", hover_color="#475569",
            command=lambda: self._app.navigate("Models"),
        ).pack(side="left")

        self._title_label = ctk.CTkLabel(
            top, text="Model Details",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=self.TEXT,
        )
        self._title_label.pack(side="left", padx=16)

        # Header card (family, params, quantization)
        self._header_card = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12)
        self._header_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))

        # Tabview
        self._tabview = ctk.CTkTabview(
            self, fg_color=self.CARD_BG, corner_radius=12,
            segmented_button_fg_color="#334155",
            segmented_button_selected_color=self.BLUE,
            segmented_button_unselected_color="#334155",
        )
        self._tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self._tabview.add("Info")
        self._tabview.add("Modelfile")
        self._tabview.add("License")

    def load_model(self, name: str) -> None:
        """Fetch and display details for the given model name."""
        self._model_name = name
        self._title_label.configure(text=name)

        # Show loading state
        self._clear_header()
        ctk.CTkLabel(
            self._header_card, text="Loading...",
            font=ctk.CTkFont(size=13), text_color=self.TEXT_DIM,
        ).pack(padx=16, pady=12)

        def _fetch():
            return self._manager.get_model_details(name)

        def _on_done(details):
            self.after(0, lambda: self._populate(details))

        def _on_error(exc):
            self.after(0, lambda: self._show_error(str(exc)))

        run_in_thread(_fetch, on_success=_on_done, on_error=_on_error)

    def _clear_header(self) -> None:
        for w in self._header_card.winfo_children():
            w.destroy()

    def _populate(self, details: ModelDetails) -> None:
        self._details = details

        # Header
        self._clear_header()
        row = ctk.CTkFrame(self._header_card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)

        badges = [
            ("Family", details.family),
            ("Parameters", details.parameter_size),
            ("Quantization", details.quantization),
            ("Format", details.format),
        ]
        for label, value in badges:
            if not value or value == "?":
                continue
            f = ctk.CTkFrame(row, fg_color="#334155", corner_radius=6)
            f.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                f, text=f"{label}: {value}",
                font=ctk.CTkFont(size=12), text_color=self.TEXT,
            ).pack(padx=10, pady=4)

        # Copy button
        ctk.CTkButton(
            row, text="📋 Copy Model", width=120, height=30,
            corner_radius=6, font=ctk.CTkFont(size=12),
            fg_color="#334155", hover_color=self.BLUE,
            command=self._copy_model,
        ).pack(side="right")

        # Info tab
        info_tab = self._tabview.tab("Info")
        for w in info_tab.winfo_children():
            w.destroy()

        if details.system_prompt:
            self._add_section(info_tab, "System Prompt", details.system_prompt)
        if details.template:
            self._add_section(info_tab, "Template", details.template)

        # Modelfile tab
        mf_tab = self._tabview.tab("Modelfile")
        for w in mf_tab.winfo_children():
            w.destroy()
        mf_text = ctk.CTkTextbox(
            mf_tab, fg_color="#0f0f0f", text_color=self.TEXT,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
        )
        mf_text.pack(fill="both", expand=True, padx=8, pady=8)
        mf_text.insert("1.0", details.modelfile or "(empty)")
        mf_text.configure(state="disabled")

        # License tab
        lic_tab = self._tabview.tab("License")
        for w in lic_tab.winfo_children():
            w.destroy()
        lic_text = ctk.CTkTextbox(
            lic_tab, fg_color="#0f0f0f", text_color=self.TEXT,
            font=ctk.CTkFont(size=12), wrap="word",
        )
        lic_text.pack(fill="both", expand=True, padx=8, pady=8)
        lic_text.insert("1.0", details.license or "(no license info)")
        lic_text.configure(state="disabled")

    def _add_section(self, parent, title: str, content: str) -> None:
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.TEXT,
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(12, 4))
        box = ctk.CTkTextbox(
            parent, height=120, fg_color="#0f0f0f", text_color=self.TEXT_DIM,
            font=ctk.CTkFont(family="Consolas", size=12), wrap="word",
        )
        box.pack(fill="x", padx=12, pady=(0, 8))
        box.insert("1.0", content)
        box.configure(state="disabled")

    def _copy_model(self) -> None:
        if not self._model_name:
            return
        dialog = ctk.CTkInputDialog(
            text=f"New name for copy of '{self._model_name}':",
            title="Copy Model",
        )
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            def _copy():
                self._manager.copy_model(self._model_name, new_name.strip())
            run_in_thread(_copy)

    def _show_error(self, msg: str) -> None:
        self._clear_header()
        ctk.CTkLabel(
            self._header_card, text=f"Error: {msg}",
            font=ctk.CTkFont(size=13), text_color="#f87171",
        ).pack(padx=16, pady=12)
