// src/types/api.ts
// TypeScript types matching the FastAPI response shapes.

export interface Finding {
  check_name: string;
  status: "pass" | "fail" | "warning";
  finding: string;
  suggested_fix: Record<string, unknown> | null;
}

export interface LineItem {
  sku: string;
  name: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface PurchaseOrder {
  po_number: string;
  requester: string;
  delivery_address: string;
  budget_code: string | null;
  line_items: LineItem[];
  subtotal: number;
  gst_amount: number;
  total_amount: number;
  currency: string;
  status: string;
  region?: string;
}

export interface ChatResponse {
  thread_id: string;
  final_status: string;
  final_po: PurchaseOrder | null;
  findings: Finding[];
  verdict: string;
  critic_summary: string;
  iteration_count: number;
}

export interface Product {
  sku: string;
  name: string;
  category: string;
  unit_price: number;
  currency: string;
  vendor_name: string | null;
  units_in_stock: number | null;
  warehouse: string | null;
  reorder_threshold: number | null;
}

export interface OrderSummary {
  po_number: string;
  requester: string;
  status: string;
  total_amount: number | null;
  budget_code: string | null;
  department: string | null;
  created_at: string;
  finding_count: number;
}

export interface Budget {
  code: string;
  department: string;
  fiscal_quarter: string;
  approved_amount: number;
  spent_amount: number;
  available: number;
}
