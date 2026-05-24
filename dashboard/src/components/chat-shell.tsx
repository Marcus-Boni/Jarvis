"use client";

import { useEffect, useRef } from "react";
import { ArrowUpRight, LoaderCircle } from "lucide-react";

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

const CONNECTION_LABEL: Record<string, string> = {
  connected: "online",
  connecting: "conectando…",
  disconnected: "desconectado",
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  });

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void onSend();
    }
  };

  const dotClass =
    connectionStatus === "connected"
      ? "conn-dot online"
      : connectionStatus === "connecting"
        ? "conn-dot pending"
        : "conn-dot offline";

  return (
    <section className="panel chat-shell">
      <header className="chat-header">
        <div className="chat-title">
          <div className={dotClass} aria-hidden="true" />
          <span>Jarvis</span>
        </div>
        <div className="chat-meta">
          <span className="chat-session">sessão · dashboard</span>
          <span className="chat-conn-label">{CONNECTION_LABEL[connectionStatus]}</span>
        </div>
      </header>

      <div role="log" aria-live="polite" className="message-stack">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`msg-row ${message.role === "user" ? "msg-row-user" : "msg-row-assistant"}`}
          >
            {message.role === "assistant" && (
              <div className="msg-avatar" aria-hidden="true">J</div>
            )}
            <article className={`message-bubble ${message.role}`}>
              <p>
                {message.content ||
                  (isPending && message.role === "assistant" ? (
                    <span className="typing-indicator">
                      <span /><span /><span />
                    </span>
                  ) : (
                    ""
                  ))}
              </p>
            </article>
            {message.role === "user" && (
              <div className="msg-avatar msg-avatar-user" aria-hidden="true">V</div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="composer">
        <textarea
          id="jarvis-command"
          name="jarvis-command"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escreva uma tarefa, pergunta ou ação… (Enter para enviar, Shift+Enter para nova linha)"
          rows={3}
        />
        <div className="composer-actions">
          <VoiceButton onClick={onVoiceToggle} state={voiceState} />
          <button
            className="primary-button"
            type="button"
            onClick={() => void onSend()}
            disabled={isPending || !draft.trim()}
          >
            {isPending ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <ArrowUpRight size={16} />
            )}
            <span>{isPending ? "Respondendo…" : "Enviar"}</span>
          </button>
        </div>
      </div>
    </section>
  );
}
