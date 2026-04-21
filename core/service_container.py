"""Lifespan-managed dependency container for Jarvis services."""

from __future__ import annotations

from core.config import AppSettings
from core.context_manager import ContextManager
from core.intent_classifier import IntentClassifier
from core.orchestrator import Orchestrator
from llm.memory.chroma_store import ChromaMemoryStore
from llm.memory.conversation import ConversationStore
from llm.memory.rag_retriever import MemoryRetriever
from llm.ollama_client import OllamaClient
from llm.prompt_manager import PromptManager
from skills.loader import SkillLoader


class ServiceContainer:
    """Constructs and owns runtime services for the application."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.prompt_manager = PromptManager(jarvis_name=settings.jarvis.name)
        self.llm_client = OllamaClient(settings=settings)
        self.conversation_store = ConversationStore(base_directory=settings.memory.conversations_directory)
        self.memory_store = ChromaMemoryStore(settings=settings)
        self.memory_retriever = MemoryRetriever(
            settings=settings,
            llm_client=self.llm_client,
            memory_store=self.memory_store,
        )
        self.context_manager = ContextManager(
            conversation_store=self.conversation_store,
            memory_retriever=self.memory_retriever,
        )
        self.skill_loader = SkillLoader()
        self.intent_classifier = IntentClassifier(
            llm_client=self.llm_client,
            prompt_manager=self.prompt_manager,
        )
        self.orchestrator = Orchestrator(
            classifier=self.intent_classifier,
            context_manager=self.context_manager,
            llm_client=self.llm_client,
            prompt_manager=self.prompt_manager,
            skill_loader=self.skill_loader,
        )

    async def start(self) -> None:
        """Initialize runtime resources."""

        await self.skill_loader.load_builtin_skills()

    async def stop(self) -> None:
        """Cleanly release runtime resources."""

        await self.llm_client.aclose()

