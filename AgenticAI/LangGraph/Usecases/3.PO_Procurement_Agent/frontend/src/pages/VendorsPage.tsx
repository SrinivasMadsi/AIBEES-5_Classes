// src/pages/VendorsPage.tsx
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import PageHeader from "@/components/PageHeader";
import { api } from "@/lib/api";

interface Vendor {
  id: number;
  name: string;
  approved_categories: string;
  payment_terms_days?: number;
  is_active?: boolean;
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.vendors()
      .then((v) => setVendors(v as Vendor[]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <PageHeader
        title="Approved Vendors"
        description="Vendor master. The Auditor verifies vendor selections against this list."
      />

      {loading ? (
        <div className="card p-12 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vendors.map((v) => (
            <div key={v.id} className="card p-5">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-medium text-slate-900">{v.name}</h3>
                <span className="badge badge-pass">Active</span>
              </div>
              <div className="text-xs text-slate-500 mb-1">APPROVED CATEGORIES</div>
              <div className="flex flex-wrap gap-1.5">
                {v.approved_categories.split(",").map((c) => (
                  <span key={c} className="badge badge-neutral">{c.trim()}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
