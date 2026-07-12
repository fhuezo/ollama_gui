"""Chat view — developer-oriented model testing interface."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from ollama_gui.services.model_manager import ModelManager
from ollama_gui.utils.threading_utils import run_in_thread

if TYPE_CHECKING:
    from ollama_gui.app import OllamaGUI


class ChatView(ctk.CTkFrame):
    """Lightweight chat panel for testing model coding ability before using in VSCode."""

    BG = "#0f0f0f"
    CARD_BG = "#1a1a2e"
    TEXT = "#f1f5f9"
    TEXT_DIM = "#94a3b8"
    USER_BG = "#16213e"
    ASSISTANT_BG = "#0f0f0f"
    BLUE = "#60a5fa"
    GREEN = "#4ade80"

    def __init__(self, master, app: "OllamaGUI", **kwargs) -> None:
        super().__init__(master, fg_color=self.BG, **kwargs)
        self._app = app
        self._manager: ModelManager = app.model_manager
        self._generating = False
        self._models_list: list[str] = []
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # chat area expands

        # Top bar: model selector + system prompt toggle
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="💬 Chat",
            font=ctk.CTkFont(size=24, weight="bold"), text_color=self.TEXT,
        ).grid(row=0, column=0, sticky="w")

        # Model selector
        self._model_var = ctk.StringVar(value="Select a model...")
        self._model_dropdown = ctk.CTkOptionMenu(
            top, variable=self._model_var,
            values=["Loading..."],
            width=250, height=36, corner_radius=8,
            fg_color="#1a1a2e", button_color="#334155",
            button_hover_color="#475569",
            text_color=self.TEXT,
            font=ctk.CTkFont(size=13),
        )
        self._model_dropdown.grid(row=0, column=1, padx=16, sticky="w")

        # Clear + System prompt buttons
        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e")

        ctk.CTkButton(
            btn_frame, text="🗑 Clear", width=80, height=32,
            corner_radius=8, font=ctk.CTkFont(size=12),
            fg_color="#334155", hover_color="#475569",
            command=self._clear_chat,
        ).pack(side="left", padx=4)

        self._sys_toggle_btn = ctk.CTkButton(
            btn_frame, text="⚙ System Prompt", width=140, height=32,
            corner_radius=8, font=ctk.CTkFont(size=12),
            fg_color="#334155", hover_color="#475569",
            command=self._toggle_system_prompt,
        )
        self._sys_toggle_btn.pack(side="left", padx=4)

        self._params_toggle_btn = ctk.CTkButton(
            btn_frame, text="⚙ Model Settings", width=140, height=32,
            corner_radius=8, font=ctk.CTkFont(size=12),
            fg_color="#334155", hover_color="#475569",
            command=self._toggle_params,
        )
        self._params_toggle_btn.pack(side="left", padx=4)

        # System prompt (hidden by default)
        self._sys_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=8)
        self._sys_visible = False

        self._sys_entry = ctk.CTkTextbox(
            self._sys_frame, height=60,
            fg_color="#0f0f0f", text_color=self.TEXT,
            font=ctk.CTkFont(size=12), wrap="word",
            border_color="#334155", border_width=1,
        )
        self._sys_entry.pack(fill="x", padx=12, pady=12)
        self._sys_entry.insert("1.0", "You are a senior software developer. Write clean, well-documented code.")

        # Model settings parameters (hidden by default)
        self._params_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=8)
        self._params_visible = False
        
        self._params_frame.grid_columnconfigure(0, weight=1)
        self._params_frame.grid_columnconfigure(1, weight=1)
        self._params_frame.grid_columnconfigure(2, weight=1)
        
        # 1. num_ctx
        ctx_frame = ctk.CTkFrame(self._params_frame, fg_color="transparent")
        ctx_frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        ctk.CTkLabel(ctx_frame, text="Context Window (num_ctx)", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.TEXT).pack(anchor="w")
        self._ctx_var = ctk.StringVar(value="Default")
        self._ctx_menu = ctk.CTkOptionMenu(ctx_frame, variable=self._ctx_var, values=["Default", "1024", "2048", "4096", "8192"], width=130, height=28, fg_color="#0f0f0f", button_color="#334155", font=ctk.CTkFont(size=12))
        self._ctx_menu.pack(anchor="w", pady=(4, 0))
        
        # 2. temperature
        temp_frame = ctk.CTkFrame(self._params_frame, fg_color="transparent")
        temp_frame.grid(row=0, column=1, padx=12, pady=12, sticky="nsew")
        temp_title_frame = ctk.CTkFrame(temp_frame, fg_color="transparent")
        temp_title_frame.pack(fill="x")
        ctk.CTkLabel(temp_title_frame, text="Temperature", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.TEXT).pack(side="left")
        self._temp_lbl = ctk.CTkLabel(temp_title_frame, text="0.8", font=ctk.CTkFont(size=11), text_color=self.BLUE)
        self._temp_lbl.pack(side="right")
        
        self._temp_slider = ctk.CTkSlider(temp_frame, from_=0.0, to=2.0, number_of_steps=20, width=150, height=16, progress_color=self.BLUE, button_color=self.BLUE, fg_color="#334155", command=self._on_temp_slider)
        self._temp_slider.set(0.8)
        self._temp_slider.pack(anchor="w", pady=(6, 0))

        # 3. num_predict
        predict_frame = ctk.CTkFrame(self._params_frame, fg_color="transparent")
        predict_frame.grid(row=0, column=2, padx=12, pady=12, sticky="nsew")
        ctk.CTkLabel(predict_frame, text="Max Tokens (num_predict)", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.TEXT).pack(anchor="w")
        self._predict_var = ctk.StringVar(value="Default")
        self._predict_menu = ctk.CTkOptionMenu(predict_frame, variable=self._predict_var, values=["Default", "256", "512", "1024", "2048", "4096"], width=130, height=28, fg_color="#0f0f0f", button_color="#334155", font=ctk.CTkFont(size=12))
        self._predict_menu.pack(anchor="w", pady=(4, 0))

        # Chat history (scrollable)
        self._chat_area = ctk.CTkTextbox(
            self, fg_color=self.CARD_BG, corner_radius=12,
            text_color=self.TEXT,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word", state="disabled",
            border_color="#334155", border_width=1,
        )
        self._chat_area.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 8))

        # Configure tags for user/assistant messages
        self._chat_area.tag_config("user", foreground=self.BLUE)
        self._chat_area.tag_config("assistant", foreground=self.GREEN)
        self._chat_area.tag_config("dim", foreground=self.TEXT_DIM)

        # Input area
        input_frame = ctk.CTkFrame(self, fg_color=self.CARD_BG, corner_radius=12)
        input_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 24))
        input_frame.grid_columnconfigure(0, weight=1)

        self._input_box = ctk.CTkTextbox(
            input_frame, height=60,
            fg_color="#0f0f0f", text_color=self.TEXT,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word", border_width=0,
        )
        self._input_box.grid(row=0, column=0, sticky="ew", padx=(12, 0), pady=12)
        self._input_box.bind("<Shift-Return>", lambda e: None)  # allow newlines with Shift+Enter
        self._input_box.bind("<Return>", self._on_enter)

        self._send_btn = ctk.CTkButton(
            input_frame, text="Send ➤", width=80, height=40,
            corner_radius=8, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.BLUE, hover_color="#3b82f6",
            command=self._send_message,
        )
        self._send_btn.grid(row=0, column=1, padx=12, pady=12)

    def _on_enter(self, event) -> str:
        """Send on Enter (without Shift)."""
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"
        return ""

    def refresh_models(self) -> None:
        """Reload the model list for the dropdown."""
        def _fetch():
            return self._manager.refresh_models()

        def _on_done(models):
            names = [m.name for m in models]
            self.after(0, lambda: self._update_dropdown(names))

        run_in_thread(_fetch, on_success=_on_done)

    def _update_dropdown(self, names: list[str]) -> None:
        self._models_list = names
        if names:
            self._model_dropdown.configure(values=names)
            if self._model_var.get() in ("Select a model...", "Loading..."):
                self._model_var.set(names[0])
        else:
            self._model_dropdown.configure(values=["No models available"])
            self._model_var.set("No models available")

    def _toggle_system_prompt(self) -> None:
        if self._sys_visible:
            self._sys_frame.grid_forget()
            self._sys_visible = False
        else:
            if self._params_visible:
                self._toggle_params()
            self._sys_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
            self._sys_visible = True

    def _toggle_params(self) -> None:
        if self._params_visible:
            self._params_frame.grid_forget()
            self._params_visible = False
        else:
            if self._sys_visible:
                self._toggle_system_prompt()
            self._params_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
            self._params_visible = True

    def _on_temp_slider(self, val: float) -> None:
        self._temp_lbl.configure(text=f"{val:.1f}")

    def _clear_chat(self) -> None:
        self._chat_area.configure(state="normal")
        self._chat_area.delete("1.0", "end")
        self._chat_area.configure(state="disabled")

    def _append_text(self, text: str, tag: str = "") -> None:
        self._chat_area.configure(state="normal")
        if tag:
            self._chat_area.insert("end", text, tag)
        else:
            self._chat_area.insert("end", text)
        self._chat_area.see("end")
        self._chat_area.configure(state="disabled")

    def _send_message(self) -> None:
        if self._generating:
            return
        prompt = self._input_box.get("1.0", "end").strip()
        if not prompt:
            return
        model = self._model_var.get()
        if model in ("Select a model...", "Loading...", "No models available"):
            return

        # Clear input
        self._input_box.delete("1.0", "end")

        # Display user message
        self._append_text(f"\n{'─' * 60}\n", "dim")
        self._append_text("You:\n", "user")
        self._append_text(f"{prompt}\n\n")

        # Display assistant header
        self._append_text(f"{model}:\n", "assistant")

        # Get system prompt
        system = None
        if self._sys_visible:
            system = self._sys_entry.get("1.0", "end").strip()
            if not system:
                system = None

        # Get options parameters
        options = {}
        ctx_val = self._ctx_var.get()
        if ctx_val != "Default":
            options["num_ctx"] = int(ctx_val)
            
        predict_val = self._predict_var.get()
        if predict_val != "Default":
            options["num_predict"] = int(predict_val)
            
        options["temperature"] = float(self._temp_slider.get())

        self._generating = True
        self._send_btn.configure(state="disabled", text="...")

        def _generate():
            self._app.client.generate(
                model=model,
                prompt=prompt,
                system=system,
                options=options,
                callback=self._on_token,
            )

        def _on_done(_):
            self.after(0, self._generation_complete)

        def _on_error(exc):
            self.after(0, lambda: self._generation_error(str(exc)))

        run_in_thread(_generate, on_success=_on_done, on_error=_on_error)

    def _on_token(self, token: str, is_done: bool) -> None:
        """Called from worker thread for each streamed token."""
        self.after(0, lambda: self._append_text(token))

    def _generation_complete(self) -> None:
        self._generating = False
        self._send_btn.configure(state="normal", text="Send ➤")
        self._append_text("\n")

    def _generation_error(self, msg: str) -> None:
        self._generating = False
        self._send_btn.configure(state="normal", text="Send ➤")
        self._append_text(f"\n❌ Error: {msg}\n", "dim")
