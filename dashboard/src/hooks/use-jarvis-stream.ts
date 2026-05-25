"use client";

import { startTransition, useCallback, useEffect, useRef, useState } from "react";
import { useConversationStore } from "@/lib/conversation-store";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type ConnectionStatus = "connecting" | "connected" | "disconnected";

export function useJarvisStream(conversationId: string) {
  const [draft, setDraft] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectDelayRef = useRef(500);
  const reconnectTimerRef = useRef<number | null>(null);
  const pendingAssistantIdRef = useRef<string | null>(null);
  // Keep conversationId in a ref so WebSocket callbacks don't recreate on conversation switch
  const conversationIdRef = useRef(conversationId);
  conversationIdRef.current = conversationId;

  const conversations = useConversationStore((s) => s.conversations);
  const messages: ChatMessage[] = (
    conversations.find((c) => c.id === conversationId)?.messages ?? []
  ).map(({ id, role, content }) => ({ id, role, content }));

  const appendUserMessage = useCallback((content: string) => {
    const convId = conversationIdRef.current;
    const userMsgId = `user-${Date.now()}`;
    const assistantId = `assistant-${Date.now() + 1}`;
    pendingAssistantIdRef.current = assistantId;

    const { conversations: convs, setTitle, addMessage } = useConversationStore.getState();
    const conv = convs.find((c) => c.id === convId);
    const hasUserMessages = conv?.messages.some((m) => m.role === "user") ?? false;
    if (!hasUserMessages) {
      setTitle(convId, content.slice(0, 45).trim());
    }

    addMessage(convId, { id: userMsgId, role: "user", content });
    addMessage(convId, { id: assistantId, role: "assistant", content: "" });
    setIsPending(true);
  }, []);

  const appendAssistantChunk = useCallback((chunk: string, assistantId?: string) => {
    const targetId = assistantId ?? pendingAssistantIdRef.current;
    if (!targetId) return;

    const convId = conversationIdRef.current;
    startTransition(() => {
      const { conversations: convs, updateMessage } = useConversationStore.getState();
      const conv = convs.find((c) => c.id === convId);
      const msg = conv?.messages.find((m) => m.id === targetId);
      const current = msg?.content ?? "";
      updateMessage(convId, targetId, current ? `${current} ${chunk}` : chunk);
    });
  }, []);

  const completeAssistantMessage = useCallback((finalText?: string, assistantId?: string) => {
    const targetId = assistantId ?? pendingAssistantIdRef.current;
    const convId = conversationIdRef.current;

    if (targetId && finalText?.trim()) {
      const { conversations: convs, updateMessage } = useConversationStore.getState();
      const conv = convs.find((c) => c.id === convId);
      const msg = conv?.messages.find((m) => m.id === targetId);
      if (!msg?.content.trim()) {
        updateMessage(convId, targetId, finalText.trim());
      }
    }

    if (pendingAssistantIdRef.current === targetId) {
      pendingAssistantIdRef.current = null;
    }
    setIsPending(false);
  }, []);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

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
    if (!trimmedDraft) return;

    const convId = conversationIdRef.current;

    if (socketRef.current?.readyState !== WebSocket.OPEN) {
      useConversationStore.getState().addMessage(convId, {
        id: `assistant-error-${Date.now()}`,
        role: "assistant",
        content: "Chat websocket is disconnected. Wait for reconnection and try again.",
      });
      return;
    }

    appendUserMessage(trimmedDraft);
    setDraft("");
    socketRef.current.send(
      JSON.stringify({
        session_id: convId,
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
