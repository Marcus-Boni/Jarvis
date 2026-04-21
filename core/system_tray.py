"""Windows system tray icon for Jarvis."""

from __future__ import annotations

import asyncio
import importlib
import os
import signal
import threading
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import AppSettings
from core.runtime_events import RuntimeEventBroker
from llm.memory.chroma_store import ChromaMemoryStore
from skills.browser.windows_browser import open_url_in_default_browser


class JarvisTrayIcon:
    """Run a Windows system tray icon with quick Jarvis actions."""

    def __init__(
        self,
        settings: AppSettings,
        event_broker: RuntimeEventBroker,
        memory_store: ChromaMemoryStore,
    ) -> None:
        self._settings = settings
        self._event_broker = event_broker
        self._memory_store = memory_store
        self._logger = logger.bind(component="tray")
        self._icon: Any | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start_in_thread(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the tray icon in a background thread."""

        self._loop = loop
        thread = threading.Thread(target=self._run_tray, daemon=True, name="jarvis-tray")
        thread.start()

    def _run_tray(self) -> None:
        try:
            pystray = importlib.import_module("pystray")

            menu = pystray.Menu(
                pystray.MenuItem("Jarvis online", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Dashboard", lambda icon, item: self._open_dashboard()),
                pystray.MenuItem("Clear Memory", lambda icon, item: self._schedule_clear_memory()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", lambda icon, item: self._quit_jarvis(icon)),
            )
            self._icon = pystray.Icon(
                name="jarvis",
                icon=self._create_icon_image(),
                title=self._settings.jarvis.name,
                menu=menu,
            )
            self._icon.run()
        except Exception as exc:  # pragma: no cover
            self._logger.warning("tray_icon_failed error={}", exc)

    def _create_icon_image(self) -> Any:
        pil_image = importlib.import_module("PIL.Image")
        pil_image_draw = importlib.import_module("PIL.ImageDraw")

        icon_path = Path("assets/jarvis-icon.png")
        if icon_path.exists():
            return pil_image.open(icon_path).resize((64, 64))

        size = 64
        image = pil_image.new("RGBA", (size, size), color=(0, 0, 0, 0))
        draw = pil_image_draw.Draw(image)
        draw.ellipse([2, 2, size - 2, size - 2], fill=(15, 140, 132))
        draw.rectangle([28, 16, 36, 44], fill="white")
        draw.ellipse([20, 40, 36, 52], fill="white")
        return image

    def _open_dashboard(self) -> None:
        open_url_in_default_browser(self._settings.dashboard.origin)

    def _schedule_clear_memory(self) -> None:
        if self._loop is None:
            return
        self._memory_store.clear_all()
        asyncio.run_coroutine_threadsafe(
            self._event_broker.publish("command", {"action": "clear_memory"}),
            self._loop,
        )

    def _quit_jarvis(self, icon: Any) -> None:
        self._logger.info("tray_quit_requested")
        icon.stop()
        if self._loop is not None:
            asyncio.run_coroutine_threadsafe(
                self._event_broker.publish("command", {"action": "quit"}),
                self._loop,
            )
        os.kill(os.getpid(), signal.SIGTERM)

    def stop(self) -> None:
        """Stop the tray icon if it is running."""

        if self._icon is None:
            return
        self._icon.stop()
