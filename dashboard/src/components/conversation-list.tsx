"use client";

import { useState } from "react";
import { MessageSquare, MessageSquarePlus, Plus, Trash2 } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useConversationStore } from "@/lib/conversation-store";

function relativeTime(timestamp: number): string {
  const diff = Date.now() - timestamp;
  const m = Math.floor(diff / 60_000);
  const h = Math.floor(diff / 3_600_000);
  const d = Math.floor(diff / 86_400_000);
  if (m < 1) return "agora";
  if (m < 60) return `${m}m`;
  if (h < 24) return `${h}h`;
  return `${d}d`;
}

type Props = {
  collapsed: boolean;
};

export function ConversationList({ collapsed }: Props) {
  const { conversations, activeId, newConversation, selectConversation, deleteConversation } =
    useConversationStore();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  if (collapsed) {
    return (
      <div className="px-2 pt-2">
        <button
          onClick={() => newConversation()}
          title="Nova conversa"
          className={cn(
            "flex items-center justify-center w-full h-9 rounded-lg border border-transparent",
            "text-text-muted hover:text-accent hover:bg-accent/5 hover:border-accent/20 transition-all duration-150"
          )}
        >
          <MessageSquarePlus size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-0 overflow-hidden px-2 pt-2">
      <div className="flex items-center justify-between px-1 mb-1.5 shrink-0">
        <span className="text-2xs font-mono uppercase tracking-widest text-text-muted">
          Conversas
        </span>
        <button
          onClick={() => newConversation()}
          title="Nova conversa"
          className="p-1 rounded text-text-muted hover:text-accent hover:bg-accent/5 transition-colors"
        >
          <Plus size={13} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 space-y-0.5">
        <AnimatePresence initial={false}>
          {conversations.map((conv) => (
            <motion.div
              key={conv.id}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.15 }}
              onMouseEnter={() => setHoveredId(conv.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => selectConversation(conv.id)}
              className={cn(
                "group flex items-center gap-2 px-2 py-2 rounded-lg cursor-pointer transition-all duration-150 border",
                conv.id === activeId
                  ? "bg-accent/10 border-accent/20 text-text-primary"
                  : "border-transparent text-text-secondary hover:text-text-primary hover:bg-bg-hover"
              )}
            >
              <MessageSquare
                size={13}
                className={cn(
                  "shrink-0",
                  conv.id === activeId ? "text-accent" : "text-text-muted"
                )}
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate leading-none mb-0.5">{conv.title}</p>
                <p className="text-2xs text-text-muted font-mono">
                  {relativeTime(conv.updatedAt)}
                </p>
              </div>
              {hoveredId === conv.id && conversations.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  title="Excluir conversa"
                  className="shrink-0 p-0.5 rounded text-text-muted hover:text-status-danger transition-colors"
                >
                  <Trash2 size={11} />
                </button>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
