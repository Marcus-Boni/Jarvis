import { cn } from "@/lib/utils";

export type StatusTone = "success" | "warning" | "danger" | "info" | "default";

type StatusCardProps = {
  label: string;
  value: string;
  detail: string;
  tone?: StatusTone;
};

const toneStyles: Record<StatusTone, { dot: string; border: string; bg: string }> = {
  success: {
    dot: "bg-status-success shadow-[0_0_6px_rgba(52,211,153,0.6)]",
    border: "border-status-success/20",
    bg: "bg-status-success-soft",
  },
  warning: {
    dot: "bg-status-warning shadow-[0_0_6px_rgba(251,191,36,0.6)]",
    border: "border-status-warning/20",
    bg: "bg-status-warning-soft",
  },
  danger: {
    dot: "bg-status-danger shadow-[0_0_6px_rgba(251,113,133,0.6)]",
    border: "border-status-danger/20",
    bg: "bg-status-danger-soft",
  },
  info: {
    dot: "bg-status-info shadow-[0_0_6px_rgba(129,140,248,0.6)]",
    border: "border-status-info/20",
    bg: "bg-status-info-soft",
  },
  default: {
    dot: "bg-text-muted",
    border: "border-border",
    bg: "bg-bg-elevated/40",
  },
};

export function StatusCard({ label, value, detail, tone = "default" }: StatusCardProps) {
  const styles = toneStyles[tone];

  return (
    <div
      className={cn(
        "flex flex-col gap-2 p-4 rounded-lg border transition-all duration-200",
        styles.border,
        styles.bg
      )}
    >
      <div className="flex items-center gap-2">
        <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", styles.dot)} />
        <span className="text-xs font-mono uppercase tracking-widest text-text-muted">{label}</span>
      </div>
      <p className="text-sm font-semibold text-text-primary leading-tight truncate">{value}</p>
      <p className="text-xs text-text-secondary leading-relaxed">{detail}</p>
    </div>
  );
}
