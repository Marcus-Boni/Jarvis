"""Lifespan-managed dependency container for Jarvis services."""

from __future__ import annotations

from core.config import AppSettings
from core.context_manager import ContextManager
from core.error_telemetry import ErrorTelemetry
from core.intent_classifier import IntentClassifier
from core.orchestrator import Orchestrator
from core.runtime_events import RuntimeEventBroker
from llm.memory.auto_memory import AutoMemoryExtractor
from llm.memory.chroma_store import ChromaMemoryStore
from llm.memory.conversation import ConversationStore
from llm.memory.rag_retriever import MemoryRetriever
from llm.ollama_client import OllamaClient
from llm.prompt_manager import PromptManager
from skills.loader import SkillLoader
from voice.audio_pipeline import AudioPipeline
from voice.stt import WhisperTranscriber
from voice.tts import PiperTTSService
from voice.vad import VoiceActivityDetector


class ServiceContainer:
    """Construct and own runtime services for the application."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.events = RuntimeEventBroker()
        self.error_telemetry = ErrorTelemetry(settings.telemetry.error_log_path)
        self.prompt_manager = PromptManager(jarvis_name=settings.jarvis.name)
        self.llm_client = OllamaClient(settings=settings)
        self.conversation_store = ConversationStore(
            base_directory=settings.memory.conversations_directory
        )
        self.memory_store = ChromaMemoryStore(
            settings=settings,
            llm_client=self.llm_client,
        )
        self.memory_retriever = MemoryRetriever(
            settings=settings,
            memory_store=self.memory_store,
        )
        self.context_manager = ContextManager(
            settings=settings,
            conversation_store=self.conversation_store,
            memory_store=self.memory_store,
            memory_retriever=self.memory_retriever,
        )
        self.auto_memory = (
            AutoMemoryExtractor(
                llm_client=self.llm_client,
                memory_store=self.memory_store,
                min_exchange_length=settings.skills.auto_memory.min_exchange_length,
            )
            if settings.skills.auto_memory.enabled
            else None
        )
        self.skill_loader = SkillLoader(
            settings=settings,
            llm_client=self.llm_client,
            event_broker=self.events,
            error_telemetry=self.error_telemetry,
        )
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
            event_broker=self.events,
            error_telemetry=self.error_telemetry,
            auto_memory=self.auto_memory,
        )
        self.vad = VoiceActivityDetector(settings=settings)
        self.stt = WhisperTranscriber(settings=settings)
        self.tts = PiperTTSService(settings=settings)
        self.audio_pipeline = AudioPipeline(
            settings=settings,
            vad=self.vad,
            stt=self.stt,
            tts=self.tts,
        )

    async def start(self) -> None:
        """Initialize runtime resources."""

        await self.skill_loader.load_builtin_skills()
        await self.events.publish("runtime", {"status": "started", "phase": "phase_2"})

    async def stop(self) -> None:
        """Cleanly release runtime resources."""

        await self.audio_pipeline.stop()
        await self.llm_client.aclose()
