import { Activity, BrainCircuit, DatabaseZap, Gauge, RadioTower, ShieldCheck } from "lucide-react";

import { ChatShell } from "@/components/chat-shell";
import { StatusCard } from "@/components/status-card";
import { activityItems, skillItems, statusCards } from "@/lib/demo-data";

const telemetry = [
  { icon: BrainCircuit, label: "Intent Engine", value: "Active", detail: "Zero-shot + structured JSON" },
  { icon: DatabaseZap, label: "Memory Layer", value: "Staged", detail: "Conversation store + retriever interface" },
  { icon: RadioTower, label: "Voice Loop", value: "Pending", detail: "VAD, STT and TTS land in Phase 1" },
  { icon: ShieldCheck, label: "Safety", value: "Guarded", detail: "No destructive OS actions without explicit flow" },
];

export default function HomePage() {
  return (
    <main className="app-shell">
      <aside className="left-rail panel">
        <div className="rail-header">
          <span className="eyebrow">Jarvis</span>
          <h1>Local Control Room</h1>
          <p>Assistente pessoal local para voz, automação, contexto e execução segura.</p>
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
            <strong>Phase 0 online</strong>
          </div>
          <div className="meter-track" aria-hidden="true">
            <span className="meter-fill" />
          </div>
          <p>Core, API e dashboard base estão prontos para a próxima rodada de integrações.</p>
        </section>
      </aside>

      <section className="workspace" id="workspace">
        <header className="hero panel">
          <div>
            <span className="eyebrow">Foundation Build</span>
            <h2>FastAPI, orchestration, memory scaffolding and dashboard shell</h2>
          </div>
          <div className="hero-metrics">
            <div className="metric-tile">
              <Gauge size={18} />
              <div>
                <span>Latency Strategy</span>
                <strong>Async-first I/O</strong>
              </div>
            </div>
            <div className="metric-tile">
              <Activity size={18} />
              <div>
                <span>Current Phase</span>
                <strong>Foundation</strong>
              </div>
            </div>
          </div>
        </header>

        <section className="status-grid" aria-label="System status">
          {statusCards.map((card) => (
            <StatusCard key={card.label} {...card} />
          ))}
        </section>

        <ChatShell />

        <section className="telemetry-grid">
          {telemetry.map((item) => (
            <article key={item.label} className="panel telemetry-card">
              <item.icon size={18} />
              <span className="eyebrow">{item.label}</span>
              <strong>{item.value}</strong>
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
            {skillItems.map((skill) => (
              <article key={skill.name} className="list-card">
                <div className="list-row">
                  <strong>{skill.name}</strong>
                  <span className="status-chip idle">{skill.state}</span>
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
            {activityItems.map((item) => (
              <li key={item}>{item}</li>
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
              <span>Fallback</span>
              <strong>phi3:mini</strong>
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

