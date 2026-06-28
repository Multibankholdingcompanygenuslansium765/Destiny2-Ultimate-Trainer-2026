from __future__ import annotations

import asyncio
import threading
import logging
from typing import Dict

import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as Item

from src.trainer import Trainer

log = logging.getLogger("Destiny2Trainer.GUI")

class TrainerGUI(ctk.CTk):
    def __init__(self, trainer: Trainer):
        super().__init__()
        self.trainer = trainer
        self.title("Destiny 2 Ultimate Trainer 2026")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#1a1a2e")

        # Variables
        self.feature_vars: Dict[str, ctk.BooleanVar] = {}
        self.status_text = ctk.StringVar(value="Not attached")

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self._update_status)

    def create_widgets(self):
        # Title
        title = ctk.CTkLabel(self, text="Destiny 2 Ultimate Trainer", font=("Segoe UI", 24, "bold"))
        title.pack(pady=20)

        # Status bar
        status_frame = ctk.CTkFrame(self, fg_color="#16213e")
        status_frame.pack(fill="x", padx=10, pady=5)
        status_label = ctk.CTkLabel(status_frame, textvariable=self.status_text, text_color="white")
        status_label.pack(side="left", padx=10)

        # Attach button
        self.attach_btn = ctk.CTkButton(status_frame, text="Attach", command=self.attach_process)
        self.attach_btn.pack(side="right", padx=10)

        # Feature cards (styled switches)
        features_frame = ctk.CTkScrollableFrame(self, fg_color="#0f3460")
        features_frame.pack(fill="both", expand=True, padx=10, pady=10)

        feature_names = ["god_mode", "unlimited_ammo", "esp", "speed_hack", "no_recoil",
                         "loot_unlocker", "bounty_complete", "aimbot"]
        for name in feature_names:
            var = ctk.BooleanVar(value=False)
            self.feature_vars[name] = var
            frame = ctk.CTkFrame(features_frame, fg_color="#1a1a2e")
            frame.pack(fill="x", padx=5, pady=5)
            label = ctk.CTkLabel(frame, text=name.replace("_", " ").title(), font=("Segoe UI", 16))
            label.pack(side="left", padx=10)
            switch = ctk.CTkSwitch(frame, variable=var, command=lambda n=name: self.toggle_feature(n))
            switch.pack(side="right", padx=10)

        # Console log area
        self.console = ctk.CTkTextbox(self, height=100, fg_color="#0f3460", text_color="white")
        self.console.pack(fill="x", padx=10, pady=10)
        self.console.insert("end", "Trainer ready.\n")

    def attach_process(self):
        asyncio.run_coroutine_threadsafe(self._attach(), asyncio.get_event_loop())

    async def _attach(self):
        success = await self.trainer.memory.attach()
        if success:
            self.status_text.set("Attached to destiny2.exe")
            self.attach_btn.configure(state="disabled")
            await self.trainer.start()
        else:
            self.status_text.set("Attach failed")

    def toggle_feature(self, feature: str):
        value = self.feature_vars[feature].get()
        asyncio.run_coroutine_threadsafe(
            self.trainer.toggle_feature(feature, value),
            asyncio.get_event_loop()
        )
        self.log_to_console(f"Feature {feature} set to {value}")

    def log_to_console(self, message: str):
        self.console.insert("end", message + "\n")
        self.console.see("end")

    def _update_status(self):
        if self.trainer.memory.pm:
            self.status_text.set("Attached - Active")
        else:
            self.status_text.set("Not attached")
        self.after(1000, self._update_status)

    def on_close(self):
        self.trainer.stop()
        self.withdraw()  # Hide window, we'll just destroy
        self.quit()

def create_tray_icon(gui: TrainerGUI):
    # Create a simple icon
    image = Image.new('RGB', (64, 64), color=(233, 69, 96))
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill=(255,255,255))
    menu = pystray.Menu(
        Item('Show', lambda: gui.deiconify()),
        Item('Exit', lambda: gui.quit()),
    )
    icon = pystray.Icon("trainer", image, "Destiny 2 Trainer", menu)
    return icon

def launch_gui(trainer: Trainer):
    app = TrainerGUI(trainer)
    tray_icon = create_tray_icon(app)
    threading.Thread(target=tray_icon.run, daemon=True).start()
    app.mainloop()
