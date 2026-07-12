"""Ollama GUI — main application shell and entry point."""

from __future__ import annotations

import customtkinter as ctk

from ollama_gui.models.data_models import ServerStatus
from ollama_gui.services.ollama_client import OllamaClient
from ollama_gui.services.model_manager import ModelManager
from ollama_gui.services.status_monitor import StatusMonitor
from ollama_gui.utils import config
from ollama_gui.views.components.sidebar import Sidebar
from ollama_gui.views.components.status_badge import StatusBadge
from ollama_gui.views.dashboard_view import DashboardView
from ollama_gui.views.models_view import ModelsView
from ollama_gui.views.model_detail_view import ModelDetailView
from ollama_gui.views.running_view import RunningView
from ollama_gui.views.chat_view import ChatView
from ollama_gui.views.settings_view import SettingsView


class OllamaGUI(ctk.CTk):
    """Main application window — sidebar + swappable content area + status bar."""

    BG = "#0f0f0f"
    STATUS_BG = "#1a1a2e"
    TEXT_DIM = "#94a3b8"

    def __init__(self) -> None:
        super().__init__()

        # Load config
        cfg = config.load()

        # Window setup
        self.title("Ollama GUI")
        self.geometry(f"{cfg['window_width']}x{cfg['window_height']}")
        self.minsize(900, 600)
        self.configure(fg_color=self.BG)
        ctk.set_appearance_mode(cfg.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        # Services
        self.client = OllamaClient(cfg["server_url"])
        self.model_manager = ModelManager(self.client)
        self.monitor = StatusMonitor(
            client=self.client,
            on_status=self._on_status_update,
            interval=cfg["refresh_interval"],
        )

        # Layout: sidebar (fixed) | content (flexible) stacked above status bar
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._sidebar = Sidebar(self, on_navigate=self.navigate)
        self._sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")

        # Content area
        self._content = ctk.CTkFrame(self, fg_color=self.BG, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # Status bar
        self._status_bar = ctk.CTkFrame(self, height=32, fg_color=self.STATUS_BG, corner_radius=0)
        self._status_bar.grid(row=1, column=1, sticky="ew")
        self._status_bar.grid_propagate(False)

        self._status_badge = StatusBadge(self._status_bar)
        self._status_badge.pack(side="left", padx=12)

        self._status_info = ctk.CTkLabel(
            self._status_bar, text="",
            font=ctk.CTkFont(size=11), text_color=self.TEXT_DIM,
        )
        self._status_info.pack(side="right", padx=12)

        # Build all views (lazy creation, pre-built for instant switching)
        self._views: dict[str, ctk.CTkFrame] = {}
        self._views["Dashboard"] = DashboardView(self._content, app=self)
        self._views["Models"] = ModelsView(self._content, app=self)
        self._views["ModelDetail"] = ModelDetailView(self._content, app=self)
        self._views["Running"] = RunningView(self._content, app=self)
        self._views["Chat"] = ChatView(self._content, app=self)
        self._views["Settings"] = SettingsView(self._content, app=self)

        self._current_view: str = ""

        # Show dashboard
        self.navigate("Dashboard")

        # Start monitoring
        self.monitor.start()

        # Cleanup on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate(self, view_name: str) -> None:
        """Switch the content area to *view_name*."""
        if view_name == self._current_view:
            return

        # Hide current
        if self._current_view and self._current_view in self._views:
            self._views[self._current_view].grid_forget()

        # Show new
        target = view_name
        if target in self._views:
            self._views[target].grid(row=0, column=0, sticky="nsew")
            self._current_view = target

            # Trigger data refresh on navigation
            if target == "Models":
                self._views["Models"].refresh()
            elif target == "Chat":
                self._views["Chat"].refresh_models()

        # Update sidebar highlight (only for main nav items, not ModelDetail)
        if view_name in ("Dashboard", "Models", "Running", "Chat", "Settings"):
            self._sidebar._set_active(view_name)

    def show_model_detail(self, name: str) -> None:
        """Navigate to the model detail view for a specific model."""
        self.navigate("ModelDetail")
        self._views["ModelDetail"].load_model(name)

    # ------------------------------------------------------------------
    # Status updates
    # ------------------------------------------------------------------

    def _on_status_update(self, status: ServerStatus) -> None:
        """Called from StatusMonitor thread — marshal to main thread."""
        self.after(0, lambda: self._apply_status(status))

    def _apply_status(self, status: ServerStatus) -> None:
        """Update all views with the latest status."""
        # Status bar
        if status.is_online:
            self._status_badge.set_status("online", "Online")
            ver = status.version or ""
            info = f"v{ver}  ·  {status.model_count} models  ·  {status.running_count} running  ·  {status.total_disk_usage}"
            self._status_info.configure(text=info)
        else:
            self._status_badge.set_status("offline", "Offline")
            self._status_info.configure(text="Ollama server not reachable")

        # Dashboard
        if "Dashboard" in self._views:
            self._views["Dashboard"].update_status(status)

        # Running view
        if "Running" in self._views:
            self._views["Running"].update_status(status)

    def refresh_status(self) -> None:
        """Force an immediate status refresh."""
        self.monitor.force_refresh()

    # ------------------------------------------------------------------
    # Settings callbacks
    # ------------------------------------------------------------------

    def update_server_url(self, url: str) -> None:
        """Recreate the client and manager when the server URL changes."""
        self.client = OllamaClient(url)
        self.model_manager = ModelManager(self.client)
        self.monitor.stop()
        self.monitor = StatusMonitor(
            client=self.client,
            on_status=self._on_status_update,
            interval=config.get("refresh_interval"),
        )
        self.monitor.start()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """Clean shutdown."""
        self.monitor.stop()
        self.destroy()


def main() -> None:
    """Entry point."""
    app = OllamaGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
