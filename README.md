# Jarvis

Jarvis is a local-first personal AI assistant for a software developer. The system is being built in phases around a modular Python backend, a Next.js dashboard, and local model/runtime integrations such as Ollama, ChromaDB, Playwright, Whisper, Piper, Spotify, Notion, Google Calendar, and Outlook.

## Phase Status

Phase 1 is implemented in this repository:

- Central configuration via YAML + `.env`
- Structured logging
- Async Ollama client
- Intent classification contracts and orchestration flow
- Persistent ChromaDB memory with Ollama embeddings
- Functional App Launcher, Browser Search, Spotify, Notion, Outlook, and Google Calendar skills
- FastAPI app with chat, SSE, WebSocket, skills, memory, health, voice upload, and realtime voice websocket
- Dashboard wired to live backend status, chat, voice, skill toggles, and activity events
- Realtime voice pipeline services for VAD, STT, TTS, and microphone playback orchestration
- Tests, scripts, Make targets, and architecture decisions

Planned next phases:

1. End-to-end runtime validation of every external integration on the target workstation
2. Wake-word improvements beyond transcript keyword gating
3. Hot-reloadable skill discovery and filesystem watching
4. Deeper browser automation and richer RAG memory shaping
5. Packaging, service management, and 24/7 idle optimization

## Repository Layout

```text
api/                FastAPI entrypoints and transports
config/             YAML configuration
core/               Intent orchestration, context, models, settings, logging
dashboard/          Next.js dashboard foundation
llm/                Ollama client, prompts, memory scaffolding
skills/             Skill contracts and initial built-in skills
voice/              Voice pipeline placeholders
scripts/            Setup and runtime helpers
tests/              Unit and smoke tests
```

## Local Development

### Backend

```bash
poetry install
uvicorn api.main:app --reload
```

### Dashboard

```bash
cd dashboard
pnpm install
pnpm dev
```

### Make targets

```bash
make start
make test
make lint
make typecheck
make dashboard
```

## Configuration

- General runtime settings: `config/jarvis.yaml`
- Skill flags: `config/skills.yaml`
- Model registry: `config/models.yaml`
- Secrets and local overrides: `.env`

## FastAPI Endpoints

- `GET /health`
- `POST /api/chat`
- `POST /api/chat/stream`
- `POST /api/voice/stream`
- `GET /api/voice/status`
- `GET /api/skills`
- `POST /api/skills/{skill_name}`
- `POST /api/memory/query`
- `WS /ws/chat`
- `WS /ws/voice`
- `WS /ws/events`

## Notes

- Backend verification in this session: `pytest`, `ruff`, and `mypy` all pass.
- Frontend verification in this session: `pnpm exec tsc --noEmit` passes.
- `next build` failed in this environment with `spawn EPERM`, so production Next build output was not verified here.
- External runtime integrations still depend on local credentials, models, binaries, audio devices, and provider consent flows being present on the target machine.
