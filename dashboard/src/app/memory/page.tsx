"use client";

import { useState } from "react";

import { motion } from "framer-motion";
import { AlertCircle, Brain, Search, Trash2 } from "lucide-react";

import { AppLayout } from "@/components/app-layout";
import { CollapsibleSection } from "@/components/collapsible-section";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";

type MemoryItem = {
  content: string;
  metadata: Record<string, string>;
  score: number;
  source: string;
};

type MemoryResponse = {
  items?: MemoryItem[];
};

export default function MemoryPage() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [clearConfirm, setClearConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    try {
      const response = await apiFetch("/api/memory/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 10 }),
      });
      const data = (await response.json()) as MemoryResponse;
      setItems(Array.isArray(data.items) ? data.items : []);
      setError(null);
    } catch (searchError) {
      setItems([]);
      setError(searchError instanceof Error ? searchError.message : "Falha ao buscar memórias.");
    } finally {
      setIsLoading(false);
    }
  };

  const clearMemory = async () => {
    if (!clearConfirm) {
      setClearConfirm(true);
      window.setTimeout(() => setClearConfirm(false), 4_000);
      return;
    }
    try {
      await apiFetch("/api/memory/clear", { method: "POST" });
      setItems([]);
      setQuery("");
      setError(null);
      setClearConfirm(false);
    } catch (clearError) {
      setError(clearError instanceof Error ? clearError.message : "Falha ao limpar memória.");
      setClearConfirm(false);
    }
  };

  const scoreColor = (score: number) => {
    if (score >= 0.8) return "text-status-success bg-status-success-soft border-status-success/20";
    if (score >= 0.5) return "text-status-warning bg-status-warning-soft border-status-warning/20";
    return "text-status-danger bg-status-danger-soft border-status-danger/20";
  };

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
        className="flex flex-col gap-4"
      >
          {/* Page header */}
          <div className="flex items-start justify-between shrink-0">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Brain size={16} className="text-accent" />
                <span className="text-xs font-mono uppercase tracking-widest text-text-muted">
                  Armazenamento Persistente
                </span>
              </div>
              <h1 className="text-xl font-bold text-text-primary">Memória</h1>
              <p className="text-sm text-text-secondary mt-1">
                Busca semântica na base vetorial ChromaDB.
              </p>
            </div>

            {/* Clear button */}
            <button
              type="button"
              onClick={() => void clearMemory()}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium border transition-all duration-200",
                clearConfirm
                  ? "bg-status-danger text-white border-status-danger shadow-[0_0_12px_rgba(251,113,133,0.3)]"
                  : "bg-bg-elevated border-border text-text-secondary hover:text-status-danger hover:border-status-danger/30 hover:bg-status-danger-soft"
              )}
              aria-label="Limpar toda a memória"
            >
              <Trash2 size={13} />
              {clearConfirm ? "Confirmar limpeza" : "Limpar tudo"}
            </button>
          </div>

          {/* Error banner */}
          {error && (
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-status-danger-soft border border-status-danger/20 text-status-danger text-xs shrink-0">
              <AlertCircle size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Search */}
          <CollapsibleSection title="Busca Semântica" defaultOpen>
            <div className="p-4 space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") void search(); }}
                  placeholder="Buscar memórias por semântica…"
                  className={cn(
                    "flex-1 h-10 px-3.5 rounded-lg text-sm border bg-bg-elevated",
                    "text-text-primary placeholder:text-text-muted",
                    "focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20",
                    "transition-colors duration-150 border-border"
                  )}
                />
                <button
                  type="button"
                  onClick={() => void search()}
                  disabled={isLoading || !query.trim()}
                  className={cn(
                    "flex items-center gap-2 h-10 px-4 rounded-lg text-sm font-medium border transition-all duration-200",
                    query.trim() && !isLoading
                      ? "bg-accent text-bg-base border-accent hover:bg-accent/90 shadow-glow-sm"
                      : "bg-bg-elevated border-border text-text-muted cursor-not-allowed opacity-50"
                  )}
                >
                  <Search size={14} className={isLoading ? "animate-pulse" : ""} />
                  {isLoading ? "Buscando…" : "Buscar"}
                </button>
              </div>

              <p className="text-2xs text-text-muted font-mono">
                Pressione Enter para buscar · Máximo 10 resultados
              </p>
            </div>
          </CollapsibleSection>

          {/* Results */}
          {(items.length > 0 || (query && !isLoading)) && (
            <CollapsibleSection
              title="Resultados"
              badge={items.length > 0 ? items.length : undefined}
              defaultOpen
            >
              {items.length === 0 ? (
                <div className="flex flex-col items-center gap-2 py-10 text-center">
                  <Brain size={24} className="text-text-muted opacity-30" />
                  <p className="text-sm text-text-muted">
                    Nenhuma memória encontrada para &ldquo;{query}&rdquo;.
                  </p>
                </div>
              ) : (
                <ul className="divide-y divide-border/50">
                  {items.map((item, index) => (
                    <li
                      key={`${item.source}-${index}`}
                      className="p-4 hover:bg-bg-hover/30 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-xs font-mono text-text-muted bg-bg-elevated border border-border px-2 py-0.5 rounded truncate">
                          {item.source}
                        </span>
                        <span
                          className={cn(
                            "shrink-0 text-2xs font-mono px-2 py-0.5 rounded border",
                            scoreColor(item.score)
                          )}
                        >
                          {(item.score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-text-primary leading-relaxed">{item.content}</p>
                      {Object.keys(item.metadata).length > 0 && (
                        <p className="mt-2 text-2xs font-mono text-text-muted">
                          {JSON.stringify(item.metadata)}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </CollapsibleSection>
          )}

          {/* Info section */}
          <CollapsibleSection title="Configuração da Memória" defaultOpen={false}>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-border/50 rounded-b-lg overflow-hidden">
              {[
                { label: "Modo de Busca", value: "Semântico" },
                { label: "Limpeza", value: "Explícita" },
                { label: "Fallback", value: "In-memory" },
                { label: "Backend", value: "ChromaDB" },
              ].map(({ label, value }) => (
                <div key={label} className="bg-bg-card px-3 py-3">
                  <p className="text-2xs font-mono uppercase tracking-wider text-text-muted mb-1">{label}</p>
                  <p className="text-xs font-semibold text-text-primary">{value}</p>
                </div>
              ))}
            </div>
          </CollapsibleSection>
      </motion.div>
    </AppLayout>
  );
}
