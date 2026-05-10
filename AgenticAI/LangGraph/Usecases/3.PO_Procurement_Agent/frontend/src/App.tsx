// src/App.tsx
import { Link, NavLink, Route, Routes } from "react-router-dom";
import {
  Bot,
  Boxes,
  ClipboardList,
  LayoutDashboard,
  PackageSearch,
  Wallet,
} from "lucide-react";

import ChatPage from "@/pages/ChatPage";
import OrdersPage from "@/pages/OrdersPage";
import OrderDetailPage from "@/pages/OrderDetailPage";
import ProductsPage from "@/pages/ProductsPage";
import VendorsPage from "@/pages/VendorsPage";
import BudgetsPage from "@/pages/BudgetsPage";
import { cn } from "@/lib/format";

const NAV = [
  { to: "/",          label: "Submit Request", icon: Bot },
  { to: "/orders",    label: "Purchase Orders", icon: ClipboardList },
  { to: "/products",  label: "Product Catalog", icon: PackageSearch },
  { to: "/vendors",   label: "Vendors",         icon: Boxes },
  { to: "/budgets",   label: "Budgets",         icon: Wallet },
];

export default function App() {
  return (
    <div className="min-h-screen flex">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col">
        <div className="px-6 py-6 border-b border-slate-800">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-brand-600 flex items-center justify-center">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <div>
              <div className="font-semibold leading-tight">PO Agent</div>
              <div className="text-xs text-slate-400">AIBees Academy</div>
            </div>
          </Link>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-4 border-t border-slate-800 text-xs text-slate-500">
          v0.1.0 · Vertex AI · Neon Postgres
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/"                    element={<ChatPage />} />
          <Route path="/orders"              element={<OrdersPage />} />
          <Route path="/orders/:poNumber"    element={<OrderDetailPage />} />
          <Route path="/products"            element={<ProductsPage />} />
          <Route path="/vendors"             element={<VendorsPage />} />
          <Route path="/budgets"             element={<BudgetsPage />} />
        </Routes>
      </main>
    </div>
  );
}
