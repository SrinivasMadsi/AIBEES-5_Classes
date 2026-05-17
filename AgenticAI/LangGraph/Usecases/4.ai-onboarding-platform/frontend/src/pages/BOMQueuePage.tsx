import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { listReviews } from "../lib/api";
import type { Review } from "../types/api";

export default function BOMQueuePage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listReviews()
      .then(setReviews)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="BOM Review Queue"
        subtitle="Findings flagged by the agent that need human review"
      />
      <div className="p-8">
        {loading && <p className="text-slate-500">Loading...</p>}
        {!loading && reviews.length === 0 && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 max-w-2xl">
            <div className="font-semibold text-emerald-900">No pending reviews 🎉</div>
            <p className="text-sm text-emerald-800 mt-1">The queue is empty.</p>
          </div>
        )}
        <div className="space-y-3">
          {reviews.map((r) => (
            <Link
              key={r.review_id}
              to={`/bom/reviews/${r.review_id}`}
              className="block bg-white border border-slate-200 rounded-xl p-5 hover:border-pink-400 hover:shadow-md transition-all"
            >
              <div className="flex items-start gap-3">
                <ShieldAlert className="w-6 h-6 text-pink-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded">{r.rule_id}</span>
                    <span className="font-semibold text-slate-900">{r.client_name}</span>
                    <span className="text-xs text-slate-500">Form {r.form_id}</span>
                  </div>
                  <p className="text-sm text-slate-700 mt-1">{r.issue_description}</p>
                  <div className="mt-2 text-xs text-slate-500">
                    Submitted by {r.submitted_by} ·{" "}
                    {r.created_at ? new Date(r.created_at).toLocaleString() : "—"}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
