# Architecture

A teaching reference for the multi-agent design used in this project.

---

## High-level flow

```
       Natural-language request
                │
                ▼
   ┌─────────────────────────────┐
   │   COMPOSER AGENT            │
   │                             │
   │  intake → enrichment →      │
   │  vendor_mapping → tax_calc  │
   │  → assembler                │
   └────────────┬────────────────┘
                │  draft PO
                ▼
   ┌─────────────────────────────┐
   │   AUDITOR AGENT             │
   │                             │
   │  inventory_check →          │
   │  price_check →              │
   │  policy_check →             │
   │  schema_check →             │
   │  critic                     │
   └────────────┬────────────────┘
                │
        ┌───────┴────────┐
        │                │
   FAIL_FIXABLE       PASS / PASS_WITH_WARNINGS / FAIL_REJECT
        │                │
        ▼                ▼
   ┌──────────┐    ┌────────────┐
   │ self-    │    │ finalize   │
   │ correct  │───▶│            │
   └──────────┘    └────────────┘
   (max 1 retry)
```

---

## Concept-by-concept mapping

This single project demonstrates five concepts students often see described separately. Knowing where each one lives in the code makes the conceptual ladder concrete.

### 1. Workflow

**Definition:** A fixed pipeline of steps decided by the developer.

**In this project:** The Composer's internal node sequence — `intake → enrichment → vendor_mapping → tax_calc → assembler` — is a workflow. Every PO goes through these five steps in this order. The LLM doesn't choose what comes next; the graph does.

**Where to look:** `graph/builder.py`, the linear `add_edge(...)` calls inside the Composer section.

### 2. AI Agent

**Definition:** An LLM that decides which tool to call and when, given a goal.

**In this project:** Each Composer node is a small agent in its own right. `enrichment.py`, for example, is given a goal ("find the SKU"), tools (database query, LLM matcher), and decides how to combine them. The full Composer is the workflow *of* these mini-agents.

**Where to look:** `agents/composer/enrichment.py` — read it top to bottom. It queries DB, asks the LLM, parses, retries.

### 3. Multi-Agent System

**Definition:** Multiple specialized agents collaborating with role separation.

**In this project:** Composer and Auditor are two distinct agents with different roles, different prompts, different tools, and a clean state-based handoff. Composer builds; Auditor verifies. Neither knows the other's internals.

**Where to look:** `graph/builder.py`. The transition from `assembler` to `inventory_check` is the agent boundary.

### 4. Reflection (Reflection Agent pattern)

**Definition:** An agent critiques its own output before finalizing.

**In this project:** The `critic` node in `agents/auditor/critic.py` reads the four deterministic check findings, reasons about them, and produces a structured verdict. This is reflection — the system asking "given everything I've found, what should I conclude?" before committing.

**Where to look:** `agents/auditor/critic.py`. Note how it combines deterministic logic (verdict from finding statuses) with LLM reasoning (human-readable summary).

### 5. Self-Correction

**Definition:** The system catches a mistake and fixes it without human intervention.

**In this project:** When the Auditor's critic emits `FAIL_FIXABLE`, the `self_correction` node applies structured patches and the graph loops back into `tax_calc` for re-assembly and re-audit. **The crucial design choice:** patches come from the deterministic checks (catalog price, current stock), not from LLM opinion. This is what makes self-correction grounded rather than hallucinated.

**Where to look:**
- `graph/self_correction.py` — patch application
- `graph/builder.py` — the conditional edge `_route_after_critic` deciding loop vs. finalize
- `agents/auditor/critic.py` — how patches are emitted

---

## The two-schema database design

```
neondb (one Postgres database)
├── business_data  ← application tables: vendors, products, …
└── agent_state    ← LangGraph checkpoints (auto-managed)
```

**Why two schemas, not two databases:**

| Concern | One DB, two schemas | Two databases |
|---|---|---|
| Operational simplicity | ✅ One backup, one connection pool | ❌ Doubled |
| Atomic transactions across both | ✅ Possible | ❌ Distributed-tx pain |
| Cost on hosted platforms | ✅ One instance | ❌ Two instances |
| Schema isolation | ✅ Postgres `SCHEMA` provides it | ✅ Native |

This is the standard pattern teams running LangGraph in production use. We're showing students the right thing.

---

## Fault tolerance

LangGraph's `PostgresSaver` checkpoints state after every node. If a run crashes mid-execution, you re-invoke with the same `thread_id` and the graph picks up from the last successful checkpoint.

**API surface:**
- `POST /api/chat` — new run, generates a `thread_id`
- `POST /api/chat/resume?thread_id=...` — resume from checkpoint

**State that survives a crash:**
- All Composer outputs (parsed intake, enriched items, vendor mapping, tax breakdown, draft PO)
- All Auditor findings up to the failed node
- The `iteration_count` (so self-correction limit is respected on resume)

**State that does not survive a crash:**
- In-flight LLM API calls (those re-execute after resume — idempotent)

---

## Observability

Langfuse v3 is wired in via the `Tracer` class in `core/tracer.py`. Every graph invocation produces a single trace tree showing:

- The full Composer pipeline as nested spans
- Each Auditor check as its own span
- The critic's reasoning + token usage
- Self-correction iterations as a sub-tree

Combined with the `audit_log` table in Postgres, this gives both **runtime** observability (Langfuse traces) and **historical** observability (audit_log queries).

---

## Where to extend

| Feature | Where to add it |
|---|---|
| Another Auditor check | New file in `agents/auditor/`, register in `graph/builder.py` |
| More patches the system can auto-apply | `graph/self_correction.py` `apply_patches()` |
| Different LLM | Change `LLM_MODEL` in `.env` |
| Migrate to self-hosted Postgres | Change `BUSINESS_DB_URL` and `AGENT_DB_URL` |
| Additional UI page | New file in `frontend/src/pages/`, add route to `App.tsx` |
| New API endpoint | New router in `backend/api/`, mount in `main.py` |

The architecture is intentionally modular so students can add features without touching the core graph.
