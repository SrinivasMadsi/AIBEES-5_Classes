// src/pages/ProductsPage.tsx
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import PageHeader from "@/components/PageHeader";
import { api } from "@/lib/api";
import { formatINR, cn } from "@/lib/format";
import type { Product } from "@/types/api";

export default function ProductsPage() {
  const [items, setItems] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");

  useEffect(() => {
    api.products()
      .then(setItems)
      .finally(() => setLoading(false));
  }, []);

  const filtered = items.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase())
    || p.sku.toLowerCase().includes(search.toLowerCase())
    || p.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <PageHeader
        title="Product Catalog"
        description="Source-of-truth pricing the Auditor checks against."
      />

      <div className="mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by SKU, name, or category…"
          className="w-full max-w-md px-3 py-2 border border-slate-300 rounded-lg text-sm
                     focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>

      {loading ? (
        <div className="card p-12 flex items-center justify-center text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr className="text-left text-xs font-medium text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Vendor</th>
                <th className="px-4 py-3 text-right">Price</th>
                <th className="px-4 py-3 text-right">Stock</th>
                <th className="px-4 py-3">Warehouse</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((p) => {
                const lowStock = p.units_in_stock !== null && p.reorder_threshold !== null
                  && p.units_in_stock < p.reorder_threshold;
                return (
                  <tr key={p.sku} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono text-xs">{p.sku}</td>
                    <td className="px-4 py-3 font-medium">{p.name}</td>
                    <td className="px-4 py-3">
                      <span className="badge badge-neutral">{p.category}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{p.vendor_name ?? "—"}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatINR(p.unit_price)}</td>
                    <td className={cn("px-4 py-3 text-right", lowStock && "text-amber-700 font-medium")}>
                      {p.units_in_stock ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{p.warehouse ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
