"""Screenshot capture skill using mss and Win32 fallbacks."""

from __future__ import annotations

import asyncio
import ctypes
import importlib
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from core.models import Intent, RequestContext, SkillResult
from skills.base_skill import BaseSkill

SCREENSHOTS_DIR = Path("data/screenshots")


class ScreenshotSkill(BaseSkill):
    """Capture screenshots of the full screen or active window."""

    name: ClassVar[str] = "screenshot"
    description: ClassVar[str] = "Captura prints da tela completa ou janela ativa."
    triggers: ClassVar[list[str]] = [
        "screenshot",
        "print da tela",
        "captura de tela",
        "tire um print",
        "capture a tela",
    ]

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if any(
            token in lowered_text
            for token in ["screenshot", "print", "captura", "capture a tela", "tire uma foto"]
        ):
            return 0.9
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del context
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lowered_text = intent.raw_text.lower()
        try:
            if "janela" in lowered_text or "window" in lowered_text:
                path = await asyncio.to_thread(self._capture_active_window, timestamp)
                mode = "active window"
            else:
                path = await asyncio.to_thread(self._capture_fullscreen, timestamp)
                mode = "full screen"

            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"Screenshot ({mode}) salvo em {path.name}.",
                data={"path": str(path), "mode": mode},
            )
        except Exception as exc:  # pragma: no cover
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Erro ao capturar tela: {exc}",
            )

    def _capture_fullscreen(self, timestamp: str) -> Path:
        mss = importlib.import_module("mss")
        mss_tools = importlib.import_module("mss.tools")

        with mss.mss() as screen_capture:
            monitor = screen_capture.monitors[0]
            screenshot = screen_capture.grab(monitor)
            path = SCREENSHOTS_DIR / f"jarvis_screen_{timestamp}.png"
            mss_tools.to_png(screenshot.rgb, screenshot.size, output=str(path))
        return path

    def _capture_active_window(self, timestamp: str) -> Path:
        try:
            win32gui: Any = importlib.import_module("win32gui")
            win32ui: Any = importlib.import_module("win32ui")
            pil_image = importlib.import_module("PIL.Image")

            hwnd = win32gui.GetForegroundWindow()
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            image = pil_image.frombuffer(
                "RGB",
                (bmp_info["bmWidth"], bmp_info["bmHeight"]),
                bmp_str,
                "raw",
                "BGRX",
                0,
                1,
            )
            path = SCREENSHOTS_DIR / f"jarvis_window_{timestamp}.png"
            image.save(str(path))
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return path
        except Exception:
            return self._capture_fullscreen(timestamp)
