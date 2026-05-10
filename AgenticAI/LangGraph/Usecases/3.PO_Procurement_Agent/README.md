# Intelligent Purchase Order Agent

An end-to-end agentic AI system that converts natural-language procurement requests into validated, ERP-ready Purchase Orders, with built-in self-correction against deterministic enterprise data sources.

---

## Table of Contents

1. [Use Case Overview](#use-case-overview)
2. [What This System Demonstrates](#what-this-system-demonstrates)
3. [System Architecture](#system-architecture)
4. [Agent Execution Flow](#agent-execution-flow)
5. [Request Lifecycle](#request-lifecycle)
6. [Repository Layout](#repository-layout)
7. [Prerequisites](#prerequisites)
8. [Setup — Step by Step](#setup--step-by-step)
9. [Running the Application](#running-the-application)
10. [Testing the Application](#testing-the-application)
11. [Demoing Self-Correction](#demoing-self-correction)
12. [Extending the System](#extending-the-system)
13. [Troubleshooting](#troubleshooting)
14. [Daily Development Workflow](#daily-development-workflow)

---

## Use Case Overview

### The problem

In every enterprise, procurement teams convert business requests like *"we need 50 laptops for the new Hyderabad office"* into formal Purchase Orders that can be sent to ERP systems (SAP, Oracle, etc.). This involves several manual steps:

- Identifying the right product SKUs from the catalog
- Verifying stock availability across warehouses
- Confirming prices match current vendor quotations
- Selecting an approved vendor for the category
- Calculating taxes (GST) based on delivery region
- Checking that totals stay within approved budget allocations
- Ensuring quantities don't exceed per-line policy limits
- Producing JSON conforming to the ERP's exact schema

Doing this manually for every request is slow, error-prone, and doesn't scale. A naive automation that just generates a PO from the request is even worse — it produces plausible-looking output that may have wrong prices, exceed budgets, or order out-of-stock items.

### The solution

This system uses **two specialized AI agents** that collaborate:

- The **Composer Agent** parses the request, looks up products, computes taxes, and assembles a draft PO.
- The **Auditor Agent** verifies that draft against deterministic enterprise data — inventory, catalog prices, budgets, business policies, and ERP schema rules.

When the Auditor finds a fixable problem (like a quantity exceeding stock), it generates a structured patch. The system applies the patch and re-validates — **self-correction grounded in real data, not LLM opinion**.

When the Auditor finds an unfixable problem (like a quantity exceeding policy limits), it correctly escalates to human review rather than auto-fixing.

### Example interaction

A user submits:

> *"Order 15 Dell OptiPlex 7010 desktops for the Hyderabad office. Use budget PO-2026-Q2-0847."*

The system:

1. Extracts items, resolves SKUs from the catalog, picks an approved vendor, computes 18% GST for Telangana, assembles a draft PO
2. Runs four checks: inventory, price, policy, schema
3. Detects only 8 units of `DELL-OPT-7010` are in stock — fails the inventory check
4. Generates patch: `{action: "reduce_quantity", sku: "DELL-OPT-7010", new_quantity: 8}`
5. Applies the patch, recomputes totals, re-runs all four checks
6. All checks pass → submits the corrected PO with 8 units to the ERP

The user sees a final PO and the full audit trail, including the self-correction step.

---

## What This System Demonstrates

| Concept | Where it lives in the code |
|---|---|
| **Workflow** | The Composer's internal pipeline (`intake → enrichment → vendor_mapping → tax_calc → assembler`) is a fixed, deterministic sequence — the developer decides the path, not the LLM. |
| **AI Agent** | Each Composer/Auditor sub-node is an LLM call with tools (database queries, prompt templates) that decides what to do based on the input. |
| **Multi-Agent System** | Composer and Auditor are two distinct agents with different roles, prompts, and tools. They communicate via a shared state — neither knows the other's internals. |
| **Reflection** | The Auditor's `critic` node reads the four check findings and synthesizes a verdict — the agent reasoning about its own intermediate output before finalizing. |
| **Self-correction** | When the critic emits `FAIL_FIXABLE`, the `self_correction` node applies structured patches and the graph loops back. Patches come from deterministic checks, not LLM guesses. |
| **Persistent state** | LangGraph's `PostgresSaver` checkpoints state after every node. If a run crashes, you resume from the last successful node using the same `thread_id`. |
| **Observability** | Langfuse v3 captures every LLM call, every node, every iteration as a hierarchical trace. |

---

## System Architecture

The system has three layers — UI, agent backend, and data store. Each layer is independent: you can swap the frontend (e.g., to a Slack bot), swap the LLM provider, or migrate the database without rewriting the others.

```mermaid
flowchart TB
    subgraph FE["Frontend — React + Vite"]
        UI["Chat UI · Trace Panel · Reference Data Browser"]
    end

    subgraph BE["Backend — FastAPI + LangGraph"]
        direction TB
        API["REST API endpoints"]

        subgraph COMPOSER["Composer Agent"]
            direction LR
            C1[intake] --> C2[enrichment] --> C3[vendor_mapping] --> C4[tax_calc] --> C5[assembler]
        end

        subgraph AUDITOR["Auditor Agent"]
            direction LR
            A1[inventory_check] --> A2[price_check] --> A3[policy_check] --> A4[schema_check] --> A5[critic]
        end

        SC[self_correction]
        FIN[finalize]

        API --> COMPOSER
        COMPOSER --> AUDITOR
        AUDITOR -->|FAIL_FIXABLE| SC
        SC -->|loop back| COMPOSER
        AUDITOR -->|PASS / FAIL_REJECT| FIN
    end

    subgraph DB["Neon Postgres"]
        direction LR
        BD[("business_data schema:<br/>vendors, products,<br/>inventory, budgets,<br/>tax rules, etc.")]
        AS[("agent_state schema:<br/>LangGraph<br/>checkpoints")]
    end

    LF["Langfuse Cloud<br/>(observability)"]
    VAI["Vertex AI<br/>Gemini 2.5 Pro"]

    FE <-->|HTTP| API
    BE <-->|SQL| BD
    BE <-->|checkpoints| AS
    BE -.->|traces| LF
    BE -.->|LLM calls| VAI

    classDef agent fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef datastore fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
    classDef external fill:#f3e8ff,stroke:#7e22ce,stroke-width:2px,color:#581c87
    classDef ui fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class FE ui
    class COMPOSER,AUDITOR,SC,FIN agent
    class DB datastore
    class LF,VAI external
```

---

## Agent Execution Flow

This is the actual LangGraph wiring — the path data takes from a user request to a final PO. The dashed line is the self-correction loop, which runs only when the critic emits `FAIL_FIXABLE`.

```mermaid
flowchart TD
    START([User request received]) --> intake

    subgraph composer["Composer Agent — builds the draft PO"]
        intake[intake<br/>parse NL → JSON]
        enrichment[enrichment<br/>resolve SKUs from catalog]
        vendor_mapping[vendor_mapping<br/>fetch approved vendor]
        tax_calc[tax_calc<br/>compute GST per region]
        assembler[assembler<br/>build PO JSON]

        intake --> enrichment --> vendor_mapping --> tax_calc --> assembler
    end

    subgraph auditor["Auditor Agent — verifies the draft"]
        inventory_check[inventory_check<br/>stock vs. requested qty]
        price_check[price_check<br/>PO price vs. catalog]
        policy_check[policy_check<br/>budget · qty limits · vendor]
        schema_check[schema_check<br/>ERP schema validation]
        critic[critic<br/>synthesize verdict + patches]

        inventory_check --> price_check --> policy_check --> schema_check --> critic
    end

    assembler --> inventory_check

    critic --> decision{verdict?}
    decision -->|PASS / WARNINGS| finalize
    decision -->|FAIL_REJECT| finalize
    decision -->|FAIL_FIXABLE<br/>and iter < max| self_correction

    self_correction[self_correction<br/>apply patches] -.->|loop back| tax_calc

    finalize([finalize<br/>submit / reject / escalate]) --> END([End])

    classDef startEnd fill:#e2e8f0,stroke:#475569,stroke-width:2px,color:#1e293b
    classDef composerNode fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef auditorNode fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef correctNode fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#831843
    classDef branch fill:#f1f5f9,stroke:#64748b,color:#334155

    class START,END,finalize startEnd
    class intake,enrichment,vendor_mapping,tax_calc,assembler composerNode
    class inventory_check,price_check,policy_check,schema_check,critic auditorNode
    class self_correction correctNode
    class decision branch
```

---

## Request Lifecycle

This shows what happens when a user clicks **Submit** in the UI — every component involved, every external call. Useful for understanding where to debug if something goes wrong.

```mermaid
sequenceDiagram
    autonumber
    participant U as User<br/>(Browser)
    participant FE as Frontend<br/>(React/Vite)
    participant BE as Backend<br/>(FastAPI)
    participant LG as LangGraph<br/>Engine
    participant DB as Neon<br/>Postgres
    participant LLM as Vertex AI<br/>Gemini
    participant LF as Langfuse<br/>Cloud

    U->>FE: Submits PO request
    FE->>BE: POST /api/chat
    BE->>LG: graph.invoke(state, thread_id)

    Note over LG: Composer Agent runs
    LG->>LLM: intake — parse request
    LG->>DB: enrichment — find SKUs
    LG->>DB: vendor_mapping — fetch vendor
    LG->>DB: tax_calc — fetch GST rates
    LG->>LG: assembler — build PO JSON

    Note over LG: Auditor Agent runs
    LG->>DB: inventory_check
    LG->>DB: price_check
    LG->>DB: policy_check (budgets, rules)
    LG->>LG: schema_check
    LG->>LLM: critic — synthesize verdict

    alt verdict == FAIL_FIXABLE
        LG->>LG: self_correction — apply patches
        Note over LG: Loop back to tax_calc;<br/>re-run audit chain
        LG->>DB: re-validate (all 4 checks)
        LG->>LLM: critic — final verdict
    end

    LG->>DB: checkpoint state (PostgresSaver)
    LG-->>LF: trace (every node, async)
    LG->>BE: final PO + findings
    BE->>FE: 200 OK with response
    FE->>U: render result
```

---

## Repository Layout

```
po-agent/
├── backend/                  ← Python: FastAPI + LangGraph
│   ├── agents/
│   │   ├── composer/         ← Composer sub-nodes
│   │   └── auditor/          ← Auditor sub-nodes
│   ├── api/                  ← FastAPI route handlers
│   ├── config/               ← settings, prompts
│   ├── core/                 ← db, llm, checkpointer, tracer
│   ├── graph/                ← LangGraph builder, state, self-correction
│   ├── scripts/              ← test_db.py, smoke_test.py
│   ├── main.py               ← uvicorn entry point
│   ├── pyproject.toml
│   └── README.md
│
├── frontend/                 ← React + Vite + TypeScript
│   ├── src/
│   │   ├── components/       ← reusable UI bits
│   │   ├── pages/            ← one file per route
│   │   ├── lib/              ← API client, formatters
│   │   └── types/            ← TypeScript types
│   ├── package.json
│   └── README.md
│
├── sql/                      ← Database schema + seed data
│   ├── 01_create_tables.sql
│   ├── 02_seed_master_data.sql
│   ├── 03_seed_purchase_orders.sql
│   ├── 04_seed_audit_log.sql
│   └── README.md
│
├── docs/
│   ├── NEON_SETUP_GUIDE.md   ← detailed Neon walkthrough
│   ├── ARCHITECTURE.md       ← deeper design notes
│   └── DEMO_SCRIPT.md        ← classroom demo script
│
├── .env.example
├── .gitignore
└── README.md                 ← this file
```

---

## Prerequisites

Before starting, you need:

| Tool | Version | How to check | If missing |
|---|---|---|---|
| Python | 3.10+ | `python --version` | Install from [python.org](https://www.python.org/downloads/) |
| Poetry | 1.8+ | `poetry --version` | `pip install poetry` |
| Node.js | 18+ | `node --version` | See "Install Node.js" step below |
| gcloud CLI | any recent | `gcloud --version` | [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install) |

You also need:

- A **Neon Postgres** account — free, sign up at [neon.tech](https://neon.tech)
- A **Google Cloud project** with **Vertex AI API enabled**
- Optional: a **Langfuse Cloud** account for tracing — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)

---

## Setup — Step by Step

Follow these steps in order. Skipping or reordering steps will cause errors.

### Step 1 — Set up the database

Follow `docs/NEON_SETUP_GUIDE.md` end-to-end. It walks you through:

- Creating a Neon account and project
- Creating the two schemas (`business_data` and `agent_state`)
- Running the four SQL files in `sql/` in order to create tables and seed data
- Retrieving your connection string

When you finish, you should have a Neon project with 8 tables populated with realistic data.

### Step 2 — Authenticate with Vertex AI

```powershell
gcloud auth application-default login
```

A browser opens for sign-in. After completing it, credentials are stored at `~/.config/gcloud/application_default_credentials.json`. The backend's `ChatVertexAI` client picks them up automatically — no API keys go in code.

Verify your active GCP project:

```powershell
gcloud config get-value project
```

Whatever this prints is your `GCP_PROJECT_ID`. Note it for Step 3.

### Step 3 — Create the `.env` file

Place a file named `.env` at the **project root**:

```
D:\path\to\PO_Agent_Usecase\po-agent\.env
```

Not inside `backend/` or `frontend/` — at the root of `po-agent/`.

Paste this template and fill in your values:

```bash
# ─── Neon Postgres ───────────────────────────────────────────────────────
# Same connection string for both. Copy from Neon dashboard.
BUSINESS_DB_URL=postgresql://YOUR_USER:YOUR_PASS@ep-XXXXX.region.aws.neon.tech/neondb?sslmode=require
AGENT_DB_URL=postgresql://YOUR_USER:YOUR_PASS@ep-XXXXX.region.aws.neon.tech/neondb?sslmode=require

# ─── Google Cloud / Vertex AI ────────────────────────────────────────────
GCP_PROJECT_ID=your-actual-gcp-project-id
GCP_LOCATION=us-central1
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.0

# ─── Langfuse (optional) ─────────────────────────────────────────────────
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# ─── App configuration ───────────────────────────────────────────────────
MAX_SELF_CORRECTION_ITERATIONS=1
DEFAULT_REGION=Telangana
DEFAULT_WAREHOUSE=Hyderabad-WH1
LOG_LEVEL=INFO

# ─── Frontend ────────────────────────────────────────────────────────────
VITE_API_URL=http://localhost:8000
```

If you don't want Langfuse traces, set `LANGFUSE_ENABLED=false` and leave the keys blank.

### Step 4 — Install backend dependencies

From the project root:

```powershell
cd backend
poetry add sqlalchemy==2.0.36
poetry add psycopg2-binary==2.9.10
poetry add "psycopg[binary,pool]==3.2.3"
poetry add langgraph-checkpoint-postgres==2.0.7
poetry add "pydantic-settings>=2.10.1,<2.11.0"
poetry add sse-starlette==2.1.3
poetry add fastapi==0.115.0
```

These are the new dependencies needed for this project. If your `pyproject.toml` already has the foundation packages (langchain, langgraph, langchain-google-vertexai, langfuse), they remain untouched.

### Step 5 — Verify the database connection

```powershell
python .\backend\scripts\test_db.py
```

Expected output:

```
Testing Neon connection…
✅ Connection OK

Table                    Rows
--------------------------------
vendors                     6
products                   15
inventory                  15
budget_codes                4
tax_rules                  11
business_rules              3
purchase_orders             6
audit_log                  24

✅ All tables reachable.
```

If this succeeds, your `.env`, your auth, and your data are all wired correctly. If you see errors, re-check your `.env` values.

### Step 6 — Install Node.js (only if not already installed)

Verify with `node --version`. If it errors out, install Node:

1. Go to <https://nodejs.org>
2. Click the **LTS** download (currently v20.x or v22.x)
3. Run the `.msi` installer:
   - Welcome → Next
   - License → Accept → Next
   - Destination folder → keep default (`C:\Program Files\nodejs\`) → Next
   - Custom Setup → keep all defaults → Next
   - Tools for Native Modules → leave **unchecked** → Next
   - Install → Yes to UAC prompt → Finish
4. **Close all PowerShell windows and reopen them** — the new PATH only takes effect in fresh shells. If using VS Code, close VS Code completely and reopen it.
5. Verify:
   ```powershell
   node --version
   npm --version
   ```

### Step 7 — Install frontend dependencies

```powershell
cd frontend
npm install
```

This installs React, Vite, Tailwind, and all UI dependencies (~200 MB into `node_modules/`). Takes 1-2 minutes the first time.

### Step 8 — Run the smoke test

This proves the entire backend works end-to-end before you bring up the UI:

```powershell
python .\backend\scripts\smoke_test.py
```

Expected output (abbreviated):

```
======================================================================
REQUEST: Need 5 Dell Latitude 5450 laptops, 5 Logitech MX Master mice...
======================================================================

[composer.intake] parsing user request
  → 3 item(s) parsed
[composer.enrichment] resolving SKUs
  ✓ 'Dell Latitude 5450 laptops' → DELL-LAT-5450 (high)
  ...
[auditor.inventory_check] verifying stock
  → PASS
[auditor.price_check] verifying prices
  → PASS
[auditor.policy_check] verifying policies
  → PASS
[auditor.schema_check] validating schema
  → PASS
[auditor.critic] reasoning over findings
  → verdict=PASS  patches=0
[finalize] producing final output
  → submitted: PO-20260509-XXXXXX
```

If you see this, the backend agent stack works. Move on to running the application.

---

## Running the Application

You need **two terminals** running at the same time.

### Terminal 1 — Backend

```powershell
cd D:\path\to\PO_Procurement_Agent_Usecase\backend
python -m uvicorn main:app --reload --port 8000
```

Expected output:

```
INFO:     Will watch for changes in these directories: ['…\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
🔍 Langfuse Auth: ✅ Connected      (or ❌ Failed if Langfuse keys are wrong)
INFO:     Application startup complete.
```

Keep this terminal running. Open <http://localhost:8000/docs> in your browser to confirm the FastAPI Swagger UI loads.

### Terminal 2 — Frontend

In a **new terminal** window (don't close Terminal 1):

```powershell
cd D:\path\to\PO_Procurement_Agent_Usecase\frontend
npm run dev
```

Expected output:

```
  VITE v5.4.10  ready in 412 ms

  ➜  Local:   http://localhost:5173/
```

Keep this terminal running too. Open <http://localhost:5173> in your browser. You should see the PO Agent UI with a sidebar on the left.

---

## Testing the Application

Test in this order — each step builds confidence the previous layer works.

### Test 1 — Backend health

Open <http://localhost:8000/health> in your browser. Expected response:

```json
{
  "status": "ok",
  "db": "ok",
  "llm_model": "gemini-2.5-pro",
  "langfuse": true
}
```

If `db` says `"unreachable"`, your `BUSINESS_DB_URL` is wrong.

### Test 2 — Reference data endpoints

In the Swagger UI at <http://localhost:8000/docs>:

1. Click **GET `/api/products`** → **Try it out** → **Execute**. Expected: a JSON array with 15 products.
2. Click **GET `/api/orders`** → **Try it out** → **Execute**. Expected: 6 purchase orders.

### Test 3 — Run the agent via Swagger

Click **POST `/api/chat`** → **Try it out**. Replace the body with:

```json
{
  "message": "Order 5 Dell Latitude 5450 laptops, 5 Logitech MX Master mice, and 5 Logitech K380 keyboards for the Hyderabad office. Charge to budget PO-2026-Q2-0847.",
  "user_id": "test-user"
}
```

Click **Execute**. Takes 10-30 seconds. Watch Terminal 1 — you'll see live agent execution scrolling.

The Swagger response panel shows the final PO with verdict, findings, and total. If you see `"final_status": "submitted"`, the entire agent stack works.

### Test 4 — UI

In your browser at <http://localhost:5173>:

1. Click any sample request to populate the textarea
2. Click **Submit**
3. Watch the right panel populate with verdict, findings, and final PO

Click around the sidebar to verify the navigation pages all load:

- **Operations**: Submit Request, Purchase Orders, Audit Log
- **Reference Data**: Product Catalog, Inventory, Vendors, Budgets
- **Configuration**: Tax Rules, Business Rules

### Test 5 — Langfuse traces (if enabled)

Open <https://cloud.langfuse.com> → **Traces**. You should see one trace per chat request, with the full execution tree (Composer → Auditor → critic → finalize) as nested spans, including token counts and latency per node.

---

## Demoing Self-Correction

The headline feature of this system is the agent catching and fixing its own mistakes. Here are two scenarios to try.

### Scenario A — Self-corrects via reduce_quantity

Open the frontend and the Neon SQL Editor side by side.

**Step 1.** Confirm `DELL-OPT-7010` has 8 units in stock:

```sql
SET search_path TO business_data;
SELECT sku, units_in_stock, warehouse FROM inventory WHERE sku = 'DELL-OPT-7010';
```

**Step 2.** Submit a PO request where the order quantity exceeds available inventory:

```
Order 15 Dell OptiPlex 7010 desktops for the Hyderabad office. Use budget PO-2026-Q2-0847.
```

**Step 3.** Watch the Findings panel:

- `inventory_check` **fails** — requested 15, only 8 available
- Reasoning critic generates a `reduce_quantity` patch
- `self_correction` step **passes** — patch applied
- `inventory_check` **passes** on re-validation
- All other checks pass
- Final verdict: **PASS**, iteration count: **1**

**Step 4.** The Final PO panel shows **8 units instead of 15** — the agent reduced the order to match available stock.

**Step 5.** Open Langfuse to see the full trace tree showing both iterations and the self-correction span.

### Scenario B — When self-correction is NOT appropriate

Some failures shouldn't be auto-corrected — they need human approval. Show the contrast:

Submit:

```
Order 200 Dell Latitude 5450 laptops for the Hyderabad office. Use budget PO-2026-Q2-0623.
```

Watch:

- `policy_check` fails because quantity exceeds the `max_qty_per_line` rule (limit: 100 for laptops)
- The critic produces a `manual_approval_required` patch — NOT a fixable type
- The graph routes to finalize without looping back
- Verdict: **FAIL_REJECT**, status: **needs_human**

This demonstrates that the agent knows the difference between failures it can fix (inventory mismatch) and failures it shouldn't touch (policy violations). Auto-correcting a policy violation would be a bug; escalating it to humans is the correct behavior.

---

## Checkpointer (LangGraph state persistence)

### How it works

LangGraph's `PostgresSaver` writes checkpoint data to your Neon database after
every agent node executes. This enables fault tolerance — if a run crashes,
you can resume from any successful node using the same `thread_id`.

The checkpointer stores its tables in the `public` schema:
- `checkpoints` — full state snapshot per node
- `checkpoint_writes` — diffs between snapshots
- `checkpoint_blobs` — large state values
- `checkpoint_migrations` — internal LangGraph version tracking

These tables are created automatically the first time `get_checkpointer()`
runs (which happens on the first `/api/chat` request after backend startup).
You don't need to create them manually.

### Verifying the checkpointer is working

After running a chat request, confirm the tables exist and are populated:

```sql
-- Are the tables there?
SELECT schemaname, tablename
FROM pg_tables
WHERE tablename LIKE 'checkpoint%'
ORDER BY schemaname;
```

Expected output:
```
schemaname | tablename
-----------+----------------------
public     | checkpoint_blobs
public     | checkpoint_migrations
public     | checkpoint_writes
public     | checkpoints
```

```sql
-- Are checkpoints being written?
SELECT COUNT(*) FROM public.checkpoints;
SELECT COUNT(*) FROM public.checkpoint_writes;
SELECT COUNT(*) FROM public.checkpoint_blobs;
```

After each chat request, expect roughly **12 rows added** to `checkpoints`
(one per graph node). All three counts should be > 0 after even one request.

### Inspecting a specific run

Each chat request gets a unique `thread_id` returned in the API response.
Use it to inspect that run's state history:

```sql
SELECT
    thread_id,
    checkpoint_id,
    created_at,
    metadata->>'source' AS triggered_by
FROM public.checkpoints
WHERE thread_id = 'po-XXXXX-XXXXX-XXXXX'
ORDER BY created_at;
```

Each row shows one node's state snapshot. You'll see the agent move through
intake → enrichment → ... → finalize, with timestamps for each step.

### Resume capability

You can replay a thread from any checkpoint. From a Python REPL with the venv
active:

```python
from graph.builder import get_graph

graph = get_graph()
state = graph.get_state({"configurable": {"thread_id": "po-XXXXX"}})
print(state.values)  # full state of that thread
print(state.next)    # which node would run next
```

This is how production agentic systems achieve fault tolerance — every node's
output is durable before the next node starts.

### Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `relation "checkpoints" does not exist` | First chat request hasn't run yet | Submit any chat request to trigger setup |
| `checkpoints` table exists but is empty | LangGraph isn't using the checkpointer | Verify `build_graph(use_checkpointer=True)` in `graph/builder.py` |
| Checkpoint tables in wrong schema | Old code may have created them in `business_data` or `agent_state` | Drop them and let `get_checkpointer()` recreate in `public` (see below) |

If checkpoint tables somehow ended up in the wrong schema, drop and recreate:

```sql
-- Drop from any wrong schema
DROP TABLE IF EXISTS business_data.checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS business_data.checkpoint_migrations CASCADE;
DROP TABLE IF EXISTS business_data.checkpoint_writes CASCADE;
DROP TABLE IF EXISTS business_data.checkpoints CASCADE;
DROP TABLE IF EXISTS agent_state.checkpoint_blobs CASCADE;
DROP TABLE IF EXISTS agent_state.checkpoint_migrations CASCADE;
DROP TABLE IF EXISTS agent_state.checkpoint_writes CASCADE;
DROP TABLE IF EXISTS agent_state.checkpoints CASCADE;

-- Verify clean slate
SELECT schemaname, tablename FROM pg_tables WHERE tablename LIKE 'checkpoint%';
```

Then restart uvicorn and submit a chat request. Tables will be auto-created
in `public`.
---

## Daily Development Workflow

After initial setup, your routine is:

```powershell
# Terminal 1 — backend
cd D:\path\to\po-agent\backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd D:\path\to\po-agent\frontend
npm run dev
```

Open <http://localhost:5173>, work, `Ctrl+C` both terminals when done.

---
