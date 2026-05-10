// src/pages/ChatPage.tsx
import { useState } from "react";
import { Send, Sparkles, Loader2, RotateCcw } from "lucide-react";

import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";
import { formatINR, cn } from "@/lib/format";
import type { ChatResponse } from "@/types/api";

const SAMPLE_REQUESTS = [
  "Order 5 Dell Latitude 5450 laptops, 5 Logitech MX Master mice, and 5 Logitech K380 keyboards for the Hyderabad office. Charge to budget PO-2026-Q2-0847.",
  "Need 3 Lenovo ThinkPad T14 Gen 4 laptops for the Sales Bangalore team. Use budget PO-2026-Q2-0445.",
  "Please order 10 Dell 27-inch monitors and 10 Logitech MX Keys keyboards for the Engineering Bangalore office. Budget PO-2026-Q2-0912.",
];

export default function ChatPage() {
  const [message, setMessage]   = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);

  const handleSubmit = async () => {
    if (!message.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const res = await api.chat(message);
      setResponse(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessage("");
    setResponse(null);
    setError(null);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <PageHeader
        title="Submit Procurement Request"
        description="Describe what you need in plain English. The agent will assemble, audit, and validate the PO."
      />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* ── Input + sample prompts ─────────────────────────────── */}
        <section className="lg:col-span-3 space-y-4">
          <div className="card p-5">
            <label className="text-sm font-medium text-slate-700 mb-2 block">
              Your request
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={6}
              placeholder="e.g. Order 5 Dell Latitude 5450 laptops for the Hyderabad office. Use budget PO-2026-Q2-0847."
              className="w-full px-3 py-2 border border-slate-300 rounded-lg
                         focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent
                         text-sm resize-none"
              disabled={loading}
            />

            <div className="flex items-center justify-between mt-4">
              <button
                onClick={handleReset}
                className="btn-secondary flex items-center gap-2"
                disabled={loading}
              >
                <RotateCcw className="w-4 h-4" /> Reset
              </button>
              <button
                onClick={handleSubmit}
                disabled={!message.trim() || loading}
                className="btn-primary flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Agent is thinking…
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Submit
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Sample prompts */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <h3 className="text-sm font-medium text-slate-700">Try a sample</h3>
            </div>
            <div className="space-y-2">
              {SAMPLE_REQUESTS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => setMessage(s)}
                  disabled={loading}
                  className="w-full text-left px-3 py-2 bg-slate-50 hover:bg-slate-100
                             rounded-lg text-sm text-slate-700 transition-colors
                             disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="card p-4 border-red-200 bg-red-50">
              <div className="text-sm text-red-700 font-medium">Error</div>
              <div className="text-sm text-red-600 mt-1">{error}</div>
            </div>
          )}
        </section>

        {/* ── Trace + Result panel ────────────────────────────────── */}
        <section className="lg:col-span-2">
          {!response ? (
            <div className="card p-6 h-full flex flex-col items-center justify-center text-center min-h-[400px]">
              <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                <Sparkles className="w-7 h-7 text-slate-400" />
              </div>
              <h3 className="font-medium text-slate-700">Agent trace will appear here</h3>
              <p className="text-sm text-slate-500 mt-1 max-w-xs">
                Submit a request to see the audit findings, verdict, and final PO.
              </p>
            </div>
          ) : (
            <ResultPanel response={response} />
          )}
        </section>
      </div>
    </div>
  );
}


function ResultPanel({ response }: { response: ChatResponse }) {
  return (
    <div className="space-y-4 sticky top-6">
      {/* Verdict header */}
      <div className="card p-5">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs font-medium text-slate-500 mb-1">VERDICT</div>
            <div className="font-semibold text-slate-900">
              {response.verdict || "—"}
            </div>
            {response.iteration_count > 0 && (
              <div className="text-xs text-slate-500 mt-1">
                Self-correction iterations: {response.iteration_count}
              </div>
            )}
          </div>
          <StatusBadge status={response.final_status} size="md" />
        </div>
        {response.critic_summary && (
          <p className="text-sm text-slate-600 mt-3 leading-relaxed">
            {response.critic_summary}
          </p>
        )}
      </div>

      {/* Findings */}
      <div className="card p-5">
        <h3 className="font-medium text-slate-900 mb-3 text-sm">
          Audit findings ({response.findings.length})
        </h3>
        <div className="space-y-2">
          {response.findings.map((f, i) => (
            <div
              key={i}
              className={cn(
                "text-xs px-3 py-2 rounded-lg border-l-2",
                f.status === "pass"    && "bg-emerald-50 border-emerald-400 text-emerald-900",
                f.status === "fail"    && "bg-red-50    border-red-400    text-red-900",
                f.status === "warning" && "bg-amber-50  border-amber-400  text-amber-900",
              )}
            >
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-mono font-medium">{f.check_name}</span>
                <StatusBadge status={f.status} />
              </div>
              <div className="text-xs opacity-90">{f.finding}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Final PO */}
      {response.final_po && (
        <div className="card p-5">
          <h3 className="font-medium text-slate-900 mb-3 text-sm">
            Final PO · {response.final_po.po_number}
          </h3>
          <dl className="text-sm space-y-1.5">
            <Row label="Requester"  value={response.final_po.requester} />
            <Row label="Delivery"   value={response.final_po.delivery_address} />
            <Row label="Budget"     value={response.final_po.budget_code ?? "—"} />
            <Row label="Subtotal"   value={formatINR(response.final_po.subtotal)} />
            <Row label="GST"        value={formatINR(response.final_po.gst_amount)} />
            <Row label="Total"      value={formatINR(response.final_po.total_amount)} bold />
          </dl>

          <div className="mt-4">
            <div className="text-xs font-medium text-slate-500 mb-2">LINE ITEMS</div>
            <div className="space-y-1.5">
              {response.final_po.line_items.map((li, i) => (
                <div key={i} className="text-xs flex justify-between text-slate-600 py-1
                                         border-b border-slate-100 last:border-0">
                  <div>
                    <span className="font-mono text-slate-500">{li.sku}</span>
                    <span className="ml-2">×{li.quantity}</span>
                  </div>
                  <span className="font-medium text-slate-700">{formatINR(li.line_total)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className={cn("text-slate-900", bold && "font-semibold")}>{value}</dd>
    </div>
  );
}
