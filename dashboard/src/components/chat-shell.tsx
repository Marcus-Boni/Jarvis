"use client";

import { useEffect, useRef } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowUp, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/hooks/use-jarvis-stream";
import { VoiceButton } from "@/components/voice-button";

type ChatShellProps = {
  connectionStatus: "connecting" | "connected" | "disconnected";
  draft: string;
  isPending: boolean;
  messages: ChatMessage[];
  onSend: () => Promise<void>;
  setDraft: (draft: string) => void;
  voiceState: "idle" | "listening" | "processing" | "speaking";
  onVoiceToggle: () => void | Promise<void>;
};

const CONNECTION_CONFIG: Record<
  string,
  { label: string; dotClass: string }
> = {
  connected: {
    label: "online",
    dotClass: "bg-status-success shadow-[0_0_5px_rgba(52,211,153,0.7)]",
  },
  connecting: {
    label: "conectando…",
    dotClass: "bg-status-warning animate-pulse",
  },
  disconnected: {
    label: "desconectado",
    dotClass: "bg-status-danger",
  },
};

export function ChatShell({
  connectionStatus,
  draft,
  isPending,
  messages,
  onSend,
  onVoiceToggle,
  setDraft,
  voiceState,
}: ChatShellProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  });

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void onSend();
    }
  };

  const conn = CONNECTION_CONFIG[connectionStatus] ?? CONNECTION_CONFIG.disconnected;
  const canSend = !isPending && draft.trim().length > 0;

  return (
    <div className="flex flex-col flex-1 glass-panel rounded-lg overflow-hidden min-h-0">
      {/* Header */}
      <header className="flex items-center justify-between px-4 h-12 border-b border-border shrink-0">
        <div className="flex items-center gap-2.5">
          <span className={cn("w-2 h-2 rounded-full shrink-0", conn.dotClass)} aria-hidden="true" />
          <span className="text-sm font-semibold text-text-primary">Jarvis</span>
          <span className="text-xs text-text-muted font-mono">chat</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-text-muted">
            {new Date().toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" })}
          </span>
          <span
            className={cn(
              "text-xs px-2 py-0.5 rounded font-mono border",
              connectionStatus === "connected"
                ? "text-status-success bg-status-success-soft border-status-success/20"
                : connectionStatus === "connecting"
                  ? "text-status-warning bg-status-warning-soft border-status-warning/20"
                  : "text-status-danger bg-status-danger-soft border-status-danger/20"
            )}
          >
            {conn.label}
          </span>
        </div>
      </header>

      {/* Messages */}
      <div
        role="log"
        aria-live="polite"
        aria-label="Histórico de mensagens"
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0"
      >
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
              className={cn(
                "flex items-end gap-2.5",
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              {/* Avatar */}
              <div
                aria-hidden="true"
                className={cn(
                  "flex items-center justify-center w-7 h-7 rounded-full text-2xs font-bold shrink-0",
                  message.role === "user"
                    ? "bg-accent/15 text-accent border border-accent/30"
                    : "bg-bg-elevated text-text-muted border border-border"
                )}
              >
                {message.role === "user" ? "V" : "J"}
              </div>

              {/* Bubble */}
              <article
                className={cn(
                  "max-w-[75%] px-3.5 py-2.5 rounded-xl text-sm leading-relaxed",
                  message.role === "user"
                    ? "bg-accent/10 border border-accent/20 text-text-primary rounded-br-sm"
                    : "bg-bg-elevated border border-border text-text-primary rounded-bl-sm"
                )}
              >
                {message.content ? (
                  <p className="whitespace-pre-wrap break-words m-0">{message.content}</p>
                ) : isPending && message.role === "assistant" ? (
                  <span className="flex items-center gap-1 h-4">
                    {[0, 0.2, 0.4].map((delay) => (
                      <span
                        key={delay}
                        className="w-1.5 h-1.5 rounded-full bg-accent/60 animate-[typingDot_1.4s_ease-in-out_infinite]"
                        style={{ animationDelay: `${delay}s` }}
                      />
                    ))}
                  </span>
                ) : null}
              </article>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div className="shrink-0 border-t border-border px-4 py-3">
        <div className="flex items-end gap-2">
          <VoiceButton onClick={onVoiceToggle} state={voiceState} />
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              id="jarvis-input"
              name="jarvis-input"
              rows={1}
              value={draft}
              onChange={(e) => {
                setDraft(e.target.value);
                e.target.style.height = "auto";
                const next = Math.min(e.target.scrollHeight, 160);
                e.target.style.height = `${next}px`;
                e.target.style.overflowY = next >= 160 ? "auto" : "hidden";
              }}
              onKeyDown={handleKeyDown}
              placeholder="Escreva uma tarefa, pergunta ou ação… (Enter para enviar)"
              className={cn(
                "w-full resize-none bg-bg-elevated border border-border rounded-lg",
                "px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted",
                "focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20",
                "transition-colors duration-150 min-h-[40px] max-h-40"
              )}
              style={{ height: "40px", overflowY: "hidden" }}
            />
          </div>
          <button
            type="button"
            onClick={() => void onSend()}
            disabled={!canSend}
            aria-label="Enviar mensagem"
            className={cn(
              "flex items-center justify-center w-9 h-9 rounded-lg border transition-all duration-200 shrink-0",
              canSend
                ? "bg-accent text-bg-base border-accent hover:bg-accent/90 shadow-glow-sm"
                : "bg-bg-elevated border-border text-text-muted cursor-not-allowed opacity-50"
            )}
          >
            {isPending ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <ArrowUp size={15} />
            )}
          </button>
        </div>
        <p className="mt-1.5 text-2xs text-text-muted font-mono">
          Enter para enviar · Shift+Enter para nova linha
        </p>
      </div>
    </div>
  );
}
