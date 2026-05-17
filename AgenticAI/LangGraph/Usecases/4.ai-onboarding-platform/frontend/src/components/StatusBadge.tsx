interface Props {
  status: string;
}

const STYLES: Record<string, string> = {
  draft:                "bg-slate-100 text-slate-700",
  submitted:            "bg-blue-100 text-blue-700",
  validating:           "bg-amber-100 text-amber-700",
  validated_pass:       "bg-emerald-100 text-emerald-700",
  validated_with_fixes: "bg-cyan-100 text-cyan-700",
  pending_human_review: "bg-pink-100 text-pink-700",
  approved:             "bg-emerald-100 text-emerald-700",
  rejected:             "bg-red-100 text-red-700",
  // Findings
  pass:    "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  fail:    "bg-red-100 text-red-700",
};

const LABELS: Record<string, string> = {
  draft:                "Draft",
  submitted:            "Submitted",
  validating:           "Validating",
  validated_pass:       "Validated",
  validated_with_fixes: "Validated (auto-fixed)",
  pending_human_review: "Pending BOM Review",
  approved:             "Approved",
  rejected:             "Rejected",
  pass:                 "Pass",
  warning:              "Warning",
  fail:                 "Fail",
};

export default function StatusBadge({ status }: Props) {
  const cls = STYLES[status] ?? "bg-slate-100 text-slate-700";
  const label = LABELS[status] ?? status;
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}
