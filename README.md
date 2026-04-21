# Jarvis

Jarvis is a local-first personal AI assistant for a software developer. The system is being built in phases around a modular Python backend, a Next.js dashboard, and local model/runtime integrations such as Ollama, ChromaDB, Playwright, Whisper, Piper, Spotify, Notion, Google Calendar, and Outlook.

## Phase Status

### Phase 0 - Foundation
- FastAPI, orchestrator, intent classifier, skill system
- Dashboard Next.js (control-room aesthetic)
- Config YAML + `.env`, testes unitarios

### Phase 1 - Voice + Real Skills
- Silero VAD + faster-whisper (`large-v3` CUDA) + Piper TTS
- AudioPipeline assincrono com `sounddevice`
- AppLauncherSkill, SpotifySkill, BrowserSearchSkill reais
- NotionSkill, OutlookSkill (Microsoft Graph), CalendarSkill (Google)
- Dashboard conectado ao WebSocket real

### Phase 2 - Memory + Advanced Skills
- ChromaDB real com embeddings Ollama (`nomic-embed-text`) e fallback in-memory
- RAG por similaridade coseno
- `AutoMemoryExtractor` para fatos duradouros extraidos automaticamente
- Browser padrao do Windows para handoff visivel; Playwright mantido para scraping headless
- `VolumeSkill` com controle de audio e teclas de midia no Windows
- `AppLauncherSkill` com foco de janela existente via Win32
- `IntentCache` com TTL de 5 minutos e capacidade de 128 entradas
- Skill chaining paralelo com `asyncio.gather` para intents compostas

### Phase 3 - Planned
- Wake word "Jarvis" via `pvporcupine`
- File management skill
- Clipboard skill
- Screenshot + OCR skill
- System tray icon

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

- Backend verification in this session: pending fresh Phase 2 validation after the new changes.
- External runtime integrations still depend on local credentials, models, binaries, audio devices, and provider consent flows being present on the target machine.
