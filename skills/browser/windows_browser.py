"""Windows default browser detection and URL launching helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import ModuleType

from loguru import logger

winreg: ModuleType | None
try:  # pragma: no cover - platform specific
    import winreg as _winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None
else:  # pragma: no cover - platform specific
    winreg = _winreg

_logger = logger.bind(component="windows_browser")
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def get_default_browser_path() -> str | None:
    """Detect the default browser executable path from the Windows registry."""

    if winreg is None:
        return None

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
        ) as key:
            prog_id, _ = winreg.QueryValueEx(key, "ProgID")

        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT,
            rf"{prog_id}\shell\open\command",
        ) as key:
            command, _ = winreg.QueryValueEx(key, "")

        executable_path = _extract_executable_path(str(command))
        if executable_path is None:
            return None
        return executable_path if Path(executable_path).exists() else None
    except (OSError, ValueError, IndexError) as exc:
        _logger.warning("default_browser_detection_failed error={}", exc)
        return None


def get_default_browser_name() -> str:
    """Return a friendly name for the current Windows default browser."""

    path = get_default_browser_path()
    if not path:
        return "browser padrao"

    normalized_path = path.lower()
    if "chrome" in normalized_path:
        return "Google Chrome"
    if "firefox" in normalized_path:
        return "Mozilla Firefox"
    if "msedge" in normalized_path or "edge" in normalized_path:
        return "Microsoft Edge"
    if "brave" in normalized_path:
        return "Brave"
    if "opera" in normalized_path:
        return "Opera"
    return Path(path).stem


def open_url_in_default_browser(url: str) -> bool:
    """Open a URL using the Windows default browser."""

    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", url],
            creationflags=_CREATE_NO_WINDOW,
        )
        _logger.info("url_opened_in_default_browser url={}", url)
        return True
    except Exception as exc:  # pragma: no cover
        _logger.error("failed_to_open_url url={} error={}", url, exc)
        return False


def open_url_in_browser_exe(url: str) -> bool:
    """Open a URL by directly invoking the detected browser executable."""

    executable = get_default_browser_path()
    if executable is None:
        return open_url_in_default_browser(url)

    try:
        subprocess.Popen([executable, url], creationflags=_CREATE_NO_WINDOW)
        _logger.info("url_opened_via_browser_exe exe={} url={}", executable, url)
        return True
    except Exception as exc:  # pragma: no cover
        _logger.error("browser_exe_open_failed exe={} error={}", executable, exc)
        return open_url_in_default_browser(url)


def _extract_executable_path(command: str) -> str | None:
    stripped_command = command.strip()
    if stripped_command.startswith('"'):
        parts = stripped_command.split('"')
        return parts[1] if len(parts) > 1 else None

    executable, _, _ = stripped_command.partition(" ")
    return executable or None
