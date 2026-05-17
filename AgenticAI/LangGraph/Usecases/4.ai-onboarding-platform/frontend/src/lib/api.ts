// API client wrapping fetch calls to the backend.

import type {
  Client,
  FormConfig,
  FormSummary,
  Review,
  ReviewDetail,
  Submission,
  ValidationResult,
} from "../types/api";

const BASE = ""; // vite proxy forwards /api to localhost:8000

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Forms ──────────────────────────────────────────────────────────────────
export const listForms = () => getJson<FormSummary[]>("/api/forms");
export const getForm = (formId: number) => getJson<{ form_id: number; form_name: string; version: string; config: FormConfig }>(`/api/forms/${formId}`);

// ── Clients ────────────────────────────────────────────────────────────────
export const listClients = () => getJson<Client[]>("/api/clients");

// ── Submissions ────────────────────────────────────────────────────────────
export const listSubmissions = () => getJson<Submission[]>("/api/submissions");
export const getSubmission = (id: string) => getJson<Submission>(`/api/submissions/${id}`);

export const createSubmission = (data: {
  client_id: string;
  client_name: string;
  form_id: number;
  form_version: string;
  submitted_by: string;
  answers: Record<string, unknown>;
}) =>
  postJson<{ submission_id: string; thread_id: string; status: string }>(
    "/api/submissions",
    data,
  );

export const validateSubmission = (id: string) =>
  postJson<ValidationResult>(`/api/submissions/${id}/validate`, {});

// ── Reviews (HITL) ─────────────────────────────────────────────────────────
export const listReviews = () => getJson<Review[]>("/api/reviews");
export const getReview = (id: number) => getJson<ReviewDetail>(`/api/reviews/${id}`);

export const submitReviewDecision = (
  id: number,
  body: { reviewed_by: string; decision: "approve" | "reject" | "override"; comment: string },
) =>
  postJson<{ review_id: number; review_status: string; submission_id: string; pending_left: number }>(
    `/api/reviews/${id}/decision`,
    body,
  );
