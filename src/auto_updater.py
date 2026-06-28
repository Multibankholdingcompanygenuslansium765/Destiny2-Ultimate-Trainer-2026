from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import aiohttp

from src.offsets import offsets as current_offsets

log = logging.getLogger("Destiny2Trainer.Updater")
UPDATE_URL = "https://api.skydock.netlify.app/updates/destiny2-trainer.json"

async def check_for_updates() -> bool:
    """Check for new offset definitions and update offsets.py if newer."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(UPDATE_URL) as resp:
                if resp.status != 200:
                    log.warning(f"Update check failed with status {resp.status}")
                    return False
                data = await resp.json()
                latest_version = data.get("version")
                current_version = "2026.06.09"  # Hardcoded for now
                if latest_version and latest_version != current_version:
                    # Download new offsets file
                    offsets_url = data.get("offsets_url")
                    if offsets_url:
                        async with session.get(offsets_url) as off_resp:
                            if off_resp.status == 200:
                                content = await off_resp.text()
                                (Path(__file__).parent / "offsets.py").write_text(content)
                                log.info(f"Updated offsets to version {latest_version}")
                                return True
    except Exception as e:
        log.error(f"Update check failed: {e}")
    return False
