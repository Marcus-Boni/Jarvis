"""Automatic fact extraction and persistence from conversations."""

from __future__ import annotations

from loguru import logger

from core.models import ContextDocument
from llm.memory.chroma_store import ChromaMemoryStore
from llm.ollama_client import OllamaClient

EXTRACTION_PROMPT = """
Voce e um extrator de fatos para um assistente pessoal.
Analise a conversa abaixo e extraia APENAS fatos concretos e duradouros sobre o usuario.
Ignore cumprimentos, perguntas gerais, e respostas do assistente.

Exemplos de fatos validos:
- "Usuario trabalha com frontend usando React e TypeScript"
- "Usuario prefere respostas em portugues"
- "Projeto atual: Marca Ambiental (portal de gestao ambiental)"

Retorne JSON: {"facts": ["fato 1", "fato 2"]} ou {"facts": []} se nao houver fatos novos.

Conversa:
{transcript}
"""


class AutoMemoryExtractor:
    """Extracts and persists durable user facts from each exchange."""

    def __init__(
        self,
        llm_client: OllamaClient,
        memory_store: ChromaMemoryStore,
        min_exchange_length: int = 20,
    ) -> None:
        self._llm_client = llm_client
        self._memory_store = memory_store
        self._min_exchange_length = min_exchange_length
        self._logger = logger.bind(component="auto_memory")

    async def extract_and_store(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> int:
        """Extract facts from an exchange and persist them to memory."""

        exchange_size = len(user_message.strip()) + len(assistant_message.strip())
        if exchange_size < self._min_exchange_length:
            return 0

        transcript = f"Usuario: {user_message}\nJarvis: {assistant_message}"
        prompt = EXTRACTION_PROMPT.format(transcript=transcript)
        try:
            payload = await self._llm_client.complete_json(prompt=prompt)
            raw_facts = payload.get("facts", [])
            facts = _normalize_facts(raw_facts)
            if not facts:
                return 0

            await self._memory_store.add_documents(
                [
                    ContextDocument(
                        source=f"auto_memory:{session_id}",
                        content=fact,
                        metadata={
                            "session_id": session_id,
                            "type": "auto_extracted",
                        },
                    )
                    for fact in facts
                ]
            )
            self._logger.info("auto_memory_stored count={} session={}", len(facts), session_id)
            return len(facts)
        except Exception as exc:  # pragma: no cover
            self._logger.warning("auto_memory_extraction_failed error={}", exc)
            return 0


def _normalize_facts(raw_facts: object) -> list[str]:
    if not isinstance(raw_facts, list):
        return []

    normalized_facts: list[str] = []
    seen: set[str] = set()
    for item in raw_facts:
        fact = str(item).strip()
        normalized_key = fact.casefold()
        if not fact or normalized_key in seen:
            continue
        seen.add(normalized_key)
        normalized_facts.append(fact)
    return normalized_facts
