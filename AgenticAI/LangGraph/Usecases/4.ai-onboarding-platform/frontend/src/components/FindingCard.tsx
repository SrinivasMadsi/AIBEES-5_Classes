import type { Finding } from "../types/api";
import { AlertCircle, CheckCircle2, XCircle } from "lucide-react";

interface Props {
  finding: Finding;
}

export default function FindingCard({ finding }: Props) {
  const isPass = finding.status === "pass";
  const isWarning = finding.status === "warning";
  const isFail = finding.status === "fail";

  const borderColor = isPass
    ? "border-emerald-200"
    : isWarning
    ? "border-amber-200"
    : "border-red-200";

  const bgColor = isPass
    ? "bg-emerald-50"
    : isWarning
    ? "bg-amber-50"
    : "bg-red-50";

  const Icon = isPass ? CheckCircle2 : isWarning ? AlertCircle : XCircle;
  const iconColor = isPass
    ? "text-emerald-600"
    : isWarning
    ? "text-amber-600"
    : "text-red-600";

  return (
    <div className={`border-l-4 ${borderColor} ${bgColor} px-4 py-3 rounded-r-lg`}>
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 mt-0.5 ${iconColor} flex-shrink-0`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs font-semibold text-slate-700">{finding.rule_id}</span>
            <span className="text-xs text-slate-400">·</span>
            <span className="text-xs text-slate-600">{finding.domain}</span>
            <span className="text-xs text-slate-400">·</span>
            <span className="text-xs text-slate-600">Q{finding.affected_field}</span>
            {finding.severity === "fail_reject" && (
              <span className="text-xs px-1.5 py-0.5 bg-red-200 text-red-900 rounded font-semibold">
                ESCALATED
              </span>
            )}
            {finding.auto_applied && (
              <span className="text-xs px-1.5 py-0.5 bg-cyan-200 text-cyan-900 rounded font-semibold">
                AUTO-FIXED
              </span>
            )}
          </div>
          <div className="mt-1 font-medium text-sm text-slate-900">{finding.rule_name}</div>
          {finding.message && <p className="mt-1 text-sm text-slate-700">{finding.message}</p>}
          {isFail && finding.current_value !== null && (
            <div className="mt-2 text-xs text-slate-600 font-mono">
              <span className="text-slate-400">current:</span> {String(finding.current_value)}
              {finding.expected_value !== null && (
                <>
                  {"  "}
                  <span className="text-slate-400">expected:</span> {String(finding.expected_value)}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
