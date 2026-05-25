"use client";

import { useState } from "react";

import { ChevronRight, Package, Tag } from "lucide-react";

import { cn } from "@/lib/utils";
import { DetailModal } from "@/components/detail-modal";

type SkillStatus = {
  description: string;
  enabled: boolean;
  name: string;
  triggers?: string[];
};

type SkillListProps = {
  skills: SkillStatus[];
  onToggle?: (name: string, enabled: boolean) => void;
};

export function SkillList({ skills, onToggle }: SkillListProps) {
  // Keep only the name so the derived skill is always fresh from props
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const selected = skills.find((s) => s.name === selectedName) ?? null;

  if (skills.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-8 text-center">
        <Package size={20} className="text-text-muted opacity-40" />
        <p className="text-xs text-text-muted">Nenhum módulo carregado.</p>
      </div>
    );
  }

  return (
    <>
      <ul className="space-y-0">
        {skills.map((skill) => (
          <li key={skill.name}>
            <button
              type="button"
              onClick={() => setSelectedName(skill.name)}
              className="flex items-center gap-3 w-full px-4 py-3 border-b border-border/50 last:border-0 hover:bg-bg-hover/30 active:bg-bg-hover/50 transition-colors group text-left"
              aria-label={`Ver detalhes de ${skill.name}`}
            >
              {/* Status dot */}
              <div
                aria-hidden="true"
                className={cn(
                  "w-1.5 h-1.5 rounded-full shrink-0 transition-colors",
                  skill.enabled
                    ? "bg-status-success shadow-[0_0_5px_rgba(52,211,153,0.5)]"
                    : "bg-text-muted"
                )}
              />

              {/* Info */}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-text-primary font-mono truncate">
                  {skill.name}
                </p>
                <p className="text-2xs text-text-muted mt-0.5 truncate">{skill.description}</p>
              </div>

              {/* Status badge + chevron */}
              <div className="flex items-center gap-1.5 shrink-0">
                <span
                  className={cn(
                    "text-2xs font-mono px-2 py-0.5 rounded border",
                    skill.enabled
                      ? "text-status-success bg-status-success-soft border-status-success/20"
                      : "text-text-muted bg-bg-elevated border-border"
                  )}
                >
                  {skill.enabled ? "ativo" : "inativo"}
                </span>
                <ChevronRight
                  size={12}
                  className="text-text-muted opacity-0 group-hover:opacity-100 transition-opacity"
                />
              </div>
            </button>
          </li>
        ))}
      </ul>

      {/* Detail modal */}
      <DetailModal
        open={!!selected}
        onClose={() => setSelectedName(null)}
        title={selected?.name ?? ""}
        subtitle="Detalhes do módulo"
      >
        {selected && (
          <SkillDetail
            skill={selected}
            onToggle={
              onToggle
                ? (name, enabled) => {
                    onToggle(name, enabled);
                  }
                : undefined
            }
          />
        )}
      </DetailModal>
    </>
  );
}

/* ── Skill detail content ── */

function SkillDetail({
  skill,
  onToggle,
}: {
  skill: SkillStatus;
  onToggle?: (name: string, enabled: boolean) => void;
}) {
  return (
    <div className="divide-y divide-border/50">
      {/* Status banner */}
      <div className="px-4 py-3">
        <div
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg text-xs border",
            skill.enabled
              ? "bg-status-success-soft border-status-success/20 text-status-success"
              : "bg-bg-elevated border-border text-text-muted"
          )}
        >
          <div
            className={cn(
              "w-1.5 h-1.5 rounded-full shrink-0",
              skill.enabled
                ? "bg-status-success shadow-[0_0_5px_rgba(52,211,153,0.5)]"
                : "bg-text-muted"
            )}
          />
          <span className="font-mono font-medium">
            {skill.enabled ? "Ativo e disponível" : "Inativo"}
          </span>
        </div>
      </div>

      {/* Description */}
      <div className="px-4 py-3">
        <p className="text-2xs font-mono uppercase tracking-wider text-text-muted mb-2">
          Descrição
        </p>
        <p className="text-sm text-text-primary leading-relaxed">{skill.description}</p>
      </div>

      {/* Triggers */}
      {skill.triggers && skill.triggers.length > 0 && (
        <div className="px-4 py-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Tag size={11} className="text-text-muted" />
            <p className="text-2xs font-mono uppercase tracking-wider text-text-muted">
              Triggers · {skill.triggers.length}
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {skill.triggers.map((trigger) => (
              <span
                key={trigger}
                className="inline-flex items-center px-2 py-0.5 rounded-md text-2xs font-mono bg-accent/10 text-accent border border-accent/20"
              >
                {trigger}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Toggle action */}
      {onToggle && (
        <div className="px-4 py-3">
          <button
            type="button"
            onClick={() => onToggle(skill.name, skill.enabled)}
            className={cn(
              "w-full py-2 px-4 rounded-lg text-sm font-medium border transition-all duration-200",
              skill.enabled
                ? "bg-status-danger-soft border-status-danger/20 text-status-danger hover:bg-status-danger hover:text-white hover:border-status-danger"
                : "bg-accent/10 border-accent/20 text-accent hover:bg-accent hover:text-bg-base hover:border-accent"
            )}
          >
            {skill.enabled ? "Desativar módulo" : "Ativar módulo"}
          </button>
        </div>
      )}
    </div>
  );
}
