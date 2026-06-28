from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Offsets:
    GOD_MODE: int = 0x02A4B3F0
    UNLIMITED_AMMO: int = 0x02A4B4A0
    ESP_ENABLED: int = 0x02A4B550
    SPEED_HACK: int = 0x02A4B600
    NO_RECOIL: int = 0x02A4B6B0
    LOOT_UNLOCKER: int = 0x02A4B760
    BOUNTY_COMPLETE: int = 0x02A4B810
    AIMBOT_FOV: int = 0x02A4B8C0

    # Pointer chains for complex structures
    PLAYER_BASE: int = 0x01E8A3C0
    PLAYER_OFFSETS: list = field(default_factory=lambda: [0x0, 0x30, 0x8, 0x20])

    # Version map (future proof)
    VERSION_OFFSETS: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        "2026.06.09": {
            "GOD_MODE": 0x02A4B3F0,
            "UNLIMITED_AMMO": 0x02A4B4A0,
        }
    })

    def get_for_version(self, version: str) -> Dict[str, int]:
        return self.VERSION_OFFSETS.get(version, {})


# Singleton instance
offsets = Offsets()
