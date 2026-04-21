"""Error telemetry sink for skill and integration failures."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ErrorTelemetry:
    """Append operational failures to a local JSONL file."""

    def __init__(self, target_path: str) -> None:
        self._target_path = Path(target_path)
        self._target_path.parent.mkdir(parents=True, exist_ok=True)

    async def record(
        self,
        component: str,
        error: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist one telemetry event without blocking the main loop."""

        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "component": component,
            "error": error,
            "message": message,
            "metadata": metadata or {},
        }
        await asyncio.to_thread(self._append_line, payload)

    def _append_line(self, payload: dict[str, Any]) -> None:
        with self._target_path.open("a", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(payload, ensure_ascii=True))
            file_handle.write("\n")

