"""Windows app launcher with real window focus support."""

from __future__ import annotations

import asyncio
import importlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, ClassVar

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from skills.base_skill import BaseSkill
from skills.browser.windows_browser import get_default_browser_path, open_url_in_default_browser

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_USERNAME = os.environ.get("USERNAME", "User")

APP_MAP: dict[str, list[str]] = {
    "vscode": [rf"C:\Users\{_USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
    "code": [rf"C:\Users\{_USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe"],
    "spotify": [rf"C:\Users\{_USERNAME}\AppData\Local\Microsoft\WindowsApps\Spotify.exe"],
    "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
    "firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "edge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "terminal": ["wt.exe"],
    "powershell": ["powershell.exe"],
    "explorer": ["explorer.exe"],
    "discord": [
        rf"C:\Users\{_USERNAME}\AppData\Local\Discord\Update.exe",
        "--processStart",
        "Discord.exe",
    ],
    "notion": [rf"C:\Users\{_USERNAME}\AppData\Local\Programs\Notion\Notion.exe"],
    "postman": [rf"C:\Users\{_USERNAME}\AppData\Local\Postman\Postman.exe"],
    "figma": [rf"C:\Users\{_USERNAME}\AppData\Local\Figma\Figma.exe"],
    "slack": [rf"C:\Users\{_USERNAME}\AppData\Local\slack\slack.exe"],
    "teams": [rf"C:\Users\{_USERNAME}\AppData\Local\Microsoft\Teams\current\Teams.exe"],
    "outlook": ["outlook.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
}

APP_ALIASES: dict[str, str] = {
    "visual studio code": "vscode",
    "vs code": "vscode",
    "navegador": "browser",
    "browser": "browser",
    "spotify": "spotify",
    "discord": "discord",
    "terminal": "terminal",
    "calculadora": "calculator",
    "bloco de notas": "notepad",
    "gerenciador de arquivos": "explorer",
    "explorador de arquivos": "explorer",
    "file manager": "explorer",
    "windows explorer": "explorer",
    "pasta downloads": "explorer",
}

_FILE_MANAGER_ALIASES = frozenset(APP_ALIASES) - {
    "visual studio code", "vs code", "navegador", "browser", "spotify",
    "discord", "terminal", "calculadora", "bloco de notas",
}


class AppLauncherSkill(BaseSkill):
    """Open Windows apps or focus the existing window when possible."""

    name: ClassVar[str] = "app_launcher"
    description: ClassVar[str] = "Abre aplicativos no Windows e foca a janela se ja estiver aberta."
    triggers: ClassVar[list[str]] = list(APP_MAP.keys()) + list(APP_ALIASES.keys())

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

    def _resolve_app_name(self, raw_text: str) -> str | None:
        lowered_text = raw_text.lower()
        for alias, canonical_name in APP_ALIASES.items():
            if alias in lowered_text:
                return canonical_name
        for app_name in APP_MAP:
            if app_name in lowered_text:
                return app_name
        return None

    async def can_handle(self, intent: Intent) -> float:
        lowered = intent.raw_text.lower()
        # Explicit file-manager / explorer phrases beat file_manager_skill's 0.84
        if any(alias in lowered for alias in _FILE_MANAGER_ALIASES):
            return 0.96
        if intent.category is IntentCategory.SYSTEM_CONTROL:
            app_name = self._resolve_app_name(intent.raw_text)
            return 0.95 if app_name else 0.72
        if any("abr" in action.lower() or "open" in action.lower() for action in intent.actions):
            return 0.65
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del context
        app_key = intent.entities.get("app") or self._resolve_app_name(intent.raw_text)
        if not app_key:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Nao reconheci qual aplicativo voce quer abrir.",
            )

        try:
            result = await asyncio.to_thread(self._open_or_focus_app, app_key.lower(), intent.raw_text)
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
                metadata={"app_name": app_key},
            )
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Erro ao abrir {app_key}. O erro foi registrado.",
            )

    def _open_or_focus_app(self, app_key: str, raw_text: str = "") -> SkillResult:
        if app_key == "explorer":
            # Open specific folder if mentioned, otherwise open the default explorer view
            folder = _extract_target_folder(raw_text)
            cmd = ["explorer.exe", str(folder)] if folder else ["explorer.exe"]
            subprocess.Popen(cmd, creationflags=_CREATE_NO_WINDOW)
            label = folder.name if folder else "Explorador de Arquivos"
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"{label} aberto.",
                data={"action": "launched", "app": "explorer", "folder": str(folder) if folder else None},
            )

        if app_key == "browser":
            opened = open_url_in_default_browser("about:blank")
            return SkillResult(
                skill_name=self.name,
                success=opened,
                message=(
                    "Browser padrao aberto."
                    if opened
                    else "Nao consegui abrir o browser padrao."
                ),
                data={"action": "launched", "app": "browser", "exe": get_default_browser_path()},
            )

        command = _resolve_command(app_key)
        if command is None:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Aplicativo '{app_key}' nao esta configurado ou nao foi encontrado.",
            )

        process_name = _process_name_from_command(command[0])
        should_focus_existing = self._settings.skills.app_launcher.focus_existing
        if should_focus_existing and process_name:
            existing_process = _find_running_process(process_name)
            if existing_process is not None and _focus_window(process_name):
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=f"{app_key.title()} ja estava aberto e a janela foi focada.",
                    data={"action": "focused", "app": app_key},
                )

        subprocess.Popen(command, creationflags=_CREATE_NO_WINDOW)
        return SkillResult(
            skill_name=self.name,
            success=True,
            message=f"{app_key.title()} aberto com sucesso.",
            data={"action": "launched", "app": app_key, "command": command},
        )


_FOLDER_MAP: dict[str, Path] = {
    "downloads": Path.home() / "Downloads",
    "documentos": Path.home() / "Documents",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "área de trabalho": Path.home() / "Desktop",
    "area de trabalho": Path.home() / "Desktop",
    "imagens": Path.home() / "Pictures",
    "pictures": Path.home() / "Pictures",
    "videos": Path.home() / "Videos",
    "músicas": Path.home() / "Music",
    "musicas": Path.home() / "Music",
}


def _extract_target_folder(raw_text: str) -> Path | None:
    lowered = raw_text.lower()
    for name, path in _FOLDER_MAP.items():
        if name in lowered:
            return path
    return None


def _resolve_command(app_key: str) -> list[str] | None:
    command = APP_MAP.get(app_key)
    if command is None:
        return None

    executable = command[0]
    if Path(executable).exists() or shutil.which(executable):
        return command
    return None


def _process_name_from_command(executable: str) -> str:
    return Path(executable).stem.lower().removesuffix(".exe")


def _find_running_process(app_name: str) -> Any | None:
    """Find a running process matching the application name."""

    psutil: Any = importlib.import_module("psutil")
    target_name = app_name.lower()
    for process in psutil.process_iter(["name", "exe"]):
        try:
            process_name = str(process.info.get("name") or "").lower().removesuffix(".exe")
            process_executable = str(process.info.get("exe") or "").lower()
            if target_name == process_name or target_name in process_executable:
                return process
        except Exception:
            continue
    return None


def _focus_window(process_name: str) -> bool:
    """Bring an application's main window to the foreground via Win32."""

    psutil: Any = importlib.import_module("psutil")
    win32con: Any = importlib.import_module("win32con")
    win32gui: Any = importlib.import_module("win32gui")
    win32process: Any = importlib.import_module("win32process")

    hwnd_list: list[int] = []

    def enum_callback(hwnd: int, _: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(process_id)
            current_name = process.name().lower().removesuffix(".exe")
            if process_name.lower() in current_name:
                hwnd_list.append(hwnd)
        except Exception:
            return True
        return True

    win32gui.EnumWindows(enum_callback, None)
    if not hwnd_list:
        return False

    hwnd = hwnd_list[0]
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    return True
