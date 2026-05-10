// src/components/StatusBadge.tsx
import { CheckCircle2, AlertTriangle, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/format";

interface Props {
  status: string;
  size?: "sm" | "md";
}

const MAP: Record<string, { className: string; icon: typeof CheckCircle2; label?: string }> = {
  pass:       { className: "badge-pass",    icon: CheckCircle2 },
  submitted:  { className: "badge-pass",    icon: CheckCircle2 },
  validated:  { className: "badge-pass",    icon: CheckCircle2 },
  fail:       { className: "badge-fail",    icon: XCircle },
  rejected:   { className: "badge-fail",    icon: XCircle },
  warning:    { className: "badge-warning", icon: AlertTriangle },
  draft:      { className: "badge-neutral", icon: Clock },
  needs_human:{ className: "badge-warning", icon: AlertTriangle, label: "needs human" },
};

export default function StatusBadge({ status, size = "sm" }: Props) {
  const cfg = MAP[status] ?? { className: "badge-neutral", icon: Clock };
  const Icon = cfg.icon;
  const label = cfg.label ?? status;

  return (
    <span className={cn("badge", cfg.className, size === "md" && "text-sm px-3 py-1")}>
      <Icon className={cn(size === "md" ? "w-3.5 h-3.5" : "w-3 h-3", "mr-1")} />
      {label}
    </span>
  );
}
