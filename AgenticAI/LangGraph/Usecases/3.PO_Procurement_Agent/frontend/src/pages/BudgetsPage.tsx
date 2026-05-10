// src/pages/BudgetsPage.tsx
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import PageHeader from "@/components/PageHeader";
import { api } from "@/lib/api";
import { formatINR, cn } from "@/lib/format";
import type { Budget } from "@/types/api";

export default function BudgetsPage() {
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.budgets()
      .then(setBudgets)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <PageHeader
        title="Budget Allocations"
        description="Active budgets the Auditor checks PO totals against."
      />

      {loading ? (
        <div className="card p-12 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="space-y-3">
          {budgets.map((b) => {
            const pct = (b.spent_amount / b.approved_amount) * 100;
            const danger = pct > 80;
            return (
              <div key={b.code} className="card p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="font-mono text-xs text-slate-500">{b.code}</div>
                    <div className="font-medium text-slate-900">{b.department}</div>
                    <div className="text-xs text-slate-500">{b.fiscal_quarter}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-500">Available</div>
                    <div className="font-semibold text-emerald-700">{formatINR(b.available)}</div>
                  </div>
                </div>

                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all",
                      danger ? "bg-red-500" : pct > 60 ? "bg-amber-500" : "bg-emerald-500"
                    )}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>

                <div className="flex justify-between mt-2 text-xs text-slate-500">
                  <span>Spent: {formatINR(b.spent_amount)}</span>
                  <span>Approved: {formatINR(b.approved_amount)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
