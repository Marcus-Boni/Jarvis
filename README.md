# Jarvis

Jarvis is a local-first personal AI assistant for a software developer. The system is being built in phases around a modular Python backend, a Next.js dashboard, and local model/runtime integrations such as Ollama, ChromaDB, Playwright, Whisper, and Piper.

## Phase Status

Phase 0 is implemented in this repository:

- Central configuration via YAML + `.env`
- Structured logging
- Async Ollama client
- Intent classification contracts and orchestration flow
- Skill registry and initial skill scaffolds
- FastAPI app with chat, SSE, WebSocket, skills, memory, voice placeholder, and health endpoints
- Dashboard foundation with a control-room UI language
- Tests, scripts, Make targets, and architecture decisions

Planned next phases:

1. Voice pipeline
2. Essential skills
3. Productivity integrations
4. Persistent memory and RAG
5. API hardening and dashboard real-time wiring
6. Polish, verification, and operational docs

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
- `GET /api/skills`
- `POST /api/skills/{skill_name}`
- `POST /api/memory/query`
- `WS /ws/chat`

## Notes

- The current workspace shell does not expose a usable Python interpreter, so the Python test and typecheck commands have not been executed in this session.
- The dashboard is scaffolded but dependencies are not installed automatically.
- Runtime integrations like Spotify OAuth, Notion, Calendar, ChromaDB, Whisper, Piper, and Playwright still require their Phase 1-5 implementations.

