import asyncio
import logging
import sys
from pathlib import Path

from rich.logging import RichHandler

from src.config import load_config
from src.trainer import Trainer
from src.gui import launch_gui

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)
log = logging.getLogger("Destiny2Trainer")


async def main() -> None:
    log.info("Starting Destiny 2 Ultimate Trainer 2026...")
    config = load_config()
    trainer = Trainer(config)
    # Launch GUI (blocking on main thread, we can run it with asyncio if needed)
    # For simplicity, we launch the GUI which will manage the trainer.
    # We'll start the web dashboard in a background task.
    dashboard_task = None
    try:
        from src.web_dashboard import WebDashboard
        dashboard = WebDashboard(trainer)
        dashboard_task = asyncio.create_task(dashboard.start())
    except ImportError:
        log.warning("Web dashboard module not found, skipping.")

    # GUI runs on the main thread (customtkinter requires main thread)
    # We'll launch it inside a helper.
    def run_gui():
        launch_gui(trainer)

    # Use a thread for the GUI to keep the asyncio loop running
    import threading
    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()

    # Wait for the trainer loop to run (or just block on GUI)
    try:
        while gui_thread.is_alive():
            await asyncio.sleep(0.5)
    except KeyboardInterrupt:
        log.info("Shutting down...")

    if dashboard_task:
        dashboard_task.cancel()
    log.info("Trainer shut down gracefully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        log.exception(f"Fatal error: {e}")
        sys.exit(1)
