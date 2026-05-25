"""Safe file system navigation and opening skill."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import ClassVar

from core.models import Intent, RequestContext, SkillResult
from skills.base_skill import BaseSkill

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
SAFE_SEARCH_ROOTS = [
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Projects",
]

KNOWN_FOLDERS: dict[str, Path] = {
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
PREVIEWABLE_SUFFIXES = {".txt", ".md", ".json", ".py", ".toml", ".yaml", ".yml"}


class FileManagerSkill(BaseSkill):
    """Search, open, preview, and list files within safe roots."""

    name: ClassVar[str] = "file_manager"
    description: ClassVar[str] = "Busca, abre e gerencia arquivos no Windows com seguranca."
    triggers: ClassVar[list[str]] = [
        "arquivo",
        "file",
        "abra o arquivo",
        "busque arquivo",
        "encontre o arquivo",
        "listar arquivos",
    ]

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        file_keywords = ["arquivo", "file", "pasta", "folder", "documento", "pdf", "xlsx"]
        if any(keyword in lowered_text for keyword in file_keywords):
            return 0.84
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del context
        lowered_text = intent.raw_text.lower()
        query = intent.entities.get("query", "")
        try:
            if any(token in lowered_text for token in ["busque", "encontre", "procure", "find"]):
                filename = query or _extract_filename(intent.raw_text)
                if not filename:
                    return SkillResult(
                        skill_name=self.name,
                        success=False,
                        message="Nao entendi qual arquivo buscar.",
                    )
                found_files = await asyncio.to_thread(_search_files, filename, SAFE_SEARCH_ROOTS)
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=_format_file_list(found_files),
                    data={
                        "files": [str(file_path) for file_path in found_files],
                        "previews": {
                            str(file_path): _read_preview(file_path)
                            for file_path in found_files[:3]
                            if file_path.is_file()
                        },
                    },
                )

            if any(token in lowered_text for token in ["abra", "open", "abre"]):
                filename = query or _extract_filename(intent.raw_text)
                found_files = await asyncio.to_thread(_search_files, filename, SAFE_SEARCH_ROOTS)
                if not found_files:
                    return SkillResult(
                        skill_name=self.name,
                        success=False,
                        message=f"Arquivo '{filename}' nao encontrado.",
                    )
                target = found_files[0]
                command = ["explorer", str(target)] if os.name == "nt" else [str(target)]
                await asyncio.to_thread(
                    subprocess.Popen,
                    command,
                    creationflags=_CREATE_NO_WINDOW,
                )
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=f"Abrindo {target.name}.",
                    data={"file": str(target), "preview": _read_preview(target)},
                )

            _list_tokens = [
                "liste", "list", "mostrar", "mostra",
                "o que tem", "o que há", "o que ha",
                "quais arquivos", "conteúdo", "conteudo",
                "ver pasta", "ver arquivos",
            ]
            if any(token in lowered_text for token in _list_tokens):
                target_dir = _resolve_known_folder(lowered_text) or (
                    Path(query) if query else Path.home() / "Documents"
                )
                files = await asyncio.to_thread(_list_directory, target_dir)
                if not files:
                    return SkillResult(
                        skill_name=self.name,
                        success=True,
                        message=f"A pasta '{target_dir.name}' está vazia ou inacessível.",
                        data={"files": [], "folder": str(target_dir)},
                    )
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=_format_file_list(files[:20]),
                    data={"files": [str(file_path) for file_path in files[:20]]},
                )

            # Implicit listing: "pasta X" without explicit verb
            inferred_folder = _resolve_known_folder(lowered_text)
            if inferred_folder:
                files = await asyncio.to_thread(_list_directory, inferred_folder)
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=_format_file_list(files[:20]) if files else f"'{inferred_folder.name}' está vazio.",
                    data={"files": [str(f) for f in files[:20]]},
                )

            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Comando de arquivo nao reconhecido. Tente: busque, abra ou liste.",
            )
        except Exception as exc:  # pragma: no cover
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Erro no gerenciador de arquivos: {exc}",
            )


def _resolve_known_folder(lowered_text: str) -> Path | None:
    for name, path in KNOWN_FOLDERS.items():
        if name in lowered_text:
            return path
    return None


def _search_files(filename: str, roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    pattern = filename.lower()
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if pattern in path.name.lower():
                found.append(path)
            if len(found) >= 10:
                return found
    return found


def _list_directory(directory: Path) -> list[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    return sorted(directory.iterdir(), key=lambda candidate: (candidate.is_file(), candidate.name.lower()))


def _extract_filename(raw_text: str) -> str:
    patterns = [
        r"(?:arquivo|file|documento|documentos?)\s+['\"]?(.+?)['\"]?\s*$",
        r"(?:busque|encontre|abra|procure)\s+(?:o\s+)?(.+?)(?:\s+em\s+|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return raw_text.strip()


def _format_file_list(files: list[Path]) -> str:
    if not files:
        return "Nenhum arquivo encontrado."
    return "\n".join(f"- {file_path.name} ({file_path.parent})" for file_path in files)


def _read_preview(path: Path) -> str:
    if not path.is_file() or path.suffix.lower() not in PREVIEWABLE_SUFFIXES:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:500]
    except OSError:
        return ""
