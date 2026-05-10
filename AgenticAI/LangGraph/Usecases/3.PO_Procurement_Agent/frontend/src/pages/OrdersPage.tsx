// src/pages/OrdersPage.tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, ExternalLink } from "lucide-react";

import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";
import { formatDate, formatINR } from "@/lib/format";
import type { OrderSummary } from "@/types/api";

export default function OrdersPage() {
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.orders()
      .then(setOrders)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <PageHeader
        title="Purchase Orders"
        description="All POs created or audited by the agent."
      />

      {loading && (
        <div className="card p-12 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
        </div>
      )}

      {error && (
        <div className="card p-6 border-red-200 bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-3">PO Number</th>
                <th className="px-4 py-3">Requester</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-center">Findings</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {orders.map((o) => (
                <tr key={o.po_number} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs">{o.po_number}</td>
                  <td className="px-4 py-3 text-slate-600">{o.requester}</td>
                  <td className="px-4 py-3 text-slate-600">{o.department ?? "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={o.status} /></td>
                  <td className="px-4 py-3 text-right font-medium">{formatINR(o.total_amount)}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="badge badge-neutral">{o.finding_count}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">{formatDate(o.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/orders/${o.po_number}`}
                      className="text-brand-600 hover:text-brand-700 inline-flex items-center gap-1 text-xs font-medium"
                    >
                      View <ExternalLink className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
              {orders.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                    No orders yet — submit one from the chat page.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
