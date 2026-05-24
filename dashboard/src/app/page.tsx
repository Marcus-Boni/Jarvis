"use client";

import { useEffect, useMemo, useState } from "react";

import { AppNav } from "@/components/app-nav";
import { ChatShell } from "@/components/chat-shell";
import { StatusCard } from "@/components/status-card";
import { useJarvisEvents } from "@/hooks/use-jarvis-events";
import { useJarvisStream } from "@/hooks/use-jarvis-stream";
import { useJarvisVoice } from "@/hooks/use-jarvis-voice";
import { API_BASE_URL, apiFetch } from "@/lib/api";

type StatusTone = "success" | "warning" | "info" | "default";

type SkillStatus = {
  description: string;
  enabled: boolean;
  name: string;
  triggers: string[];
};

type HealthPayload = {
  loaded_skills: string[];
  model?: string;
  ollama_reachable: boolean;
  status: string;
  voice_active: boolean;
};

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
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [healthResponse, skillsResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/health`),
          apiFetch("/api/skills"),
        ]);
        const nextHealth = (await healthResponse.json()) as HealthPayload;
        const nextSkills = (await skillsResponse.json()) as { items?: SkillStatus[] };
        setHealth(nextHealth);
        setSkills(Array.isArray(nextSkills.items) ? nextSkills.items : []);
        setLoadError(null);
      } catch (error) {
        setHealth(null);
        setSkills([]);
        setLoadError(error instanceof Error ? error.message : "Failed to load dashboard data.");
      }
    };
    void loadData();
  }, []);

  const statusCards = useMemo(
    () => [
      {
        label: "Modelo",
        value: health?.model ?? (health?.ollama_reachable ? "Reachable" : "Offline"),
        detail: health?.ollama_reachable ? "Ollama respondeu ao health check" : "Backend não consegue alcançar Ollama",
        tone: (health?.ollama_reachable ? "success" : "warning") as StatusTone,
      },
      {
        label: "Memória",
        value: "ChromaDB",
        detail: "Memória vetorial persistente com busca semântica.",
        tone: "info" as StatusTone,
      },
      {
        label: "Voz",
        value: voiceState,
        detail: `Socket de voz ${voiceConnectionStatus}.`,
        tone: (voiceState === "idle" ? "default" : "success") as StatusTone,
      },
      {
        label: "Skills",
        value: `${skills.filter((s) => s.enabled).length} / ${skills.length}`,
        detail: "Módulos ativos carregados do registry.",
        tone: "default" as StatusTone,
      },
    ],
    [health, skills, voiceConnectionStatus, voiceState]
  );

  const toggleSkill = async (skillName: string, enabled: boolean) => {
    try {
      await apiFetch(`/api/skills/${skillName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !enabled }),
      });
      setSkills((current) =>
        current.map((s) => (s.name === skillName ? { ...s, enabled: !enabled } : s))
      );
      setLoadError(null);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Failed to update skill.");
    }
  };

  return (
    <main className="app-shell">
      <aside className="left-rail panel">
        <div className="rail-header">
          <span className="eyebrow">Jarvis</span>
          <h1>Painel de Controle</h1>
          <p>Modelos locais, memória, voz e skills de sistema.</p>
        </div>
        <AppNav />
        <section className="rail-meter">
          <div>
            <span className="eyebrow">Runtime</span>
            <strong>{health?.status === "ok" ? "Online" : "Verificando…"}</strong>
          </div>
          <div className="meter-track" aria-hidden="true">
            <span className="meter-fill" />
          </div>
          <p>{health?.model ? `Modelo ativo: ${health.model}` : "Aguardando backend…"}</p>
        </section>
      </aside>

      <section className="workspace" id="workspace">
        <section className="status-grid" aria-label="Status do sistema">
          {statusCards.map((card) => (
            <StatusCard key={card.label} {...card} />
          ))}
        </section>

        {loadError ? <p className="panel error-banner">{loadError}</p> : null}

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
      </section>

      <aside className="right-rail">
        <section className="panel" id="config">
          <span className="eyebrow">Configuração</span>
          <div className="config-grid">
            <div className="config-item">
              <span>Modelo</span>
              <strong>{health?.model ?? "—"}</strong>
            </div>
            <div className="config-item">
              <span>Voz</span>
              <strong>{voiceConnectionStatus}</strong>
            </div>
            <div className="config-item">
              <span>Idioma</span>
              <strong>pt-BR</strong>
            </div>
            <div className="config-item">
              <span>Transporte</span>
              <strong>WS + REST</strong>
            </div>
          </div>
        </section>

        <section className="panel" id="skills">
          <div className="panel-header">
            <div>
              <span className="eyebrow">Skills</span>
              <h2>Módulos</h2>
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
                    {skill.enabled ? "ativo" : "inativo"}
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
              <span className="eyebrow">Trace</span>
              <h2>Atividade Recente</h2>
            </div>
          </div>
          <ol className="timeline">
            {events.length === 0 ? (
              <li className="timeline-empty">Nenhuma atividade ainda.</li>
            ) : (
              events.slice(-10).map((event) => (
                <li key={`${event.timestamp}-${event.type}`}>
                  <strong>{event.type}</strong>: {JSON.stringify(event.payload)}
                </li>
              ))
            )}
          </ol>
        </section>
      </aside>
    </main>
  );
}
