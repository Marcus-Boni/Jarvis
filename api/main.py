"""FastAPI application entrypoint for Jarvis."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api.routes import chat, memory, skills, voice, webhooks
from api.websocket.handler import websocket_router
from core.config import AppSettings
from core.logging import configure_logging, get_logger
from core.service_container import ServiceContainer
from core.system_tray import JarvisTrayIcon


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and tear down runtime services."""

    configure_logging()
    logger = get_logger(component="api")
    settings = AppSettings.load()
    container = ServiceContainer(settings=settings)
    await container.start()
    app.state.container = container
    if os.name == "nt":
        tray = JarvisTrayIcon(
            settings=settings,
            event_broker=container.events,
            memory_store=container.memory_store,
        )
        tray.start_in_thread(loop=asyncio.get_running_loop())
        app.state.tray = tray
    logger.info("jarvis_api_started")
    try:
        yield
    finally:
        tray_icon: JarvisTrayIcon | None = getattr(app.state, "tray", None)
        if tray_icon is not None:
            tray_icon.stop()
        await container.stop()
        logger.info("jarvis_api_stopped")


app = FastAPI(title="Jarvis API", version="0.1.0", lifespan=lifespan)

settings_for_cors = AppSettings.load()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_for_cors.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(skills.router)
app.include_router(memory.router)
app.include_router(webhooks.router)
app.include_router(websocket_router)


@app.middleware("http")
async def attach_trace_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a trace identifier to every request for cross-cutting logs."""

    request.state.trace_id = request.headers.get("x-trace-id", str(uuid4()))
    response = await call_next(request)
    response.headers["x-trace-id"] = request.state.trace_id
    return response


@app.get("/health")
async def healthcheck(request: Request) -> dict[str, object]:
    """Return runtime health and integration readiness."""

    container: ServiceContainer = request.app.state.container
    return {
        "status": "ok",
        "voice_active": container.audio_pipeline.is_active,
        "ollama_reachable": await container.llm_client.health(),
        "loaded_skills": [skill.name for skill in container.skill_loader.list_all()],
    }
