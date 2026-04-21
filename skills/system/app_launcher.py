"""Windows application launcher with best-effort window focus."""

from __future__ import annotations

import asyncio
import importlib
import os
import re
import subprocess
from pathlib import Path
from typing import Any, ClassVar

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from skills.base_skill import BaseSkill

APP_MAP: dict[str, list[str]] = {
    "vscode": [r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
    "spotify": [r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe"],
    "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
    "firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "notion": ["notion.exe"],
    "terminal": ["wt.exe"],
    "explorer": ["explorer.exe"],
    "discord": [
        r"C:\Users\{username}\AppData\Local\Discord\Update.exe",
        "--processStart",
        "Discord.exe",
    ],
    "postman": ["postman.exe"],
    "figma": ["figma.exe"],
}


class AppLauncherSkill(BaseSkill):
    """Open or focus common Windows applications."""

    name: ClassVar[str] = "app_launcher"
    description: ClassVar[str] = "Open desktop applications and focus running windows."
    triggers: ClassVar[list[str]] = [
        "abra o chrome",
        "abre o spotify",
        "open vscode",
        "launch discord",
    ]

    def __init__(
        self,
        settings: AppSettings,
        event_broker: RuntimeEventBroker,
        error_telemetry: ErrorTelemetry,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if intent.category is IntentCategory.SYSTEM_CONTROL:
            return 0.92
        if any(verb in lowered_text for verb in ["abra", "abre", "open", "launch"]):
            if any(app_name in lowered_text for app_name in APP_MAP):
                return 0.8
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        if os.name != "nt":
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="App launcher is implemented for Windows only in this phase.",
            )

        app_name = _extract_app_name(intent=intent)
        if app_name is None:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="I could not determine which application should be opened.",
            )

        try:
            result = await asyncio.to_thread(
                self._open_or_focus_app,
                app_name,
                intent.raw_text,
            )
            await self._event_broker.publish(
                "activity",
                {"component": self.name, "message": result.message},
            )
            return result
        except Exception as exc:  # pragma: no cover
            await self._error_telemetry.record(
                component=self.name,
                error=type(exc).__name__,
                message=str(exc),
                metadata={"app_name": app_name},
            )
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Failed to open {app_name}. The error was logged safely.",
            )

    def _open_or_focus_app(self, app_name: str, utterance: str) -> SkillResult:
        running_process = _find_running_process(app_name)
        if running_process is not None:
            did_focus = _focus_window(process_id=running_process.pid, app_name=app_name)
            focus_message = "and focused it" if did_focus else "but could not focus its window"
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"{app_name} is already running {focus_message}.",
                data={"app_name": app_name, "pid": running_process.pid, "action": "focus"},
            )

        command = _resolve_command(app_name)
        if command is None:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"No executable mapping is configured for {app_name}.",
            )

        extra_args = _extract_launch_arguments(app_name=app_name, utterance=utterance)
        launch_command = [*command, *extra_args]
        working_directory = extra_args[0] if extra_args and Path(extra_args[0]).exists() else None
        subprocess.Popen(
            launch_command,
            cwd=working_directory,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return SkillResult(
            skill_name=self.name,
            success=True,
            message=f"Opened {app_name}.",
            data={"app_name": app_name, "command": launch_command},
        )


def _extract_app_name(intent: Intent) -> str | None:
    entity_app = intent.entities.get("app")
    if entity_app and entity_app in APP_MAP:
        return entity_app

    lowered_text = intent.raw_text.lower()
    for app_name in APP_MAP:
        if app_name in lowered_text:
            return app_name
    return None


def _resolve_command(app_name: str) -> list[str] | None:
    template_parts = APP_MAP.get(app_name)
    if template_parts is None:
        return None

    username = os.environ.get("USERNAME", "")
    resolved_parts = [
        os.path.expandvars(part.format(username=username)) for part in template_parts
    ]
    executable_path = resolved_parts[0]
    if Path(executable_path).exists() or not executable_path.lower().endswith(".exe"):
        return resolved_parts
    return None


def _find_running_process(app_name: str) -> Any | None:
    psutil = importlib.import_module("psutil")
    aliases = {app_name}
    if app_name == "vscode":
        aliases.add("code")
    if app_name == "terminal":
        aliases.add("windowsterminal")

    for process in psutil.process_iter(["name"]):
        process_name = (process.info.get("name") or "").lower().removesuffix(".exe")
        if process_name in aliases:
            return process
    return None


def _focus_window(process_id: int, app_name: str) -> bool:
    try:
        gw = importlib.import_module("pygetwindow")

        for title in gw.getAllTitles():
            lowered_title = title.lower()
            if not title.strip():
                continue
            if app_name in lowered_title or (
                app_name == "vscode" and "visual studio code" in lowered_title
            ):
                for window in gw.getWindowsWithTitle(title):
                    window.activate()
                    return True
    except Exception:
        pass

    try:
        win32con = importlib.import_module("win32con")
        win32gui = importlib.import_module("win32gui")
        win32process = importlib.import_module("win32process")

        focused = False

        def callback(window_handle: int, _: Any) -> None:
            nonlocal focused
            _, target_process_id = win32process.GetWindowThreadProcessId(window_handle)
            if target_process_id != process_id or not win32gui.IsWindowVisible(window_handle):
                return
            win32gui.ShowWindow(window_handle, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(window_handle)
            focused = True

        win32gui.EnumWindows(callback, None)
        return focused
    except Exception:
        return False


def _extract_launch_arguments(app_name: str, utterance: str) -> list[str]:
    if app_name != "vscode":
        return []

    match = re.search(r"(?:no projeto|na pasta|in project)\s+(.+)$", utterance, re.IGNORECASE)
    if match is None:
        return []

    raw_path = match.group(1).strip().strip("\"'")
    candidate_path = Path(raw_path).expanduser()
    if candidate_path.exists():
        return [str(candidate_path)]
    return []
