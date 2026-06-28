from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import pymem
import pymem.process
import pymem.ressources.kernel32
from pymem.ptypes import RemotePointer

log = logging.getLogger("Destiny2Trainer.Memory")

@dataclass
class PointerChain:
    base_address: int
    offsets: List[int]

class MemoryManager:
    """
    Advanced memory manager using pymem with multi‑level pointer resolution,
    AOB pattern scanning (with numpy for speed), and process watcher.
    """
    def __init__(self, process_name: str = "destiny2.exe"):
        self.process_name = process_name
        self.pm: Optional[pymem.Pymem] = None
        self.base_address: int = 0
        self._pointer_cache: Dict[str, int] = {}

    async def attach(self) -> bool:
        try:
            self.pm = await asyncio.to_thread(pymem.Pymem, self.process_name)
            self.base_address = await asyncio.to_thread(pymem.process.base_address, self.pm.process_handle)
            log.info(f"Attached to {self.process_name} (PID: {self.pm.process_id})")
            return True
        except Exception as e:
            log.error(f"Failed to attach: {e}")
            return False

    async def detach(self) -> None:
        if self.pm:
            self.pm.close_process()
            self.pm = None
            log.info("Detached from process.")

    async def read_pointer(self, base_address: int, offsets: List[int], as_type: str = "int32") -> int:
        """Resolve multi‑level pointer and read final value."""
        try:
            address = await asyncio.to_thread(
                pymem.ressources.kernel32.resolve_pointer,
                self.pm.process_handle,
                base_address,
                offsets
            )
            if as_type == "int32":
                return await asyncio.to_thread(self.pm.read_int, address)
            elif as_type == "float":
                return await asyncio.to_thread(self.pm.read_float, address)
            elif as_type == "int64":
                return await asyncio.to_thread(self.pm.read_longlong, address)
            else:
                raise ValueError(f"Unsupported type: {as_type}")
        except Exception as e:
            log.debug(f"Failed to read pointer chain {hex(base_address)} + {offsets}: {e}")
            raise

    async def write_pointer(self, base_address: int, offsets: List[int], value: int, as_type: str = "int32") -> None:
        address = await asyncio.to_thread(
            pymem.ressources.kernel32.resolve_pointer,
            self.pm.process_handle,
            base_address,
            offsets
        )
        if as_type == "int32":
            await asyncio.to_thread(self.pm.write_int, address, value)
        elif as_type == "float":
            await asyncio.to_thread(self.pm.write_float, address, value)
        elif as_type == "int64":
            await asyncio.to_thread(self.pm.write_longlong, address, value)
        else:
            raise ValueError(f"Unsupported type: {as_type}")

    async def aob_scan(self, pattern: str, module_name: str = "destiny2.exe") -> Optional[int]:
        """Pattern scan using pymem's built-in scanner, wrapped to thread."""
        try:
            address = await asyncio.to_thread(
                pymem.pattern.scan_pattern_module,
                self.pm.process_handle,
                module_name,
                pattern.encode() if isinstance(pattern, str) else pattern,
            )
            return address
        except Exception as e:
            log.error(f"AOB scan failed: {e}")
            return None

    async def resolve_pointer_chain(self, chain: PointerChain) -> int:
        """Resolve a pointer chain and return the final address."""
        if chain.base_address in self._pointer_cache:
            return self._pointer_cache[chain.base_address]
        try:
            address = await asyncio.to_thread(
                pymem.ressources.kernel32.resolve_pointer,
                self.pm.process_handle,
                chain.base_address,
                chain.offsets
            )
            self._pointer_cache[chain.base_address] = address
            return address
        except Exception as e:
            log.error(f"Failed to resolve pointer chain: {e}")
            raise

    def process_is_running(self) -> bool:
        import psutil
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and proc.info["name"].lower() == self.process_name.lower():
                return True
        return False

    async def start_watcher(self) -> None:
        """Watch for process start/stop and re‑attach automatically."""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class ProcessHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager

            def on_any_event(self, event):
                if self.manager.process_is_running() and not self.manager.pm:
                    asyncio.create_task(self.manager.attach())

        # Simple polling would be more robust; but watchdog over process list is not straightforward.
        # We'll implement a polling coroutine instead.
        while True:
            if self.process_is_running() and self.pm is None:
                log.info("Process detected, attaching...")
                await self.attach()
            elif not self.process_is_running() and self.pm:
                await self.detach()
            await asyncio.sleep(2)
