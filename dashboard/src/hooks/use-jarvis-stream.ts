"use client";

import { startTransition, useDeferredValue, useState } from "react";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

const starterMessages: ChatMessage[] = [
  {
    id: "assistant-boot",
    role: "assistant",
    content:
      "Jarvis foundation online. O backend já entende intenções, contexto e skill routing. As integrações reais entram nas próximas fases.",
  },
];

export function useJarvisStream() {
  const [messages, setMessages] = useState<ChatMessage[]>(starterMessages);
  const [draft, setDraft] = useState("");
  const [isPending, setIsPending] = useState(false);
  const deferredDraft = useDeferredValue(draft);

  const sendMessage = async () => {
    const trimmedDraft = draft.trim();
    if (!trimmedDraft) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmedDraft,
    };

    startTransition(() => {
      setMessages((currentMessages) => [...currentMessages, userMessage]);
      setDraft("");
      setIsPending(true);
    });

    window.setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content:
          "Este painel ainda usa uma resposta simulada. Quando o backend Python estiver ativo, o hook será conectado ao SSE/WebSocket do Jarvis.",
      };
      startTransition(() => {
        setMessages((currentMessages) => [...currentMessages, assistantMessage]);
        setIsPending(false);
      });
    }, 450);
  };

  return {
    draft,
    deferredDraft,
    isPending,
    messages,
    sendMessage,
    setDraft,
  };
}

