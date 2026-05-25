"use client";

import { Mic, Radio } from "lucide-react";
import { cn } from "@/lib/utils";

type VoiceState = "idle" | "listening" | "processing" | "speaking";

type VoiceButtonProps = {
  state: VoiceState;
  onClick: () => void | Promise<void>;
};

const stateConfig: Record<VoiceState, { label: string; icon: typeof Mic }> = {
  idle: { label: "Voz", icon: Mic },
  listening: { label: "Ouvindo…", icon: Mic },
  processing: { label: "Processando…", icon: Radio },
  speaking: { label: "Falando…", icon: Radio },
};

export function VoiceButton({ state, onClick }: VoiceButtonProps) {
  const { label, icon: Icon } = stateConfig[state];
  const isActive = state !== "idle";

  return (
    <button
      type="button"
      onClick={() => void onClick()}
      aria-label={label}
      className={cn(
        "flex items-center gap-2 h-9 px-3 rounded-lg text-xs font-medium border transition-all duration-200",
        isActive
          ? "bg-accent/10 border-accent/30 text-accent"
          : "bg-bg-elevated border-border text-text-secondary hover:text-text-primary hover:border-border-strong"
      )}
    >
      <Icon size={14} className={cn(state === "listening" && "animate-pulse")} />
      <span>{label}</span>
      {(state === "listening" || state === "speaking") && (
        <span className="flex items-end gap-px h-3.5" aria-hidden="true">
          {[0, 80, 160].map((delay) => (
            <span
              key={delay}
              className="block w-0.5 rounded-full bg-accent animate-[voiceBar_900ms_ease-in-out_infinite]"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </span>
      )}
    </button>
  );
}
