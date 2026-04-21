"use client";

import { Mic, MicOff, Radio } from "lucide-react";

type VoiceButtonProps = {
  onClick: () => void | Promise<void>;
  state: "idle" | "listening" | "processing" | "speaking";
};

export function VoiceButton({ onClick, state }: VoiceButtonProps) {
  return (
    <button
      className={`voice-button state-${state}`}
      type="button"
      aria-label="Toggle voice mode"
      onClick={() => void onClick()}
    >
      <span className="voice-core">
        {state === "idle" && <Mic size={18} />}
        {state === "listening" && <Radio size={18} />}
        {state === "processing" && <Mic size={18} />}
        {state === "speaking" && <MicOff size={18} />}
      </span>
      <span>{state}</span>
      <span className="voice-wave" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
    </button>
  );
}

