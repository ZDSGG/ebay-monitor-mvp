type StatusPillProps = {
  tone: "neutral" | "rise" | "drop";
  children: string;
};

export function StatusPill({ tone, children }: StatusPillProps) {
  return <span className={`status-pill status-pill-${tone}`}>{children}</span>;
}
