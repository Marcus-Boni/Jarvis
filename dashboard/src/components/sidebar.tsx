"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, ChevronLeft, ChevronRight, Database, LayoutDashboard, Settings2 } from "lucide-react";
import { ConversationList } from "@/components/conversation-list";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Workspace", icon: LayoutDashboard },
  { href: "/settings", label: "Configurações", icon: Settings2 },
  { href: "/memory", label: "Memória", icon: Database },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 64 : 220 }}
      transition={{ duration: 0.25, ease: [0.2, 0.8, 0.2, 1] }}
      className="relative flex flex-col shrink-0 h-screen glass-panel border-r border-border z-20"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-border shrink-0 overflow-hidden">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent/10 border border-accent/30 shrink-0">
          <Bot size={16} className="text-accent" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.18 }}
              className="overflow-hidden"
            >
              <p className="text-text-primary font-semibold text-sm leading-none">Jarvis</p>
              <p className="text-text-muted text-2xs mt-0.5 font-mono">v3.0 — local</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="shrink-0 px-2 py-3 space-y-1" aria-label="Principal">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              title={collapsed ? label : undefined}
              className={cn(
                "flex items-center gap-3 px-2.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group overflow-hidden",
                isActive
                  ? "bg-accent/10 text-accent border border-accent/20"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-hover border border-transparent"
              )}
            >
              <Icon
                size={17}
                className={cn(
                  "shrink-0 transition-colors",
                  isActive ? "text-accent" : "text-text-muted group-hover:text-text-secondary"
                )}
              />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                    className="truncate"
                  >
                    {label}
                  </motion.span>
                )}
              </AnimatePresence>
            </Link>
          );
        })}
      </nav>

      {/* Conversation history */}
      <div className="flex-1 min-h-0 overflow-hidden border-t border-border">
        <ConversationList collapsed={collapsed} />
      </div>

      {/* Collapse toggle */}
      <button
        type="button"
        onClick={() => setCollapsed((v) => !v)}
        className={cn(
          "flex items-center justify-center w-full h-12 border-t border-border shrink-0",
          "text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-colors"
        )}
        aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
      >
        {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
      </button>
    </motion.aside>
  );
}
