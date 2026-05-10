// src/pages/OrderDetailPage.tsx
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";

import PageHeader from "@/components/PageHeader";
import StatusBadge from "@/components/StatusBadge";
import { api } from "@/lib/api";
import { formatDate, formatINR, cn } from "@/lib/format";
import type { Finding, PurchaseOrder } from "@/types/api";

export default function OrderDetailPage() {
  const { poNumber = "" } = useParams();
  const [order, setOrder] = useState<PurchaseOrder | null>(null);
  const [audit, setAudit] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.order(poNumber), api.orderAudit(poNumber)])
      .then(([o, a]) => {
        setOrder(o);
        setAudit(a);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [poNumber]);

  if (loading) {
    return (
      <div className="p-8">
        <div className="card p-12 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <Link to="/orders" className="text-brand-600 text-sm inline-flex items-center gap-1 mb-4">
          <ArrowLeft className="w-4 h-4" /> Back to orders
        </Link>
        <div className="card p-6 border-red-200 bg-red-50 text-red-700 text-sm">
          {error ?? "Not found"}
        </div>
      </div>
    );
  }

  // payload may carry the original line_items; fall back to top-level
  const payload = (order as any).payload ?? order;
  const lineItems = payload.line_items ?? order.line_items ?? [];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <Link to="/orders" className="text-brand-600 text-sm inline-flex items-center gap-1 mb-4">
        <ArrowLeft className="w-4 h-4" /> Back to orders
      </Link>

      <PageHeader
        title={order.po_number}
        description={`Requested by ${order.requester}`}
        action={<StatusBadge status={order.status} size="md" />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PO Body */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h3 className="font-medium mb-4">Purchase Order Details</h3>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              <Field label="Delivery"   value={payload.delivery_address ?? "—"} />
              <Field label="Budget"     value={(order as any).budget_code ?? "—"} />
              <Field label="Subtotal"   value={formatINR(payload.subtotal)} />
              <Field label="GST"        value={formatINR(payload.gst_amount)} />
              <Field label="Total"      value={formatINR(payload.total_amount)} />
              <Field label="Currency"   value={payload.currency ?? "INR"} />
            </dl>
          </div>

          <div className="card p-6">
            <h3 className="font-medium mb-4">Line Items</h3>
            <table className="w-full text-sm">
              <thead className="text-xs text-slate-500 uppercase">
                <tr>
                  <th className="text-left  py-2">SKU</th>
                  <th className="text-left  py-2">Name</th>
                  <th className="text-right py-2">Qty</th>
                  <th className="text-right py-2">Unit</th>
                  <th className="text-right py-2">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lineItems.map((li: any, i: number) => (
                  <tr key={i}>
                    <td className="py-2 font-mono text-xs">{li.sku}</td>
                    <td className="py-2">{li.name}</td>
                    <td className="py-2 text-right">{li.quantity}</td>
                    <td className="py-2 text-right">{formatINR(li.unit_price)}</td>
                    <td className="py-2 text-right font-medium">{formatINR(li.line_total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Audit timeline */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-6">
            <h3 className="font-medium mb-4">Audit Trail</h3>
            <div className="space-y-3">
              {audit.length === 0 ? (
                <div className="text-sm text-slate-500">No audit entries yet.</div>
              ) : (
                audit.map((f, i) => (
                  <div key={i} className="relative pl-4 pb-3 border-l-2 border-slate-100">
                    <div className={cn(
                      "absolute -left-1.5 top-1 w-3 h-3 rounded-full",
                      f.status === "pass"    && "bg-emerald-500",
                      f.status === "fail"    && "bg-red-500",
                      f.status === "warning" && "bg-amber-500",
                    )} />
                    <div className="text-xs font-mono text-slate-500 mb-0.5">
                      {f.check_name}
                    </div>
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={f.status} />
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">{f.finding}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-slate-900 font-medium text-right">{value}</dd>
    </>
  );
}
