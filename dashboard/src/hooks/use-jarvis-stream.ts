"use client";

import { startTransition, useCallback, useEffect, useRef, useState } from "react";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type ConnectionStatus = "connecting" | "connected" | "disconnected";

const starterMessages: ChatMessage[] = [
  {
    id: "assistant-boot",
    role: "assistant",
    content:
      "Jarvis live routing online. Text chat uses the backend websocket and voice can stream through the realtime pipeline.",
  },
];

export function useJarvisStream() {
  const [messages, setMessages] = useState<ChatMessage[]>(starterMessages);
  const [draft, setDraft] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectDelayRef = useRef(500);
  const reconnectTimerRef = useRef<number | null>(null);
  const pendingAssistantIdRef = useRef<string | null>(null);

  const appendUserMessage = useCallback((content: string) => {
    const assistantId = `assistant-${Date.now()}`;
    pendingAssistantIdRef.current = assistantId;
    setMessages((currentMessages) => [
      ...currentMessages,
      { id: `user-${Date.now()}`, role: "user", content },
      { id: assistantId, role: "assistant", content: "" },
    ]);
    setIsPending(true);
  }, []);

  const appendAssistantChunk = useCallback((chunk: string, assistantId?: string) => {
    const targetAssistantId = assistantId ?? pendingAssistantIdRef.current;
    if (!targetAssistantId) {
      return;
    }

    startTransition(() => {
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === targetAssistantId
            ? {
                ...message,
                content: message.content ? `${message.content} ${chunk}` : chunk,
              }
            : message
        )
      );
    });
  }, []);

  const completeAssistantMessage = useCallback((finalText?: string, assistantId?: string) => {
    const targetAssistantId = assistantId ?? pendingAssistantIdRef.current;
    if (targetAssistantId && finalText?.trim()) {
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === targetAssistantId && !message.content.trim()
            ? { ...message, content: finalText.trim() }
            : message
        )
      );
    }

    if (pendingAssistantIdRef.current === targetAssistantId) {
      pendingAssistantIdRef.current = null;
    }
    setIsPending(false);
  }, []);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus("connecting");
    const socket = new WebSocket("ws://localhost:8000/ws/chat");
    socketRef.current = socket;

    socket.onopen = () => {
      reconnectDelayRef.current = 500;
      setConnectionStatus("connected");
    };

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { type: string; text?: string };
      const assistantId = pendingAssistantIdRef.current;
      if (payload.type === "chunk" && payload.text) {
        appendAssistantChunk(payload.text, assistantId ?? undefined);
      }
      if (payload.type === "error" && payload.text) {
        appendAssistantChunk(payload.text, assistantId ?? undefined);
      }
      if (payload.type === "done") {
        completeAssistantMessage(payload.text, assistantId ?? undefined);
      }
    };

    socket.onclose = () => {
      setConnectionStatus("disconnected");
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      reconnectTimerRef.current = window.setTimeout(() => {
        connect();
      }, reconnectDelayRef.current);
      reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 8000);
    };
  }, [appendAssistantChunk, completeAssistantMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback(async () => {
    const trimmedDraft = draft.trim();
    if (!trimmedDraft) {
      return;
    }

    if (socketRef.current?.readyState !== WebSocket.OPEN) {
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: "Chat websocket is disconnected. Wait for reconnection and try again.",
        },
      ]);
      return;
    }

    appendUserMessage(trimmedDraft);
    setDraft("");
    socketRef.current.send(
      JSON.stringify({
        session_id: "dashboard-session",
        locale: "pt-BR",
        message: trimmedDraft,
      })
    );
  }, [appendUserMessage, draft]);

  return {
    appendAssistantChunk,
    appendUserMessage,
    completeAssistantMessage,
    connectionStatus,
    draft,
    isPending,
    messages,
    sendMessage,
    setDraft,
  };
}
