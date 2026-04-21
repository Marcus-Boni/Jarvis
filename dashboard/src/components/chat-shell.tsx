"use client";

import { ArrowUpRight, LoaderCircle, Mic, Sparkles } from "lucide-react";

import { useJarvisStream } from "@/hooks/use-jarvis-stream";

export function ChatShell() {
  const { deferredDraft, draft, isPending, messages, sendMessage, setDraft } = useJarvisStream();

  return (
    <section className="panel chat-shell">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Primary Workspace</span>
          <h2>Command Conversation</h2>
        </div>
        <div className="status-chip online">
          <Sparkles size={14} />
          <span>Local-first routing</span>
        </div>
      </div>

      <div className="message-stack" aria-live="polite">
        {messages.map((message) => (
          <article key={message.id} className={`message-bubble ${message.role}`}>
            <span className="message-role">{message.role === "assistant" ? "Jarvis" : "Você"}</span>
            <p>{message.content}</p>
          </article>
        ))}
      </div>

      <div className="composer">
        <label className="composer-field" htmlFor="jarvis-command">
          <textarea
            id="jarvis-command"
            name="jarvis-command"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Descreva uma tarefa, pergunte algo técnico ou simule um comando local."
            rows={4}
          />
          <span className="composer-hint">
            Draft ativo: {deferredDraft.length} caracteres.
          </span>
        </label>

        <div className="composer-actions">
          <button className="ghost-button" type="button" aria-label="Ativar modo voz">
            <Mic size={16} />
            <span>Voice</span>
          </button>
          <button className="primary-button" type="button" onClick={() => void sendMessage()}>
            {isPending ? <LoaderCircle className="spin" size={16} /> : <ArrowUpRight size={16} />}
            <span>{isPending ? "Responding" : "Send"}</span>
          </button>
        </div>
      </div>
    </section>
  );
}

