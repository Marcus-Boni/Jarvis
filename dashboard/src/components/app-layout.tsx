"use client";

import { useState } from "react";
import type { ReactNode } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, ChevronLeft, PanelRightOpen, X } from "lucide-react";

import { MobileNav } from "@/components/mobile-nav";
import { Sidebar } from "@/components/sidebar";

type AppLayoutProps = {
  /** Conteúdo principal da página */
  children: ReactNode;
  /** Conteúdo do painel direito (workspace). Opcional — omitir nas outras páginas. */
  rightPanel?: ReactNode;
  /** Rótulo do botão de abrir painel (padrão: "Painéis") */
  rightPanelLabel?: string;
  /**
   * Se true, o wrapper `main` usa overflow-hidden (para páginas com chat que
   * gerenciam scroll internamente). Se false usa overflow-y-auto.
   */
  mainOverflowHidden?: boolean;
};

export function AppLayout({
  children,
  rightPanel,
  rightPanelLabel = "Painéis",
  mainOverflowHidden = false,
}: AppLayoutProps) {
  const [rightOpen, setRightOpen] = useState(false);

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-bg-base">
      {/* ── Desktop sidebar (md+) ── */}
      <div className="hidden md:flex shrink-0">
        <Sidebar />
      </div>

      {/* ── Content column ── */}
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">

        {/* Mobile header (< md) */}
        <header className="md:hidden flex items-center justify-between px-4 h-14 shrink-0
          bg-bg-card border-b border-border z-10">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg
              bg-accent/10 border border-accent/30 shrink-0">
              <Bot size={14} className="text-accent" />
            </div>
            <div>
              <p className="text-sm font-semibold text-text-primary leading-none">Jarvis</p>
              <p className="text-2xs font-mono text-text-muted">v3.0 — local</p>
            </div>
          </div>

          {rightPanel && (
            <button
              type="button"
              onClick={() => setRightOpen(true)}
              aria-label="Abrir painéis"
              className="flex items-center gap-1.5 px-3 h-8 rounded-lg text-xs font-medium
                border border-border bg-bg-elevated text-text-secondary
                hover:text-text-primary hover:border-border-strong transition-colors"
            >
              <PanelRightOpen size={14} />
              {rightPanelLabel}
            </button>
          )}
        </header>

        {/* Body row */}
        <div className="flex flex-1 overflow-hidden min-h-0">

          {/* Main content */}
          <main
            className={[
              "flex flex-col flex-1 gap-3 p-3 md:p-4 min-w-0",
              /* Space for mobile bottom nav */
              "pb-20 md:pb-4",
              mainOverflowHidden ? "overflow-hidden" : "overflow-y-auto",
            ].join(" ")}
          >
            {children}
          </main>

          {/* Desktop right panel (lg+) */}
          {rightPanel && (
            <aside className="hidden lg:flex flex-col w-72 gap-3 p-4 overflow-y-auto
              border-l border-border shrink-0 h-full min-h-0">
              {rightPanel}
            </aside>
          )}
        </div>

        {/* Mobile bottom nav */}
        <MobileNav />
      </div>

      {/* ── Tablet right panel tab (md–lg) ── */}
      {rightPanel && (
        <AnimatePresence>
          {!rightOpen && (
            <motion.button
              key="tab"
              initial={{ x: 32 }}
              animate={{ x: 0 }}
              exit={{ x: 32 }}
              transition={{ type: "spring", damping: 28, stiffness: 260 }}
              onClick={() => setRightOpen(true)}
              aria-label="Abrir painel lateral"
              className="hidden md:flex lg:hidden fixed right-0 top-1/2 -translate-y-1/2 z-30
                flex-col items-center gap-1.5 px-1.5 py-3 rounded-l-lg border border-r-0
                border-border bg-bg-elevated/95 backdrop-blur-sm text-text-muted
                hover:text-accent hover:bg-accent/5 hover:border-accent/30 transition-colors shadow-card"
            >
              <ChevronLeft size={12} />
              <span
                className="text-2xs font-mono"
                style={{ writingMode: "vertical-lr", transform: "rotate(180deg)" }}
              >
                Painéis
              </span>
            </motion.button>
          )}
        </AnimatePresence>
      )}

      {/* ── Right panel drawer (mobile + tablet) ── */}
      {rightPanel && (
        <AnimatePresence>
          {rightOpen && (
            <>
              {/* Backdrop */}
              <motion.div
                key="backdrop"
                className="fixed inset-0 bg-black/60 z-40 lg:hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                onClick={() => setRightOpen(false)}
              />

              {/* Drawer */}
              <motion.aside
                key="drawer"
                className="fixed inset-y-0 right-0 w-80 z-50 flex flex-col overflow-hidden
                  bg-bg-card border-l border-border lg:hidden"
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 28, stiffness: 260 }}
              >
                {/* Drawer header */}
                <div className="flex items-center justify-between px-4 h-12 border-b border-border shrink-0">
                  <span className="text-xs font-mono uppercase tracking-widest text-text-muted">
                    Painéis
                  </span>
                  <button
                    type="button"
                    onClick={() => setRightOpen(false)}
                    aria-label="Fechar painel"
                    className="text-text-muted hover:text-text-primary transition-colors p-1 rounded"
                  >
                    <X size={16} />
                  </button>
                </div>

                {/* Drawer content */}
                <div className="flex-1 overflow-y-auto p-3 space-y-3 pb-safe">
                  {rightPanel}
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      )}
    </div>
  );
}
