"use client";

import { useEffect, useState } from "react";

import { motion } from "framer-motion";
import { CheckCircle2, Info, Package, Settings2 } from "lucide-react";

import { apiFetch } from "@/lib/api";
import { AppLayout } from "@/components/app-layout";
import { CollapsibleSection } from "@/components/collapsible-section";

type SkillStatus = {
  description: string;
  enabled: boolean;
  name: string;
};

type SkillsResponse = {
  items?: SkillStatus[];
};

export default function SettingsPage() {
  const [skills, setSkills] = useState<SkillStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSkills = async () => {
      setIsLoading(true);
      try {
        const response = await apiFetch("/api/skills");
        const data = (await response.json()) as SkillsResponse;
        setSkills(Array.isArray(data.items) ? data.items : []);
        setError(null);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Falha ao carregar módulos.");
      } finally {
        setIsLoading(false);
      }
    };
    void loadSkills();
  }, []);

  const toggleSkill = async (skillName: string, currentEnabled: boolean) => {
    try {
      await apiFetch(`/api/skills/${skillName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !currentEnabled }),
      });
      setSkills((current) =>
        current.map((s) => (s.name === skillName ? { ...s, enabled: !currentEnabled } : s))
      );
      setError(null);
      setSavedId(skillName);
      window.setTimeout(() => setSavedId(null), 1_800);
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "Falha ao atualizar módulo.");
    }
  };

  const activeCount = skills.filter((s) => s.enabled).length;

  return (
    <AppLayout>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.2, 0.8, 0.2, 1] }}
        className="flex flex-col gap-4"
      >
          {/* Page header */}
          <div className="shrink-0">
            <div className="flex items-center gap-2 mb-1">
              <Settings2 size={16} className="text-accent" />
              <span className="text-xs font-mono uppercase tracking-widest text-text-muted">
                Configuração
              </span>
            </div>
            <h1 className="text-xl font-bold text-text-primary">Configurações</h1>
            <p className="text-sm text-text-secondary mt-1">
              Gerencie os módulos de runtime e inspecione o registry de skills.
            </p>
          </div>

          {/* Error banner */}
          {error && (
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-status-danger-soft border border-status-danger/20 text-status-danger text-xs">
              <Info size={14} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Skills section */}
          <CollapsibleSection
            title="Módulos de Runtime"
            badge={isLoading ? undefined : `${activeCount}/${skills.length} ativos`}
            defaultOpen
          >
            {isLoading ? (
              <div className="flex items-center gap-3 px-4 py-6 text-text-muted text-sm">
                <Package size={16} className="animate-pulse" />
                <span>Carregando módulos…</span>
              </div>
            ) : (
              <ul className="space-y-0">
                {skills.map((skill) => (
                  <li
                    key={skill.name}
                    className="flex items-center gap-3 px-4 py-3 border-b border-border/50 last:border-0 hover:bg-bg-hover/30 transition-colors"
                  >
                    <div
                      className={`w-1.5 h-1.5 rounded-full shrink-0 transition-colors ${
                        skill.enabled
                          ? "bg-status-success shadow-[0_0_5px_rgba(52,211,153,0.5)]"
                          : "bg-text-muted"
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-text-primary font-mono">{skill.name}</p>
                      <p className="text-2xs text-text-muted mt-0.5 truncate">{skill.description}</p>
                    </div>

                    {/* Saved indicator */}
                    {savedId === skill.name && (
                      <CheckCircle2 size={13} className="text-status-success shrink-0" />
                    )}

                    <button
                      type="button"
                      onClick={() => void toggleSkill(skill.name, skill.enabled)}
                      aria-label={skill.enabled ? `Desativar ${skill.name}` : `Ativar ${skill.name}`}
                      className={`shrink-0 text-2xs font-mono px-2.5 py-1 rounded border transition-all duration-150 ${
                        skill.enabled
                          ? "text-status-success bg-status-success-soft border-status-success/20 hover:bg-status-danger-soft hover:text-status-danger hover:border-status-danger/20"
                          : "text-text-muted bg-bg-elevated border-border hover:text-accent hover:border-accent/30 hover:bg-accent/10"
                      }`}
                    >
                      {skill.enabled ? "ativo" : "inativo"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CollapsibleSection>

          {/* Info section */}
          <CollapsibleSection title="Informações do Runtime" defaultOpen={false}>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-border/50 rounded-b-lg overflow-hidden">
              {[
                { label: "Escopo", value: "Runtime Local" },
                { label: "Persistência", value: "Imediata" },
                { label: "Transporte", value: "FastAPI REST" },
                { label: "Fase", value: "3" },
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
