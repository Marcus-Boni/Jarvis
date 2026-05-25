"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type ConversationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
};

export type Conversation = {
  id: string;
  title: string;
  messages: ConversationMessage[];
  createdAt: number;
  updatedAt: number;
};

type ConversationStore = {
  conversations: Conversation[];
  activeId: string;
  newConversation: () => string;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  addMessage: (convId: string, msg: Omit<ConversationMessage, "timestamp">) => void;
  updateMessage: (convId: string, msgId: string, content: string) => void;
  setTitle: (convId: string, title: string) => void;
};

function makeId() {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function makeConversation(): Conversation {
  const now = Date.now();
  return {
    id: makeId(),
    title: "Nova conversa",
    messages: [
      {
        id: "assistant-boot",
        role: "assistant",
        content:
          "Jarvis live routing online. Text chat uses the backend websocket and voice can stream through the realtime pipeline.",
        timestamp: now,
      },
    ],
    createdAt: now,
    updatedAt: now,
  };
}

const initial = makeConversation();

export const useConversationStore = create<ConversationStore>()(
  persist(
    (set) => ({
      conversations: [initial],
      activeId: initial.id,

      newConversation() {
        const conv = makeConversation();
        set((s) => ({ conversations: [conv, ...s.conversations], activeId: conv.id }));
        return conv.id;
      },

      selectConversation(id) {
        set({ activeId: id });
      },

      deleteConversation(id) {
        set((s) => {
          const next = s.conversations.filter((c) => c.id !== id);
          if (next.length === 0) {
            const conv = makeConversation();
            return { conversations: [conv], activeId: conv.id };
          }
          return {
            conversations: next,
            activeId: s.activeId === id ? next[0].id : s.activeId,
          };
        });
      },

      addMessage(convId, msg) {
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: [...c.messages, { ...msg, timestamp: Date.now() }],
                  updatedAt: Date.now(),
                }
              : c
          ),
        }));
      },

      updateMessage(convId, msgId, content) {
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === convId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === msgId ? { ...m, content } : m
                  ),
                  updatedAt: Date.now(),
                }
              : c
          ),
        }));
      },

      setTitle(convId, title) {
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === convId ? { ...c, title } : c
          ),
        }));
      },
    }),
    {
      name: "jarvis-conversations",
      storage: createJSONStorage(() => localStorage),
    }
  )
);
