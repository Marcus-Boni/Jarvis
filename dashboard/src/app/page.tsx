"use client";

import { useEffect, useMemo, useState } from "react";

import { motion } from "framer-motion";
import { AlertCircle, Cpu, Database, Layers, Mic } from "lucide-react";

import { API_BASE_URL, apiFetch } from "@/lib/api";
import { useConversationStore } from "@/lib/conversation-store";
import { useJarvisEvents } from "@/hooks/use-jarvis-events";
import { useJarvisStream } from "@/hooks/use-jarvis-stream";
import { useJarvisVoice } from "@/hooks/use-jarvis-voice";
import { ActivityFeed } from "@/components/activity-feed";
import { AppLayout } from "@/components/app-layout";
import { ChatShell } from "@/components/chat-shell";
import { CollapsibleSection } from "@/components/collapsible-section";
import { SkillList } from "@/components/skill-list";
import { StatusCard, type StatusTone } from "@/components/status-card";

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
  const activeId = useConversationStore((s) => s.activeId);

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
  } = useJarvisStream(activeId);

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
        setLoadError(error instanceof Error ? error.message : "Falha ao carregar dados.");
      }
    };
    void loadData();
  }, []);

  const statusCards = useMemo(
    () => [
      {
        icon: Cpu,
        label: "Modelo",
        value: health?.model ?? (health?.ollama_reachable ? "Acessível" : "Offline"),
        detail: health?.ollama_reachable
          ? "Ollama respondeu ao health check"
          : "Backend não alcança o Ollama",
        tone: (health?.ollama_reachable ? "success" : "warning") as StatusTone,
      },
      {
        icon: Database,
        label: "Memória",
        value: "ChromaDB",
        detail: "Memória vetorial persistente com busca semântica",
        tone: "info" as StatusTone,
      },
      {
        icon: Mic,
        label: "Voz",
        value: voiceState === "idle" ? "ocioso" : voiceState,
        detail: `Socket de voz ${voiceConnectionStatus === "connected" ? "conectado" : voiceConnectionStatus}`,
        tone: (voiceState === "idle" ? "default" : "success") as StatusTone,
      },
      {
        icon: Layers,
        label: "Skills",
        value: `${skills.filter((s) => s.enabled).length} / ${skills.length}`,
        detail: "Módulos ativos carregados do registry",
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
      setLoadError(error instanceof Error ? error.message : "Falha ao atualizar módulo.");
    }
  };

  /* ── Right panel (shared between desktop aside and mobile drawer) ── */
  const rightPanelContent = (
    <>
      {/* Config info */}
      <CollapsibleSection title="Configuração" defaultOpen>
        <div className="grid grid-cols-2 gap-px bg-border/50 overflow-hidden rounded-b-lg">
          {[
            { label: "Modelo", value: health?.model ?? "—" },
            {
              label: "Voz",
              value:
                voiceConnectionStatus === "connected" ? "conectada" : voiceConnectionStatus,
            },
            { label: "Idioma", value: "pt-BR" },
            { label: "Transporte", value: "WS + REST" },
          ].map(({ label, value }) => (
            <div key={label} className="bg-bg-card px-3 py-2.5">
              <p className="text-2xs font-mono uppercase tracking-wider text-text-muted mb-1">
                {label}
              </p>
              <p className="text-xs font-semibold text-text-primary truncate">{value}</p>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Skills */}
      <CollapsibleSection
        title="Módulos"
        badge={`${skills.filter((s) => s.enabled).length}/${skills.length}`}
        defaultOpen
      >
        <div className="max-h-60 overflow-y-auto">
          <SkillList
            skills={skills}
            onToggle={(name, enabled) => void toggleSkill(name, enabled)}
          />
        </div>
      </CollapsibleSection>

      {/* Activity */}
      <CollapsibleSection
        title="Atividade"
        badge={events.length > 0 ? events.length : undefined}
        defaultOpen={false}
      >
        <ActivityFeed events={events} />
      </CollapsibleSection>
    </>
  );

  return (
    <AppLayout rightPanel={rightPanelContent} mainOverflowHidden>
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28, ease: [0.2, 0.8, 0.2, 1] }}
        className="flex flex-col flex-1 gap-3 min-h-0 overflow-hidden"
      >
        {/* Status cards */}
        <CollapsibleSection title="Status do Sistema" defaultOpen className="shrink-0">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 p-3">
            {statusCards.map((card) => (
              <StatusCard key={card.label} {...card} />
            ))}
          </div>
        </CollapsibleSection>

        {/* Error banner */}
        {loadError && (
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg
            bg-status-danger-soft border border-status-danger/20 text-status-danger text-xs shrink-0">
            <AlertCircle size={14} className="shrink-0" />
            <span>{loadError}</span>
          </div>
        )}

        {/* Chat — fills remaining height */}
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
      </motion.div>
    </AppLayout>
  );
}
