"use client";

import { ArrowUpRight, LoaderCircle, Sparkles } from "lucide-react";

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
  return (
    <section className="panel chat-shell">
      <div className="panel-header">
        <div>
          <span className="eyebrow">Primary Workspace</span>
          <h2>Command Conversation</h2>
        </div>
        <div className={`status-chip ${connectionStatus === "connected" ? "online" : "idle"}`}>
          <Sparkles size={14} />
          <span>{connectionStatus}</span>
        </div>
      </div>

      <div className="message-stack" aria-live="polite">
        {messages.map((message) => (
          <article key={message.id} className={`message-bubble ${message.role}`}>
            <span className="message-role">{message.role === "assistant" ? "Jarvis" : "You"}</span>
            <p>{message.content || (isPending && message.role === "assistant" ? "..." : "")}</p>
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
            placeholder="Describe a task, ask a technical question, or launch a local action."
            rows={4}
          />
          <span className="composer-hint">
            Live backend websocket + realtime voice pipeline.
          </span>
        </label>

        <div className="composer-actions">
          <VoiceButton onClick={onVoiceToggle} state={voiceState} />
          <button className="primary-button" type="button" onClick={() => void onSend()}>
            {isPending ? <LoaderCircle className="spin" size={16} /> : <ArrowUpRight size={16} />}
            <span>{isPending ? "Responding" : "Send"}</span>
          </button>
        </div>
      </div>
    </section>
  );
}

