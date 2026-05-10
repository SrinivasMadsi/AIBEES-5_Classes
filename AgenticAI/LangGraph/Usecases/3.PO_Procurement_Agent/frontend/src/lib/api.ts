// src/lib/api.ts
// Typed wrapper around fetch for the backend API.
import type {
  Budget,
  ChatResponse,
  Finding,
  OrderSummary,
  Product,
  PurchaseOrder,
} from "@/types/api";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function http<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // ── Chat ──────────────────────────────────────────────────────────────────
  chat: (message: string, threadId?: string) =>
    http<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message,
        thread_id: threadId ?? null,
        user_id: "ui-user",
      }),
    }),

  resume: (threadId: string) =>
    http<ChatResponse>(`/api/chat/resume?thread_id=${encodeURIComponent(threadId)}`, {
      method: "POST",
    }),

  // ── Reference data ────────────────────────────────────────────────────────
  products:  () => http<Product[]>("/api/products"),
  vendors:   () => http<{ id: number; name: string; approved_categories: string }[]>("/api/vendors"),
  inventory: () => http<Product[]>("/api/inventory"),
  budgets:   () => http<Budget[]>("/api/budgets"),

  // ── Orders ────────────────────────────────────────────────────────────────
  orders:    () => http<OrderSummary[]>("/api/orders"),
  order:     (poNumber: string) => http<PurchaseOrder>(`/api/orders/${poNumber}`),
  orderAudit: (poNumber: string) =>
    http<Finding[]>(`/api/orders/${poNumber}/audit`),

  // ── Health ────────────────────────────────────────────────────────────────
  health: () => http<{ status: string; db: string; llm_model: string; langfuse: boolean }>("/health"),
};
