"""Settings view — configuration panel for server URL, theme, and refresh interval."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ollama_gui.utils import config

if TYPE_CHECKING:
    from ollama_gui.app import OllamaGUI


class SettingsView(ctk.CTkFrame):
    """Configuration panel persisted to ~/.ollama_gui/config.json."""

    BG = "#0f0f0f"
    CARD_BG = "#1a1a2e"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    BLUE = "#60a5fa"
    GREEN = "#4ade80"

    def __init__(self, master, app: "OllamaGUI", **kwargs) -> None:
        super().__init__(master, fg_color=self.BG, **kwargs)
        self._app = app
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.TEXT,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 16))

        # --- Server URL ---
        card1 = self._card(row=1)
        ctk.CTkLabel(
            card1, text="Ollama Server URL",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(
            card1, text="The base URL where Ollama is running",
            font=ctk.CTkFont(size=11), text_color=self.TEXT_DIM,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._url_var = ctk.StringVar(value=config.get("server_url"))
        ctk.CTkEntry(
            card1, textvariable=self._url_var,
            width=400, height=36, corner_radius=8,
            fg_color="#0f0f0f", border_color="#334155",
            text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(0, 16))

        # --- Appearance ---
        card2 = self._card(row=2)
        ctk.CTkLabel(
            card2, text="Appearance",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        theme_frame = ctk.CTkFrame(card2, fg_color="transparent")
        theme_frame.pack(anchor="w", padx=16, pady=(0, 16))

        self._theme_var = ctk.StringVar(value=config.get("theme"))
        for label in ["dark", "light", "system"]:
            ctk.CTkRadioButton(
                theme_frame, text=label.capitalize(),
                variable=self._theme_var, value=label,
                font=ctk.CTkFont(size=13), text_color=self.TEXT,
                fg_color=self.BLUE, hover_color="#3b82f6",
                border_color="#334155",
            ).pack(side="left", padx=(0, 16))

        # --- Refresh Interval ---
        card3 = self._card(row=3)
        ctk.CTkLabel(
            card3, text="Status Refresh Interval",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        slider_frame = ctk.CTkFrame(card3, fg_color="transparent")
        slider_frame.pack(fill="x", padx=16, pady=(0, 16))

        self._interval_label = ctk.CTkLabel(
            slider_frame, text=f"{config.get('refresh_interval')}s",
            font=ctk.CTkFont(size=13), text_color=self.TEXT, width=40,
        )
        self._interval_label.pack(side="right", padx=(8, 0))

        self._interval_slider = ctk.CTkSlider(
            slider_frame, from_=1, to=30,
            number_of_steps=29,
            progress_color=self.BLUE,
            button_color=self.BLUE,
            button_hover_color="#3b82f6",
            fg_color="#334155",
            command=self._on_slider,
        )
        self._interval_slider.set(config.get("refresh_interval"))
        self._interval_slider.pack(fill="x", expand=True)

        # --- Connection Timeout ---
        card4 = self._card(row=4)
        ctk.CTkLabel(
            card4, text="Connection Timeout",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.TEXT,
        ).pack(anchor="w", padx=16, pady=(16, 4))

        self._timeout_var = ctk.StringVar(value=str(config.get("connect_timeout")))
        timeout_frame = ctk.CTkFrame(card4, fg_color="transparent")
        timeout_frame.pack(anchor="w", padx=16, pady=(0, 16))
        ctk.CTkEntry(
            timeout_frame, textvariable=self._timeout_var,
            width=80, height=36, corner_radius=8,
            fg_color="#0f0f0f", border_color="#334155",
            text_color=self.TEXT,
        ).pack(side="left")
        ctk.CTkLabel(
            timeout_frame, text="seconds",
            font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
        ).pack(side="left", padx=8)

        # --- Save button ---
        self._save_msg = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color=self.GREEN,
        )
        self._save_msg.grid(row=6, column=0, sticky="w", padx=24)

        ctk.CTkButton(
            self, text="💾  Save Settings", width=160, height=40,
            corner_radius=8, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.BLUE, hover_color="#3b82f6",
            command=self._save,
        ).grid(row=5, column=0, sticky="w", padx=24, pady=(16, 4))

    def _card(self, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12)
        card.grid(row=row, column=0, sticky="ew", padx=24, pady=4)
        return card

    def _on_slider(self, value: float) -> None:
        self._interval_label.configure(text=f"{int(value)}s")

    def _save(self) -> None:
        try:
            timeout = int(self._timeout_var.get())
        except ValueError:
            timeout = 5

        updates = {
            "server_url": self._url_var.get().strip(),
            "theme": self._theme_var.get(),
            "refresh_interval": int(self._interval_slider.get()),
            "connect_timeout": timeout,
        }
        config.save(updates)

        # Apply theme
        ctk.set_appearance_mode(updates["theme"])

        # Update monitor interval
        self._app.monitor.set_interval(updates["refresh_interval"])

        # Recreate client with new URL
        self._app.update_server_url(updates["server_url"])

        self._save_msg.configure(text="✅ Settings saved!")
        self.after(3000, lambda: self._save_msg.configure(text=""))
