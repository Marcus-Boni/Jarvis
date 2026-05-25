"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

type CollapsibleSectionProps = {
  title: string;
  badge?: string | number;
  defaultOpen?: boolean;
  className?: string;
  headerClassName?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
};

export function CollapsibleSection({
  title,
  badge,
  defaultOpen = true,
  className,
  headerClassName,
  children,
  actions,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={cn("glass-panel rounded-lg overflow-hidden", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center justify-between w-full px-4 py-3 text-left",
          "hover:bg-bg-hover/50 transition-colors group",
          headerClassName
        )}
        aria-expanded={open}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="text-xs font-semibold uppercase tracking-widest text-text-muted font-mono truncate">
            {title}
          </span>
          {badge !== undefined && (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-2xs font-mono bg-accent/10 text-accent border border-accent/20">
              {badge}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {actions && <div onClick={(e) => e.stopPropagation()}>{actions}</div>}
          <motion.div
            animate={{ rotate: open ? 0 : -90 }}
            transition={{ duration: 0.2, ease: [0.2, 0.8, 0.2, 1] }}
          >
            <ChevronDown size={14} className="text-text-muted group-hover:text-text-secondary transition-colors" />
          </motion.div>
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
            style={{ overflow: "hidden" }}
          >
            <div className="border-t border-border/50">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
