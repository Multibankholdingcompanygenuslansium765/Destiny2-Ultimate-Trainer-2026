from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Dict, Set

import keyboard
import discordrpc
from rich.logging import RichHandler

from src.config import Config
from src.memory import MemoryManager
from src.offsets import offsets

log = logging.getLogger("Destiny2Trainer.Trainer")

class Trainer:
    """Core trainer class managing cheats, hotkeys, and Discord Rich Presence."""

    def __init__(self, config: Config):
        self.config = config
        self.memory = MemoryManager(config.process_name)
        self.running = False
        self.features: Dict[str, bool] = {
            "god_mode": False,
            "unlimited_ammo": False,
            "esp": False,
            "speed_hack": False,
            "no_recoil": False,
            "loot_unlocker": False,
            "bounty_complete": False,
            "aimbot": False,
        }
        self.lock = asyncio.Lock()
        self.discord_rpc = None
        if config.discord_rich_presence:
            self._init_discord_rpc()

    def _init_discord_rpc(self):
        try:
            discordrpc.initialize('123456789012345678')  # Your application ID
            self.discord_rpc = True
        except:
            log.warning("Discord RPC initialization failed")

    async def start(self) -> None:
        """Start the main trainer loop."""
        self.running = True
        log.info("Trainer loop started")
        # Register global hotkeys
        keyboard.add_hotkey(self.config.hotkey_toggle, self.toggle_cheats)
        keyboard.add_hotkey(self.config.hotkey_exit, self.stop)
        # Background task that writes cheats continuously
        asyncio.create_task(self._cheat_loop())

    async def _cheat_loop(self) -> None:
        while self.running:
            await asyncio.sleep(0.05)  # High frequency
            if not self.memory.pm:
                continue
            async with self.lock:
                if self.features["god_mode"]:
                    await self.memory.write_pointer(
                        offsets.PLAYER_BASE, offsets.PLAYER_OFFSETS, 1, "int32"
                    )
                if self.features["unlimited_ammo"]:
                    await self.memory.write_pointer(
                        offsets.UNLIMITED_AMMO, [], 1337, "int32"
                    )
                # Other features would be implemented similarly.
            # Update Discord Rich Presence
            if self.discord_rpc:
                self._update_rpc()

    def _update_rpc(self):
        active = [name for name, on in self.features.items() if on]
        try:
            discordrpc.update_presence(
                state=", ".join(active) if active else "Idle",
                details="Destiny 2 Ultimate Trainer",
                large_image="trainer_logo",
                large_text="v1.0.0",
            )
        except:
            pass

    async def toggle_feature(self, feature: str, value: bool) -> None:
        async with self.lock:
            if feature in self.features:
                self.features[feature] = value
                log.info(f"Feature '{feature}' set to {value}")

    def toggle_cheats(self) -> None:
        # Global hotkey: toggle all active?
        log.info("Global hotkey pressed, toggling God Mode as example")
        asyncio.create_task(self.toggle_feature("god_mode", not self.features["god_mode"]))

    def stop(self) -> None:
        self.running = False
        log.info("Trainer stopped")
        if self.discord_rpc:
            try:
                discordrpc.shutdown()
            except:
                pass
        keyboard.unhook_all()
