export const statusCards = [
  {
    label: "Model Ready",
    value: "Mistral Nemo",
    detail: "RTX 4050 profile active",
    tone: "success",
  },
  {
    label: "Memory",
    value: "Warm",
    detail: "Chroma scaffold loaded",
    tone: "info",
  },
  {
    label: "Voice",
    value: "Phase 1",
    detail: "Pipeline staged, runtime pending",
    tone: "warning",
  },
  {
    label: "Local Auth",
    value: "Token",
    detail: "Enabled when .env token is present",
    tone: "default",
  },
] as const;

export const activityItems = [
  "Intent router classified Spotify, browser, memory, and system flows.",
  "FastAPI now exposes chat, SSE, WebSocket, memory, and skills routes.",
  "Dashboard foundation tracks local model, memory, and runtime readiness.",
  "Voice, productivity, and RAG integrations remain queued for later phases.",
];

export const skillItems = [
  { name: "App Launcher", state: "Scaffolded", description: "OS launch/focus control in Phase 2." },
  { name: "Browser Search", state: "Scaffolded", description: "DuckDuckGo + Playwright integration next." },
  { name: "Spotify", state: "Scaffolded", description: "OAuth and playback wiring queued." },
];

