# Jarvis Architecture Decisions

## ADR-001: Local-first service boundaries

- Date: 2026-04-20
- Status: accepted

Jarvis is split into `core`, `llm`, `skills`, `api`, `voice`, and `dashboard` packages so each concern can evolve independently without turning the assistant into one large runtime blob.

Why:
- Voice, LLM, browser automation, and external integrations have different latency and failure profiles.
- Skills need hot-reload and isolated contracts.
- The dashboard should remain optional and independently deployable.

Tradeoff:
- More modules and wiring upfront.
- Slightly more bootstrap code in the first phase.

## ADR-002: FastAPI as the internal system bus

- Date: 2026-04-20
- Status: accepted

FastAPI is the control plane for chat, voice, skill management, memory inspection, and live status over WebSocket/SSE.

Why:
- Async-first I/O fits local model calls, browser automation, and streaming well.
- Pydantic v2 keeps schemas and validation aligned.
- Lifespan hooks give a clean place to initialize Ollama clients, skill registries, and future audio workers.

## ADR-003: Pydantic settings + YAML hybrid configuration

- Date: 2026-04-20
- Status: accepted

General runtime configuration lives in YAML under `config/`, while secrets and local machine overrides live in `.env`.

Why:
- The system has many tunable, non-secret knobs that are easier to reason about in YAML.
- Provider credentials and local tokens should not live in committed config files.

## ADR-004: Intent orchestration before autonomous skill execution

- Date: 2026-04-20
- Status: accepted

Every request flows through an intent classifier, context enrichment, and a skill router before falling back to the LLM.

Why:
- Directly calling tools from raw user text is unsafe and hard to debug.
- Structured intent data allows better logs, policy checks, and future evaluation datasets.
- Composite intents need a coordinator rather than ad hoc string matching inside each skill.

## ADR-005: Dashboard visual direction

- Date: 2026-04-20
- Status: accepted

The dashboard starts with a technical console aesthetic that avoids generic AI purple gradients: parchment-like surfaces, graphite text, cyan telemetry, and amber action accents.

Why:
- The product is for a developer, not a mass-market chatbot.
- The UI needs to feel like a control room, not a marketing site.
- Warm/cool accent pairing helps separate action, observability, and status states.

## ADR-006: Persistent semantic memory with ChromaDB

- Date: 2026-04-20
- Status: accepted

Phase 1 replaces the in-process memory placeholder with ChromaDB backed by Ollama embeddings.

Why:
- Conversation history now survives restarts.
- Every exchange can become retrievable context for later tasks.
- The same memory substrate supports explicit recall and passive personalization.

Tradeoff:
- More moving parts in local setup.
- Embedding on write adds latency, so writes stay small and async.

## ADR-007: Lazy imports for heavy local integrations

- Date: 2026-04-20
- Status: accepted

Optional integrations such as Torch, sounddevice, MSAL, Google auth, and desktop window control are imported lazily at runtime instead of module import time.

Why:
- API startup should stay healthy even when one provider stack is missing.
- Tests and static analysis stay fast and deterministic.
- Setup failures degrade gracefully to per-skill errors instead of whole-app crashes.

## ADR-008: Spotify auth prefers PKCE when no client secret exists

- Date: 2026-04-20
- Status: accepted

Jarvis uses Spotify OAuth with a desktop-friendly fallback to PKCE when no client secret is configured.

Why:
- Desktop/local assistants should not require a stored client secret.
- PKCE still gives refreshable user tokens.
- This keeps the integration usable in local-only setups.

## ADR-009: Dashboard treats WebSockets as the live source of truth

- Date: 2026-04-20
- Status: accepted

The dashboard now uses `/ws/chat`, `/ws/voice`, and `/ws/events` for live interaction and activity telemetry, while REST remains the control/config surface.

Why:
- Chat and voice benefit from incremental updates instead of polling.
- Activity logs and status transitions should appear immediately.
- REST alone would make the assistant feel laggy and indirect.

## ADR-010: Voice pipeline uses raw PCM internally and WAV at browser boundaries

- Date: 2026-04-20
- Status: accepted

Piper audio stays raw PCM inside the Python voice pipeline for low-overhead playback, but HTTP/WebSocket responses wrap that PCM in WAV for browser compatibility.

Why:
- Local playback via sounddevice works directly with PCM.
- Browsers and Web Audio tooling expect a decodable container for remote playback.
- This keeps one TTS source with two delivery formats.

## ADR-011: Visible browser handoff must respect the Windows default browser

- Date: 2026-04-21
- Status: accepted

When Jarvis needs to open a page for the user to see, it now delegates that handoff to the Windows default browser instead of Playwright's bundled Chromium.

Why:
- The assistant should match the user's configured browser workflow instead of forcing an internal runtime choice.
- Playwright Chromium remains useful for scraping and form automation, but it is the wrong UX surface for visible navigation.
- Separating visible browsing from internal automation keeps both paths simpler to reason about.

Tradeoff:
- Registry detection is Windows-specific and needs a graceful fallback path.
- There are now two browser execution modes to maintain.

## ADR-012: Intent classification uses a small TTL cache

- Date: 2026-04-21
- Status: accepted

Intent results are cached in-memory for five minutes with bounded capacity and oldest-entry eviction.

Why:
- Repeated voice retries and dashboard resends often replay identical utterances.
- Avoiding redundant LLM classification removes unnecessary latency from the hot path.
- A small bounded cache gives the speedup without introducing durable correctness risk.

Tradeoff:
- Very recent classifier improvements do not apply to already cached inputs until expiry.
- Capacity is intentionally small, so low-value entries may be evicted quickly under bursty usage.

## ADR-013: Compound intents execute the top matching skills in parallel

- Date: 2026-04-21
- Status: accepted

For compound intents, Jarvis now scores candidate skills concurrently and executes the top matches in parallel with isolated failure handling.

Why:
- Multi-action requests should not pay unnecessary serial latency when the chosen skills are independent.
- Parallel score evaluation is a direct latency win because `can_handle()` calls may already depend on async I/O or model hints.
- Failure isolation keeps one broken skill from collapsing the whole request.

Tradeoff:
- Concurrent skill execution increases pressure on shared local resources.
- Results must stay independent enough to avoid ordering assumptions between skills.
