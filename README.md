# 🤖 Jarvis

<p align="center">
  <em>A local-first, modular, and privacy-focused personal AI assistant for software developers.</em>
</p>

---

**Jarvis** is a highly capable, local-first personal AI assistant tailored for developers. It operates on a modular Python backend paired with a beautiful control-room aesthetic Next.js dashboard. It seamlessly integrates with local AI models and external services to boost your productivity without compromising your privacy.

## ✨ Key Features

- **Local AI Processing**: Uses Ollama for LLMs and embeddings (`nomic-embed-text`), Piper for TTS, and faster-whisper for state-of-the-art Voice-to-Text.
- **Advanced Context & Memory**: Long-term persistent memory using ChromaDB and a locally hosted RAG (Retrieval-Augmented Generation) pipeline.
- **Voice Interactivity**: Wake word detection ("Jarvis") and asynchronous real-time audio pipeline.
- **Deep OS Integration**: Control OS volume, take screenshots (full screen or active window), manage clipboard, and interact with the file system locally.
- **Productivity Ecosystem**: Integrates directly with Spotify, Notion, Google Calendar, Microsoft Outlook, and features a local app launcher.
- **Control Room Dashboard**: A sleek, real-time Next.js web application to monitor states, control skills, view memory blocks, and manage tasks.
- **System Tray**: Unobtrusive background execution with a system tray menu for quick actions.

## 🏗️ Architecture & Tech Stack

- **Backend**: Python, FastAPI, WebSockets
- **Frontend**: Next.js, React, TailwindCSS
- **AI Models**: Ollama (LLM/Embeddings), faster-whisper (STT), Piper (TTS), pvporcupine (Wake Word)
- **Database**: ChromaDB (Vector Store), SQLite
- **Integrations**: Playwright (Headless Scraping), Microsoft Graph (Outlook), Google APIs (Calendar)

### Directory Structure

```text
├── api/                # FastAPI entrypoints, routes, and WebSockets
├── config/             # YAML configurations and model registries
├── core/               # Orchestrator, intent classification, memory extraction
├── dashboard/          # Next.js frontend application
├── llm/                # Ollama client, RAG, and prompt management
├── skills/             # Implementations for integrations (media, system, productivity)
├── voice/              # Audio pipeline, VAD, STT, TTS, and Wake Word
└── scripts/            # Setup and initialization scripts
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ and `poetry`
- Node.js 18+ and `pnpm`
- Ollama installed with the required models (e.g., `llama3`, `nomic-embed-text`)
- Required system binaries for audio (FFmpeg)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/jarvis.git
   cd jarvis
   ```

2. **Backend Setup:**
   ```bash
   poetry install
   ```

3. **Dashboard Setup:**
   ```bash
   cd dashboard
   pnpm install
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in your credentials for external apps (Spotify, Notion, etc.).

### Running Jarvis

You can use the provided Make targets for convenience:

```bash
# Start both backend and dashboard (if defined in Makefile)
make start

# Or start them separately:
# Terminal 1: Backend
poetry run uvicorn api.main:app --reload

# Terminal 2: Dashboard
cd dashboard && pnpm dev
```

### Useful Commands

- `make test`: Run unit and integration tests
- `make lint`: Run linters
- `make typecheck`: Run mypy/type checkers

## 🔌 API Reference (FastAPI)

<details>
<summary><b>Click to expand endpoints</b></summary>

- `GET /health` - System health check
- `POST /api/chat` - Synchronous text chat
- `POST /api/chat/stream` - Streaming text chat
- `POST /api/voice/stream` - Audio streaming input
- `GET /api/voice/status` - Current voice pipeline status
- `GET /api/skills` - List available skills
- `POST /api/skills/{skill_name}` - Trigger a specific skill
- `POST /api/memory/query` - Query ChromaDB memory
- `POST /api/memory/clear` - Wipe current memory contexts
- `POST /api/webhooks/command` - Execute external command
- `WS /ws/chat` - Real-time chat connection
- `WS /ws/voice` - Real-time voice interaction
- `WS /ws/events` - System telemetry and events broadcast

</details>

## 🗺️ Project Roadmap & Phase Status

<details>
<summary><b>Phase 0 - Foundation ✅</b></summary>
FastAPI, orchestrator, intent classifier, skill system. Dashboard Next.js (control-room aesthetic). Config YAML + .env, testes unitarios.
</details>

<details>
<summary><b>Phase 1 - Voice + Real Skills ✅</b></summary>
Silero VAD + faster-whisper (large-v3 CUDA) + Piper TTS, async AudioPipeline com sounddevice. AppLauncherSkill, SpotifySkill, BrowserSearchSkill reais. NotionSkill, OutlookSkill, CalendarSkill. Dashboard conectado ao WebSocket real.
</details>

<details>
<summary><b>Phase 2 - Memory + Advanced Skills ✅</b></summary>
ChromaDB real com embeddings Ollama (nomic-embed-text) e fallback in-memory. RAG por similaridade coseno. AutoMemoryExtractor para fatos duradouros. Browser padrao do Windows para handoff; Playwright para headless. VolumeSkill, AppLauncherSkill com foco via Win32. IntentCache, Skill chaining paralelo.
</details>

<details>
<summary><b>Phase 3 - System Integration ✅</b></summary>
Wake word "Jarvis" via pvporcupine. System Tray com menu e quit. ClipboardSkill, FileManagerSkill (busca, listagem, preview). ScreenshotSkill. NotificationSkill via Windows UI. Dashboard: endpoints configurados e ADRs 14 a 17.
</details>

<details>
<summary><b>Phase 4 - Planned ⏳</b></summary>

- File operations com confirmacao via dialogo
- Politica de retencao de screenshots configuravel
- Skill de agendamento (cron-like via APScheduler)
- Exportar conversa para PDF/Markdown
- Atualizacao OTA dos modelos Piper e Whisper
</details>

## ⚙️ Configuration

- **General runtime settings:** `config/jarvis.yaml`
- **Model registry:** `config/models.yaml`
- **Secrets and local overrides:** `.env`

---

*Notes: External runtime integrations still depend on local credentials, models, binaries, audio devices, and provider consent flows being present on the target machine.*
