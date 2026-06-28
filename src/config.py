from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Config(BaseModel):
    theme: str = "dark"
    hotkey_toggle: str = "F1"
    hotkey_exit: str = "F2"
    hotkey_gui: str = "INSERT"
    discord_rich_presence: bool = True
    auto_attach: bool = False
    process_name: str = "destiny2.exe"
    log_level: str = "INFO"


CONFIG_DIR = Path.home() / "Documents" / "Destiny2Trainer"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> Config:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return Config(**data)
        except Exception:
            # Fallback to default
            pass
    # Create default config and save
    config = Config()
    save_config(config)
    return config


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(config.model_dump_json(indent=2), encoding="utf-8")
