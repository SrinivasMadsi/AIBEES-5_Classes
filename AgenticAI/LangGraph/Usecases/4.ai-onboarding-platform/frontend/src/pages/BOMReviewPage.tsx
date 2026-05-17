import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Check, FileWarning, X } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { getReview, submitReviewDecision } from "../lib/api";
import type { ReviewDetail } from "../types/api";

export default function BOMReviewPage() {
  const { reviewId } = useParams<{ reviewId: string }>();
  const navigate = useNavigate();
  const [review, setReview] = useState<ReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewer, setReviewer] = useState("bom.analyst@healthcare.com");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (reviewId) {
      getReview(Number(reviewId))
        .then(setReview)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [reviewId]);

  const handleDecision = async (decision: "approve" | "reject" | "override") => {
    if (!reviewId) return;
    setSubmitting(true);
    try {
      await submitReviewDecision(Number(reviewId), { reviewed_by: reviewer, decision, comment });
      navigate("/bom/queue");
    } catch (err) {
      console.error(err);
      alert("Failed to submit decision");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="p-8 text-slate-500">Loading...</div>;
  if (!review) return <div className="p-8 text-red-500">Review not found</div>;

  return (
    <div>
      <PageHeader
        title={`Review: ${review.rule_id}`}
        subtitle={`${review.client_name} · Submission ${review.submission_id}`}
      />
      <div className="p-8 max-w-4xl">
        {/* Context */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 mb-6">
          <h2 className="font-display font-semibold text-base text-slate-800 mb-3">Issue</h2>
          <div className="flex items-start gap-3">
            <FileWarning className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-slate-700">{review.issue_description}</p>
          </div>
          {review.agent_recommendation && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="text-xs uppercase tracking-wide text-slate-500 font-semibold mb-1">
                Agent Recommendation
              </div>
              <p className="text-sm text-slate-700">{review.agent_recommendation}</p>
            </div>
          )}
        </div>

        {/* Finding detail */}
        {review.finding && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 mb-6">
            <h2 className="font-display font-semibold text-base text-slate-800 mb-3">
              Rule details: {review.finding.rule_name}
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Field</div>
                <div className="font-mono">Q{review.finding.affected_field}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Domain</div>
                <div>{review.finding.domain}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Current</div>
                <div className="font-mono">{String(review.finding.current_value)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Expected</div>
                <div className="font-mono">{String(review.finding.expected_value)}</div>
              </div>
            </div>
          </div>
        )}

        {/* Decision form */}
        <div className="bg-white border border-slate-200 rounded-xl p-6">
          <h2 className="font-display font-semibold text-base text-slate-800 mb-4">Your Decision</h2>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Reviewed by</label>
              <input
                type="email"
                className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
              />
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-1">Comment</label>
            <textarea
              rows={3}
              className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Optional comment explaining your decision..."
            />
          </div>

          <div className="flex gap-3 pt-2 border-t border-slate-100">
            <button
              onClick={() => handleDecision("approve")}
              disabled={submitting}
              className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white px-4 py-2 rounded-lg text-sm font-medium"
            >
              <Check className="w-4 h-4" />
              Approve as-is
            </button>
            <button
              onClick={() => handleDecision("reject")}
              disabled={submitting}
              className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white px-4 py-2 rounded-lg text-sm font-medium"
            >
              <X className="w-4 h-4" />
              Reject (back to IPM)
            </button>
            <button
              onClick={() => handleDecision("override")}
              disabled={submitting || !comment}
              className="flex items-center gap-2 bg-slate-700 hover:bg-slate-800 disabled:bg-slate-300 text-white px-4 py-2 rounded-lg text-sm font-medium"
            >
              <Check className="w-4 h-4" />
              Override with comment
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
