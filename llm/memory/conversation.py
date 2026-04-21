"""Persistent conversation transcript storage."""

from __future__ import annotations

import asyncio
from pathlib import Path

from core.models import ConversationMessage


class ConversationStore:
    """Stores conversations as per-session JSON lines files."""

    def __init__(self, base_directory: str) -> None:
        self._base_directory = Path(base_directory)
        self._base_directory.mkdir(parents=True, exist_ok=True)

    async def load_messages(self, session_id: str) -> list[ConversationMessage]:
        """Load transcript messages for a session."""

        target_file = self._target_file(session_id=session_id)
        if not target_file.exists():
            return []

        return await asyncio.to_thread(self._read_messages, target_file)

    async def append_messages(self, session_id: str, messages: list[ConversationMessage]) -> None:
        """Append transcript messages to a session file."""

        target_file = self._target_file(session_id=session_id)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(self._append_messages, target_file, messages)

    def _target_file(self, session_id: str) -> Path:
        """Resolve the per-session transcript path."""

        return self._base_directory / f"{session_id}.jsonl"

    def _read_messages(self, target_file: Path) -> list[ConversationMessage]:
        messages: list[ConversationMessage] = []
        with target_file.open("r", encoding="utf-8") as file_handle:
            for line in file_handle:
                payload = ConversationMessage.model_validate_json(line.strip())
                messages.append(payload)
        return messages

    def _append_messages(self, target_file: Path, messages: list[ConversationMessage]) -> None:
        with target_file.open("a", encoding="utf-8") as file_handle:
            for message in messages:
                file_handle.write(message.model_dump_json())
                file_handle.write("\n")
