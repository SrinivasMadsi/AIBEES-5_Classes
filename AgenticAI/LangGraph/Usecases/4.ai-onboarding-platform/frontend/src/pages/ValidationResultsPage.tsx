import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle2, RefreshCw, ShieldAlert } from "lucide-react";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import FindingCard from "../components/FindingCard";
import { getSubmission, validateSubmission } from "../lib/api";
import type { Submission } from "../types/api";

export default function ValidationResultsPage() {
  const { submissionId } = useParams<{ submissionId: string }>();
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [revalidating, setRevalidating] = useState(false);

  const fetch = async () => {
    if (!submissionId) return;
    setLoading(true);
    try {
      const sub = await getSubmission(submissionId);
      setSubmission(sub);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [submissionId]);

  const handleRevalidate = async () => {
    if (!submissionId) return;
    setRevalidating(true);
    try {
      await validateSubmission(submissionId);
      await fetch();
    } catch (err) {
      console.error(err);
    } finally {
      setRevalidating(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-500">Loading...</div>;
  }
  if (!submission) {
    return <div className="p-8 text-red-500">Submission not found</div>;
  }

  const findings = submission.findings ?? [];
  const passCount = findings.filter((f) => f.status === "pass").length;
  const warnCount = findings.filter((f) => f.status === "warning").length;
  const failCount = findings.filter((f) => f.status === "fail").length;

  return (
    <div>
      <PageHeader
        title={`Validation: ${submission.submission_id}`}
        subtitle={`${submission.client_name} · Form ${submission.form_id}`}
        right={
          <div className="flex items-center gap-3">
            <StatusBadge status={submission.status} />
            <button
              onClick={handleRevalidate}
              disabled={revalidating}
              className="flex items-center gap-2 border border-slate-300 hover:border-slate-400 px-3 py-2 rounded-lg text-sm font-medium"
            >
              <RefreshCw className={`w-4 h-4 ${revalidating ? "animate-spin" : ""}`} />
              Re-validate
            </button>
          </div>
        }
      />

      <div className="p-8 max-w-5xl">
        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <StatCard label="Plan Type" value={submission.plan_type ?? "—"} />
          <StatCard label="Passed" value={passCount} color="emerald" />
          <StatCard label="Warnings" value={warnCount} color="amber" />
          <StatCard label="Failures" value={failCount} color="red" />
        </div>

        {submission.status === "pending_human_review" && (
          <div className="mb-6 bg-pink-50 border border-pink-200 rounded-xl p-5 flex items-start gap-3">
            <ShieldAlert className="w-6 h-6 text-pink-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-pink-900">Pending BOM Analyst Review</div>
              <p className="text-sm text-pink-800 mt-1">
                One or more findings require human review. A BOM analyst will approve or reject
                them shortly.
              </p>
            </div>
          </div>
        )}

        {submission.status === "validated_pass" && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex items-start gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-emerald-900">Submission Validated</div>
              <p className="text-sm text-emerald-800 mt-1">
                All checks passed. Ready for downstream provisioning.
              </p>
            </div>
          </div>
        )}

        {/* Findings */}
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="font-display text-lg font-bold text-slate-900 mb-4">
            Validation Findings ({findings.length})
          </h2>
          {findings.length === 0 && <p className="text-sm text-slate-500">No findings yet.</p>}
          <div className="space-y-2">
            {findings.map((f, idx) => (
              <FindingCard key={idx} finding={f} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  const colors: Record<string, string> = {
    emerald: "border-emerald-200 bg-emerald-50",
    amber:   "border-amber-200 bg-amber-50",
    red:     "border-red-200 bg-red-50",
  };
  const cls = color ? colors[color] : "border-slate-200 bg-white";
  return (
    <div className={`border rounded-xl p-4 ${cls}`}>
      <div className="text-xs uppercase tracking-wide text-slate-500 font-semibold">{label}</div>
      <div className="text-2xl font-bold text-slate-900 mt-1">{value}</div>
    </div>
  );
}
