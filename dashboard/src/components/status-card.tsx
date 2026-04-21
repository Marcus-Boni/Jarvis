type StatusCardProps = {
  label: string;
  value: string;
  detail: string;
  tone: "success" | "warning" | "info" | "default";
};

export function StatusCard({ detail, label, tone, value }: StatusCardProps) {
  return (
    <article className={`panel status-card tone-${tone}`}>
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

