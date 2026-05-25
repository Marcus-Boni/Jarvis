"use client";

import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

type DetailModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function DetailModal({ open, onClose, title, subtitle, children }: DetailModalProps) {
  // Guard SSR — createPortal needs document.body
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  // Prevent body scroll while open
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop — z-[200] is above every app layer (sidebar z-20, drawer z-50) */}
          <motion.div
            key="backdrop"
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            style={{ zIndex: 200 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Dialog wrapper — pointer-events-none, centres the card */}
          <div
            role="dialog"
            aria-modal="true"
            aria-label={title}
            className="fixed inset-0 flex items-center justify-center p-4 sm:p-6 pointer-events-none"
            style={{ zIndex: 201 }}
          >
            <motion.div
              key="modal"
              className="pointer-events-auto flex flex-col w-full max-w-lg bg-bg-card border border-border rounded-xl shadow-[0_32px_64px_rgba(0,0,0,0.65)] overflow-hidden"
              style={{ maxHeight: "min(85vh, 680px)" }}
              initial={{ opacity: 0, scale: 0.96, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 12 }}
              transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
            >
              {/* Header — fixed, never scrolls */}
              <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border shrink-0">
                <div className="min-w-0">
                  <p className="text-base font-semibold text-text-primary font-mono truncate">
                    {title}
                  </p>
                  {subtitle && (
                    <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  aria-label="Fechar"
                  className="shrink-0 p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Body — scrollable */}
              <div className="overflow-y-auto flex-1">{children}</div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>,
    document.body,
  );
}
