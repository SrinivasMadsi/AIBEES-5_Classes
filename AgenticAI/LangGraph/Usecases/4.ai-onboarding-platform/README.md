# AI_Onboarding_Platform

**AI-assisted enterprise client onboarding platform** that automates BOM
(Business Operations Management) validation of IPM (Implementation Project
Manager) form submissions against SOP (Standard Operating Procedure)
documents — using a multi-agent LangGraph pipeline, MCP for SOP access,
human-in-the-loop for regulatory items, fault-tolerant checkpointing, and
Langfuse observability.

> The full agentic AI stack: multi-agent collaboration, MCP, HITL, fault
> tolerance, Langfuse, and a real Node-based UI.

---

## The use case

At one of the Healthcare clients(and any large enterprise onboarding clients onto a
platform), the workflow looks like this today:

1. **IPM** (Implementation Project Manager) fills out client configuration
   forms — Benefits & Services, Clinical, Accumulator, UMR, CDF, and so on
2. **BOM team** (Business Operations Management) manually validates that
   submission against SOP documents covering each domain
3. Issues bounce back and forth between IPM and BOM via email/tickets until
   the configuration is approved
4. Approved config flows downstream to provisioning

This is **slow, inconsistent, and bottlenecked by human availability**.

This platform automates the validation layer. When an IPM clicks Validate,
three AI agents collaborate to:

- Parse and structure the submission
- Detect the plan type and flag preliminary risk signals
- Fetch the relevant SOPs via MCP and apply rules deterministically
- Auto-correct fixable issues (with structured patches, not LLM guessing)
- Escalate regulatory/policy items to the BOM analyst for human review

The BOM analyst sees only the items that genuinely need human judgment.
Everything else is auto-resolved with a full audit trail.

---

## Project structure

```
ai-onboarding-platform/
│
├── backend/                          ← FastAPI + LangGraph (Python)
│   ├── agents/                       ← Three agent subgraphs
│   │   ├── intake/                   ← 🟡 Intake Agent
│   │   │   ├── graph.py              ← Subgraph builder
│   │   │   └── nodes/                ← Individual node implementations
│   │   ├── validation/               ← 🔵 Validation Agent
│   │   │   ├── graph.py
│   │   │   └── nodes/                ← Including fetch_sops_via_mcp
│   │   └── resolution/               ← 🟣 Resolution Agent
│   │       ├── graph.py
│   │       └── nodes/                ← Including escalate_to_BOM (HITL)
│   ├── api/                          ← FastAPI route modules
│   ├── config/                       ← Settings + LLM prompts
│   ├── core/                         ← DB, LLM, checkpointer, Langfuse, MCP client
│   ├── graph/                        ← Main graph orchestrating the 3 agents
│   ├── scripts/                      ← test_db, test_mcp, smoke_test
│   ├── main.py                       ← uvicorn entry point
│   └── pyproject.toml
│
├── mcp-servers/                      ← MCP servers (separate processes)
│   └── sop-mcp/                      ← The SOP MCP server
│       ├── server.py                 ← MCP server using stdio transport
│       ├── sops/                     ← SOP markdown files
│       │   ├── accumulator.md
│       │   ├── financial.md
│       │   └── clinical.md
│       └── pyproject.toml
│
├── frontend/                         ← React + Vite + Tailwind (Node/TypeScript)
│   ├── src/
│   │   ├── pages/                    ← IPM views + BOM views
│   │   ├── components/               ← FormRenderer, FindingCard, etc.
│   │   ├── lib/api.ts                ← Backend client
│   │   └── types/api.ts              ← TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
├── sql/                              ← Database schema + seed data
│   ├── 01_create_tables.sql
│   └── 02_seed_forms.sql
│
├── docs/                             ← Architecture, MCP explainer, demo script
│   ├── ARCHITECTURE.md
│   ├── HOW_MCP_WORKS.md
│   └── DEMO_SCRIPT.md
│
├── .env.example                      ← Template for environment variables
├── .gitignore
└── README.md                         ← You are here
```

---

## Architecture at a glance

```mermaid
flowchart TB
    subgraph FE["🟦 Frontend — React + Vite + Tailwind (port 5173)"]
        UI1[IPM Form Builder]
        UI2[BOM Review Queue]
    end

    subgraph BE["🟩 Backend — FastAPI + LangGraph (port 8000)"]
        API[REST API]
        subgraph GRAPH["Main Graph"]
            INTAKE[🟡 Intake Agent]
            VAL[🔵 Validation Agent]
            RES[🟣 Resolution Agent]
            FIN[Finalize]
        end
    end

    subgraph MCP["🟧 MCP Server — separate process"]
        SOP_MCP[sop-mcp server]
        SOPFILES[(SOPs folder<br/>markdown)]
    end

    subgraph DB["🟪 Postgres — Neon"]
        T1[(business_data<br/>tables)]
        T2[(checkpoints<br/>public schema)]
    end

    UI1 -->|HTTP| API
    UI2 -->|HTTP| API
    API --> GRAPH
    INTAKE --> VAL
    VAL <-->|MCP protocol| SOP_MCP
    SOP_MCP --> SOPFILES
    VAL --> RES
    RES --> FIN
    FIN --> T1
    GRAPH <-.->|checkpoint per node| T2
    GRAPH -.->|traces| LF[Langfuse Cloud]
```

For agent-level diagrams (per-agent subgraph internals), see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Tech stack — component by component

This project is built from **five distinct components**, each with its own
purpose and tech. Understanding the boundaries matters more than memorizing
package versions.

### 🟦 Frontend

| Aspect | Choice |
|---|---|
| Framework | React 18 |
| Build tool | Vite 5 |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 3 |
| Routing | React Router 6 |
| Icons | lucide-react |
| Port | 5173 (dev) |

The frontend is a **pure SPA** — it has no server-side rendering, no Node
runtime in production (just static files), and talks to the backend via
HTTP/JSON. Vite proxies `/api/*` to `http://localhost:8000` during dev.

Two distinct UI flows:

- **IPM views** (`pages/FormsListPage.tsx`, `FormFillPage.tsx`,
  `SubmissionsListPage.tsx`, `ValidationResultsPage.tsx`)
- **BOM analyst views** (`pages/BOMQueuePage.tsx`, `BOMReviewPage.tsx`)

### 🟩 Backend

| Aspect | Choice |
|---|---|
| Web framework | FastAPI 0.115 |
| Server | Uvicorn (ASGI) |
| Agent framework | LangGraph 0.3 |
| LLM SDK | langchain-google-vertexai |
| LLM model | Gemini 2.5 Pro (configurable) |
| ORM | SQLAlchemy 2.0 |
| DB driver | psycopg2-binary + psycopg (for checkpoints) |
| Settings | pydantic-settings |
| Dependency manager | Poetry |
| Python | 3.10–3.12 |
| Port | 8000 |

The backend is **stateless between requests** — all state lives in
Postgres (business data) and LangGraph checkpoints (agent state).

### 🟧 Agents (inside the backend)

Three agents, each a **LangGraph subgraph** with its own internal flow:

| Agent | Folder | Subgraph internal flow |
|---|---|---|
| 🟡 Intake | `backend/agents/intake/` | parse → check_completeness → classify_plan_type → detect_risk_signals → group_by_domain |
| 🔵 Validation | `backend/agents/validation/` | fetch_sops_via_mcp → apply_rules_to_answers → collect_findings |
| 🟣 Resolution | `backend/agents/resolution/` | categorize → generate_fixes → review → (mark_validated \| apply_auto_fixes \| escalate_to_BOM) |

Each agent is **independently compileable** and could be tested or reused
in other graphs. The main graph (`backend/graph/builder.py`) wires them
together with conditional edges and the self-correction loop.

### 🟪 MCP server

| Aspect | Choice |
|---|---|
| Protocol | Model Context Protocol (MCP) |
| SDK | `mcp` Python package |
| Transport | stdio (spawns server as subprocess) |
| Runtime | Separate Python process |
| Storage backend | Local markdown files |

The `sop-mcp` server (`mcp-servers/sop-mcp/server.py`) exposes four tools:

| Tool | Purpose |
|---|---|
| `list_sops` | Catalog of available SOPs |
| `get_sop_by_domain` | Full SOP markdown for a domain |
| `extract_rules_for_domain` | Structured rules parsed from a SOP |
| `search_sop_rules` | Free-text search across all SOPs |

**The agent never reads SOP files directly.** All access goes through the
MCP server, demonstrating the protocol pattern. Tomorrow these SOPs could
move to Confluence, SharePoint, or any system — only the MCP server
implementation changes, not the agent code.

See [`docs/HOW_MCP_WORKS.md`](docs/HOW_MCP_WORKS.md) for the full MCP
explainer.

### 🟫 SOPs (knowledge layer)

| Aspect | Choice |
|---|---|
| Format | Markdown |
| Location | `mcp-servers/sop-mcp/sops/` |
| Files | `accumulator.md`, `financial.md`, `clinical.md` |
| Access | Through the MCP server only |

The SOPs are **synthesized for the demo** — realistic UHC-style content
covering Accumulator, Out-of-Pocket, Deductible, Co-pay, Prior
Authorization, Utilization Management, Care Management, and Eligibility
rules. They're plain markdown so they can be diff'd, version-controlled,
and audited like any other text artifact.

### ⛔ Human-in-the-Loop (HITL)

HITL isn't a separate component — it's a **behavior built into the
Resolution Agent**.

When the critic verdict is `FAIL_REJECT` (regulatory or policy issues
that cannot be auto-corrected), the `escalate_to_BOM` node:

1. Inserts a row into `business_data.human_reviews` for each finding
2. Sets `submission.status = 'pending_human_review'`
3. Returns control to the main graph, which finalizes

The submission then **waits** for a BOM analyst to act:

- BOM analyst sees the item in `pages/BOMQueuePage.tsx`
- Opens the detail view (`pages/BOMReviewPage.tsx`)
- Picks one of: **Approve as-is**, **Reject (send back to IPM)**, **Override with comment**
- Decision is recorded via `POST /api/reviews/{id}/decision`
- When the last pending review for a submission is resolved, the submission
  status flips to `approved` or `rejected`

This design ensures:

- ✅ Regulatory violations always get human eyes
- ✅ Every decision is logged with reviewer identity, decision, and comment
- ✅ Submissions can wait days for human review without losing state
  (PostgresSaver checkpoints persist across crashes and restarts)

### Observability

| Aspect | Choice |
|---|---|
| Platform | Langfuse Cloud (v3) |
| Integration | `langfuse.langchain.CallbackHandler` |
| What's traced | Every node, every LLM call, every MCP call, every tool result |
| Format | Hierarchical span tree (Coordinator → its nodes → ...) |

Turn off via `LANGFUSE_ENABLED=false` in `.env` if not using Langfuse.

### Fault tolerance

`PostgresSaver` from `langgraph-checkpoint-postgres` checkpoints state
after **every node execution** — including inside subgraphs. Checkpoint
tables live in the `public` schema (not `business_data`), avoiding Neon
pooler search_path issues.

To resume a crashed validation, invoke the graph with the same
`thread_id`. The graph picks up from the last successful node.

---

## Setup — full installation walkthrough

This project has three runtime components: **backend (Python)**,
**mcp-server (Python)**, and **frontend (Node)**. Each has its own
dependencies. Follow these steps in order.

### Prerequisites

- **Python 3.10–3.12** with `python --version`
- **Node.js 18+** with `node --version` and `npm --version`
- **Poetry** (Python dependency manager): `pip install poetry`
- **A Neon Postgres database** (or any Postgres ≥ 13) — sign up at
  [neon.tech](https://neon.tech), it's free
- **A Google Cloud project** with Vertex AI API enabled
- **`gcloud` CLI** installed for ADC authentication
- _(Optional)_ **A Langfuse account** at [cloud.langfuse.com](https://cloud.langfuse.com) — also free

### Step 1 — Clone or extract this project

```bash
cd path/to/wherever-you-extracted-it
cd ai-onboarding-platform
```

### Step 2 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in:

```bash
# Database (use the same URL for both — one DB)
BUSINESS_DB_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
AGENT_DB_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require

# Google Cloud
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
LLM_MODEL=gemini-2.5-pro

# Langfuse (optional — set ENABLED=false if you don't use it)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com

# MCP path (default works for the included project layout)
SOP_MCP_SERVER_PATH=mcp-servers/sop-mcp/server.py
```

### Step 3 — Authenticate with Google Cloud

Run this once on your machine:

```bash
gcloud auth application-default login
```

This creates the credentials file the Vertex AI SDK picks up automatically.
You don't need an API key in code.

### Step 4 — Create the database schema

In the Neon SQL Editor (or any Postgres client), run these files in order:

1. `sql/01_create_tables.sql` — creates `business_data` schema + 6 tables
2. `sql/02_seed_forms.sql` — loads the 2 forms and 5 sample clients

Verify:

```bash
cd backend
poetry install     # (after this, see Step 5 below)
poetry run python scripts/test_db.py
```

You should see a row count summary of all tables.

### Step 5 — Install backend (Python) dependencies

From the project root:

```bash
cd backend
poetry install
```

This installs FastAPI, LangGraph, langchain-google-vertexai, SQLAlchemy,
psycopg, the MCP SDK, Langfuse, and everything else listed in
`backend/pyproject.toml`.

If you don't use Poetry, you can install with pip:

```bash
cd backend
pip install fastapi==0.115.0 "uvicorn[standard]==0.34.0" \
  "pydantic>=2.7,<3.0" "pydantic-settings>=2.10.1" python-dotenv==1.1.1 \
  langchain==0.3.27 langgraph==0.3.34 \
  langgraph-checkpoint-postgres==2.0.7 \
  "langchain-google-vertexai>=2.0.12" \
  sqlalchemy==2.0.36 psycopg2-binary==2.9.10 \
  "psycopg[binary,pool]==3.2.3" \
  "mcp>=1.0.0" "langfuse>=3.14.1" \
  sse-starlette==2.1.3
```

### Step 6 — Install MCP server (Python) dependencies

The sop-mcp server is a separate Python package with its own dependencies
(just `mcp`). It runs as a subprocess of the backend — you don't start it
manually for normal use.

```bash
cd ../mcp-servers/sop-mcp
poetry install
```

Or with pip:

```bash
pip install "mcp>=1.0.0"
```

Verify the MCP server works:

```bash
cd ../../backend
poetry run python scripts/test_mcp.py
```

You should see `list_sops` returning the catalog and
`extract_rules_for_domain('accumulator')` returning structured rules.

### Step 7 — Install frontend (Node) dependencies

```bash
cd ../frontend
npm install
```

This installs React, React Router, Vite, TypeScript, Tailwind CSS,
PostCSS, autoprefixer, and lucide-react.

If you prefer `yarn` or `pnpm`, those work too.

---

## Running the project

You'll need **two terminals open** simultaneously:

### Terminal 1 — Backend

```bash
cd backend
poetry run uvicorn main:app --reload --port 8000
```

Backend runs at <http://localhost:8000>. API docs at
<http://localhost:8000/docs>. Health check at <http://localhost:8000/health>.

The backend will spawn the `sop-mcp` server as a subprocess on demand —
you don't need to start it separately.

### Terminal 2 — Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at <http://localhost:5173>.

Open <http://localhost:5173> in your browser. You're ready.

---

## Quick smoke test

Without using the UI, you can run the whole agent pipeline end-to-end from
the command line:

```bash
cd backend
poetry run python scripts/smoke_test.py
```

This:

1. Inserts a hardcoded submission with intentional errors
2. Triggers the full graph (Intake → Validation → Resolution → Finalize)
3. Prints the final state with verdict, findings count, and human reviews

Expected outcome: verdict `FAIL_REJECT` (mid-year contract date triggers
the regulatory rule ACC-02), 1 human review created, ready for BOM
analyst action.

---

## The six concepts you'll demonstrate

| Concept | Where in the code | Where in the demo |
|---|---|---|
| **Multi-Agent Collaboration** | 3 agent subgraphs in `backend/agents/` | Logs scroll through Intake → Validation → Resolution |
| **MCP** | `mcp-servers/sop-mcp/` + `backend/core/mcp_client.py` | `🔌 calling sop-mcp server` in logs |
| **Human-in-the-Loop** | `escalate_to_BOM` node + BOM UI views | BOM analyst approves/rejects flagged items |
| **Fault Tolerance** | `backend/core/checkpointer.py` (PostgresSaver) | Kill backend mid-run; restart; resume |
| **Langfuse** | `backend/core/tracer.py` | Open dashboard, click latest trace |
| **UI with Node.js** | `frontend/` (React + Vite + Tailwind) | The two views students interact with |

For a step-by-step session walkthrough, see
[`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `cannot reach the database` | Bad `BUSINESS_DB_URL`, Neon paused | Run `python scripts/test_db.py`; wake Neon by opening SQL editor |
| `Module not found: mcp` | sop-mcp deps not installed | `cd mcp-servers/sop-mcp && poetry install` |
| `gcloud auth` error | No ADC credentials | Run `gcloud auth application-default login` |
| `Langfuse Auth: ❌ Failed` | Wrong keys | Check `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` in `.env`; or set `LANGFUSE_ENABLED=false` |
| Frontend can't reach API | Backend not running | Confirm `http://localhost:8000/health` returns OK |
| `relation "business_data.forms" does not exist` | SQL not run | Run `sql/01_create_tables.sql` then `02_seed_forms.sql` |
| Checkpointer error about search_path | Connection-string conflict | Already handled — checkpoint tables are in `public` schema |
| Smoke test says "Form 1005 not found" | Seed not loaded | Run `sql/02_seed_forms.sql` |

---

## Where to go next

- **Adding a new form** → insert into `business_data.forms`, no code change
- **Adding a new SOP** → drop a markdown file into `mcp-servers/sop-mcp/sops/`
  and update the `DOMAIN_TO_FILE` map in `server.py`
- **Adding a new agent** → create a subgraph under `backend/agents/<name>/`
  and add it as a node in `backend/graph/builder.py`
- **Replacing the SOP source** with real Confluence → swap `sop-mcp` for
  a `confluence-mcp` server; agent code unchanged
- **Adding a new MCP server** (CRM, Slack, etc.) → mirror the `sop-mcp`
  folder pattern; add an MCP client wrapper in `backend/core/`

---

## Purpose

Built for  covering the
agentic AI stack — LangGraph multi-agent subgraphs, MCP, HITL, fault
tolerance, and observability — applied to a realistic UnitedHealthcare-
style client onboarding scenario.
