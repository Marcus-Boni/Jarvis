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

