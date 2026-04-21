"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BrainCircuit,
  DatabaseZap,
  Gauge,
  RadioTower,
  ShieldCheck,
} from "lucide-react";

import { ChatShell } from "@/components/chat-shell";
import { StatusCard } from "@/components/status-card";
import { useJarvisEvents } from "@/hooks/use-jarvis-events";
import { useJarvisStream } from "@/hooks/use-jarvis-stream";
import { useJarvisVoice } from "@/hooks/use-jarvis-voice";

type StatusTone = "success" | "warning" | "info" | "default";

type SkillStatus = {
  description: string;
  enabled: boolean;
  name: string;
  triggers: string[];
};

type HealthPayload = {
  loaded_skills: string[];
  ollama_reachable: boolean;
  status: string;
  voice_active: boolean;
};

const telemetry = [
  { icon: BrainCircuit, label: "Intent Engine", detail: "Zero-shot + cached routing" },
  { icon: DatabaseZap, label: "Memory Layer", detail: "ChromaDB + conversation recall" },
  { icon: RadioTower, label: "Voice Loop", detail: "Mic capture, STT, TTS, websocket voice" },
  { icon: ShieldCheck, label: "Safety", detail: "Errors logged and destructive actions guarded" },
];

export default function HomePage() {
  const {
    appendAssistantChunk,
    appendUserMessage,
    completeAssistantMessage,
    connectionStatus,
    draft,
    isPending,
    messages,
    sendMessage,
    setDraft,
  } = useJarvisStream();
  const { events } = useJarvisEvents();
  const { toggleListening, voiceConnectionStatus, voiceState } = useJarvisVoice({
    onAssistantChunk: appendAssistantChunk,
    onAssistantDone: completeAssistantMessage,
    onTranscript: appendUserMessage,
  });
  const [health, setHealth] = useState<HealthPayload | null>(null);
  const [skills, setSkills] = useState<SkillStatus[]>([]);

  useEffect(() => {
    const loadData = async () => {
      const [healthResponse, skillsResponse] = await Promise.all([
        fetch("http://localhost:8000/health"),
        fetch("http://localhost:8000/api/skills"),
      ]);
      const nextHealth = (await healthResponse.json()) as HealthPayload;
      const nextSkills = (await skillsResponse.json()) as { items: SkillStatus[] };
      setHealth(nextHealth);
      setSkills(nextSkills.items);
    };
    void loadData();
  }, []);

  const statusCards = useMemo(
    () => [
      {
        label: "Model",
        value: health?.ollama_reachable ? "Reachable" : "Offline",
        detail: health?.ollama_reachable ? "Ollama responded to health check" : "Backend cannot reach Ollama",
        tone: (health?.ollama_reachable ? "success" : "warning") as StatusTone,
      },
      {
        label: "Memory",
        value: "ChromaDB",
        detail: "Persistent vector memory is active in Phase 1.",
        tone: "info" as StatusTone,
      },
      {
        label: "Voice",
        value: voiceState,
        detail: `Voice socket ${voiceConnectionStatus}.`,
        tone: (voiceState === "idle" ? "default" : "success") as StatusTone,
      },
      {
        label: "Skills",
        value: `${skills.filter((skill) => skill.enabled).length}`,
        detail: "Builtin skills loaded from the backend registry.",
        tone: "default" as StatusTone,
      },
    ],
    [health?.ollama_reachable, skills, voiceConnectionStatus, voiceState]
  );

  const toggleSkill = async (skillName: string, enabled: boolean) => {
    await fetch(`http://localhost:8000/api/skills/${skillName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: !enabled }),
    });
    setSkills((currentSkills) =>
      currentSkills.map((skill) =>
        skill.name === skillName ? { ...skill, enabled: !enabled } : skill
      )
    );
  };

  return (
    <main className="app-shell">
      <aside className="left-rail panel">
        <div className="rail-header">
          <span className="eyebrow">Jarvis</span>
          <h1>Local Control Room</h1>
          <p>Voice, memory, local models, productivity integrations, and safe execution.</p>
        </div>

        <nav className="rail-nav" aria-label="Primary">
          <a className="nav-item current" href="#workspace">
            Workspace
          </a>
          <a className="nav-item" href="#skills">
            Skills
          </a>
          <a className="nav-item" href="#activity">
            Activity
          </a>
          <a className="nav-item" href="#config">
            Config
          </a>
        </nav>

        <section className="rail-meter">
          <div>
            <span className="eyebrow">Runtime</span>
            <strong>{health?.status === "ok" ? "Phase 1 online" : "Checking backend"}</strong>
          </div>
          <div className="meter-track" aria-hidden="true">
            <span className="meter-fill" />
          </div>
          <p>Text chat, voice websocket, skills, and Chroma memory are wired to the live backend.</p>
        </section>
      </aside>

      <section className="workspace" id="workspace">
        <header className="hero panel">
          <div>
            <span className="eyebrow">Realtime Build</span>
            <h2>Voice, Chroma memory, external skills, and dashboard live wiring</h2>
          </div>
          <div className="hero-metrics">
            <div className="metric-tile">
              <Gauge size={18} />
              <div>
                <span>Chat Socket</span>
                <strong>{connectionStatus}</strong>
              </div>
            </div>
            <div className="metric-tile">
              <Activity size={18} />
              <div>
                <span>Voice State</span>
                <strong>{voiceState}</strong>
              </div>
            </div>
          </div>
        </header>

        <section className="status-grid" aria-label="System status">
          {statusCards.map((card) => (
            <StatusCard key={card.label} {...card} />
          ))}
        </section>

        <ChatShell
          connectionStatus={connectionStatus}
          draft={draft}
          isPending={isPending}
          messages={messages}
          onSend={sendMessage}
          onVoiceToggle={toggleListening}
          setDraft={setDraft}
          voiceState={voiceState}
        />

        <section className="telemetry-grid">
          {telemetry.map((item) => (
            <article key={item.label} className="panel telemetry-card">
              <item.icon size={18} />
              <span className="eyebrow">{item.label}</span>
              <strong>{item.label}</strong>
              <p>{item.detail}</p>
            </article>
          ))}
        </section>
      </section>

      <aside className="right-rail">
        <section className="panel" id="skills">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Skill Registry</span>
              <h2>Loaded Modules</h2>
            </div>
          </div>
          <div className="stack-list">
            {skills.map((skill) => (
              <article key={skill.name} className="list-card">
                <div className="list-row">
                  <strong>{skill.name}</strong>
                  <button
                    className={`status-chip ${skill.enabled ? "online" : "idle"}`}
                    type="button"
                    onClick={() => void toggleSkill(skill.name, skill.enabled)}
                  >
                    {skill.enabled ? "enabled" : "disabled"}
                  </button>
                </div>
                <p>{skill.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel" id="activity">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Execution Trace</span>
              <h2>Recent Work</h2>
            </div>
          </div>
          <ol className="timeline">
            {events.map((event) => (
              <li key={`${event.timestamp}-${event.type}`}>
                <strong>{event.type}</strong>: {JSON.stringify(event.payload)}
              </li>
            ))}
          </ol>
        </section>

        <section className="panel" id="config">
          <span className="eyebrow">Config Overview</span>
          <div className="config-grid">
            <div className="config-item">
              <span>Primary Model</span>
              <strong>mistral-nemo:12b</strong>
            </div>
            <div className="config-item">
              <span>Voice Socket</span>
              <strong>{voiceConnectionStatus}</strong>
            </div>
            <div className="config-item">
              <span>Locale</span>
              <strong>pt-BR</strong>
            </div>
            <div className="config-item">
              <span>Transport</span>
              <strong>REST + SSE + WS</strong>
            </div>
          </div>
        </section>
      </aside>
    </main>
  );
}
