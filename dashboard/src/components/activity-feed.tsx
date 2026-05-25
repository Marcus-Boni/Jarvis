"use client";

import { useState } from "react";

import {
  CheckCircle2,
  ChevronRight,
  Clock,
  MessageSquare,
  XCircle,
  Zap,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { DetailModal } from "@/components/detail-modal";

type RuntimeEvent = {
  payload: Record<string, unknown>;
  timestamp: string;
  type: string;
};

type ActivityFeedProps = {
  events: RuntimeEvent[];
};

type ParsedEvent = {
  dotClass: string;
  icon: typeof Zap;
  iconClass: string;
  title: string;
  detail: string | null;
};

function parseEvent(event: RuntimeEvent): ParsedEvent {
  const { type, payload } = event;

  if (type === "skill") {
    const name = typeof payload.skill_name === "string" ? payload.skill_name : "skill";
    const success = payload.success !== false;
    return {
      icon: success ? CheckCircle2 : XCircle,
      iconClass: success ? "text-status-success" : "text-status-danger",
      title: name,
      detail: success ? "executado com sucesso" : "falhou na execução",
      dotClass: success
        ? "bg-status-success shadow-[0_0_4px_rgba(52,211,153,0.5)]"
        : "bg-status-danger shadow-[0_0_4px_rgba(251,113,133,0.5)]",
    };
  }

  if (type === "chat") {
    const intent = typeof payload.intent === "string" ? payload.intent : null;
    const fallback = payload.used_fallback_llm === true;
    return {
      icon: MessageSquare,
      iconClass: "text-accent",
      title: intent ? `chat · ${intent}` : "chat",
      detail: fallback ? "via LLM fallback" : "via skill",
      dotClass: "bg-accent/70",
    };
  }

  if (type === "activity") {
    const msg = typeof payload.message === "string" ? payload.message : null;
    const comp = typeof payload.component === "string" ? payload.component : null;
    return {
      icon: Zap,
      iconClass: "text-status-warning",
      title: comp ?? "atividade",
      detail: msg,
      dotClass: "bg-status-warning/70",
    };
  }

  return {
    icon: Zap,
    iconClass: "text-text-muted",
    title: type,
    detail: Object.keys(payload).length > 0 ? JSON.stringify(payload) : null,
    dotClass: "bg-text-muted/50",
  };
}

export function ActivityFeed({ events }: ActivityFeedProps) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  const visible = events.slice(-20).reverse();
  const selected = selectedIdx !== null ? visible[selectedIdx] ?? null : null;

  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
        <Zap size={18} className="text-text-muted opacity-30" />
        <p className="text-xs text-text-muted">Nenhuma atividade ainda.</p>
      </div>
    );
  }

  return (
    <>
      <ol className="space-y-0">
        {visible.map((event, idx) => {
          const parsed = parseEvent(event);
          const Icon = parsed.icon;
          return (
            <li key={`${event.timestamp}-${event.type}-${idx}`}>
              <button
                type="button"
                onClick={() => setSelectedIdx(idx)}
                className="flex gap-3 w-full px-4 py-3 border-b border-border/50 last:border-0 hover:bg-bg-hover/30 active:bg-bg-hover/50 transition-colors group text-left"
                aria-label={`Ver detalhes do evento ${parsed.title}`}
              >
                {/* Status dot */}
                <div
                  aria-hidden="true"
                  className={cn("shrink-0 w-1.5 h-1.5 rounded-full mt-1.5", parsed.dotClass)}
                />

                <div className="min-w-0 flex-1">
                  {/* Title row */}
                  <div className="flex items-center gap-1.5">
                    <Icon size={11} className={cn("shrink-0", parsed.iconClass)} aria-hidden="true" />
                    <p className="text-xs font-semibold text-text-primary font-mono truncate">
                      {parsed.title}
                    </p>
                  </div>

                  {/* Detail snippet */}
                  {parsed.detail && (
                    <p className="text-2xs text-text-secondary mt-0.5 leading-snug line-clamp-1">
                      {parsed.detail}
                    </p>
                  )}

                  {/* Timestamp */}
                  <p className="text-2xs text-text-muted font-mono mt-0.5">
                    {new Date(event.timestamp).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </p>
                </div>

                {/* Chevron */}
                <ChevronRight
                  size={12}
                  className="shrink-0 self-center text-text-muted opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-hidden="true"
                />
              </button>
            </li>
          );
        })}
      </ol>

      {/* Detail modal */}
      <DetailModal
        open={!!selected}
        onClose={() => setSelectedIdx(null)}
        title={selected ? parseEvent(selected).title : ""}
        subtitle={`Tipo: ${selected?.type ?? ""}`}
      >
        {selected && <EventDetail event={selected} />}
      </DetailModal>
    </>
  );
}

/* ── Event detail content ── */

const FIELD_LABELS: Record<string, string> = {
  skill_name: "Módulo",
  success: "Sucesso",
  session_id: "Sessão",
  intent: "Intenção",
  used_fallback_llm: "Usou LLM fallback",
  component: "Componente",
  message: "Mensagem",
};

function formatValue(_key: string, value: unknown): string {
  if (typeof value === "boolean") return value ? "sim" : "não";
  if (value === null || value === undefined) return "—";
  return String(value);
}

function EventDetail({ event }: { event: RuntimeEvent }) {
  const parsed = parseEvent(event);
  const Icon = parsed.icon;
  const isSkill = event.type === "skill";
  const success = event.payload.success !== false;

  return (
    <div className="divide-y divide-border/50">
      {/* Status banner */}
      <div className="px-4 py-3">
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg text-xs border",
            isSkill && success
              ? "bg-status-success-soft border-status-success/20 text-status-success"
              : isSkill && !success
                ? "bg-status-danger-soft border-status-danger/20 text-status-danger"
                : event.type === "chat"
                  ? "bg-accent/10 border-accent/20 text-accent"
                  : "bg-status-warning-soft border-status-warning/20 text-status-warning"
          )}
        >
          <Icon size={12} className="shrink-0" aria-hidden="true" />
          <span className="font-mono font-medium">{parsed.detail ?? parsed.title}</span>
        </div>
      </div>

      {/* Timestamp */}
      <div className="px-4 py-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <Clock size={11} className="text-text-muted" aria-hidden="true" />
          <p className="text-2xs font-mono uppercase tracking-wider text-text-muted">Horário</p>
        </div>
        <p className="text-sm text-text-primary font-mono">
          {new Date(event.timestamp).toLocaleString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })}
        </p>
      </div>

      {/* Payload fields */}
      {Object.keys(event.payload).length > 0 && (
        <div className="px-4 py-3">
          <p className="text-2xs font-mono uppercase tracking-wider text-text-muted mb-3">
            Dados do evento
          </p>
          <dl className="space-y-2">
            {Object.entries(event.payload).map(([key, value]) => (
              <div key={key} className="flex items-start gap-3">
                <dt className="text-2xs font-mono text-text-muted shrink-0 w-28 pt-px">
                  {FIELD_LABELS[key] ?? key}
                </dt>
                <dd
                  className={cn(
                    "text-2xs font-mono break-all",
                    key === "success"
                      ? value !== false
                        ? "text-status-success"
                        : "text-status-danger"
                      : "text-text-primary"
                  )}
                >
                  {formatValue(key, value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Raw type badge */}
      <div className="px-4 py-3">
        <p className="text-2xs font-mono uppercase tracking-wider text-text-muted mb-1.5">
          Tipo de evento
        </p>
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-2xs font-mono bg-bg-elevated border border-border text-text-secondary">
          {event.type}
        </span>
      </div>
    </div>
  );
}
