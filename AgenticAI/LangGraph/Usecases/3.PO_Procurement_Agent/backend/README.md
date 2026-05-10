# The Purchase Order Agent — Use Case
- In any enterprise, procurement teams convert business requests like "we need 50 laptops for the new Hyderabad office" into formal Purchase Orders that get sent to ERP systems like SAP or Oracle. This involves identifying the right product SKUs from the catalog, verifying stock availability, confirming current vendor prices, picking an approved vendor, calculating regional taxes, checking that totals fit within budget allocations, ensuring quantities don't exceed policy limits, and producing JSON that conforms to the ERP's exact schema. Doing this manually is slow and error-prone. A naive LLM-based automation is even worse — it produces plausible-looking POs that may have hallucinated prices, exceed budgets, or order out-of-stock items.
- This system solves the problem with two specialized AI agents that collaborate. The Composer Agent parses the natural-language request, looks up products, picks vendors, computes taxes, and assembles a draft PO. The Auditor Agent then verifies that draft against deterministic enterprise data — inventory levels, catalog prices, budget balances, business policies, and ERP schema rules. When the Auditor finds a fixable problem (like a quantity exceeding stock), it generates a structured patch that the system applies and re-validates — self-correction grounded in real data, not LLM opinion. When the Auditor finds an unfixable problem (like a quantity exceeding policy limits), it correctly escalates to human review rather than auto-fixing. The user gets back a final PO with the full audit trail, including any self-correction steps that occurred along the way.



# Backend — Purchase Order Agent

FastAPI service running the LangGraph multi-agent system.

## Folder structure

```
backend/
├── agents/
│   ├── composer/         ← Composer Agent: builds the PO
│   │   ├── intake.py        - parses NL request to structured items
│   │   ├── enrichment.py    - resolves SKUs from catalog
│   │   ├── vendor_mapping.py- selects approved vendor per item
│   │   ├── tax_calc.py      - computes GST per region/category
│   │   └── assembler.py     - assembles the final PO JSON
│   │
│   └── auditor/          ← Auditor Agent: verifies the PO
│       ├── inventory_check.py  - stock vs requested qty
│       ├── price_check.py      - PO price vs catalog price
│       ├── policy_check.py     - budget, qty limits, vendor rules
│       ├── schema_check.py     - ERP schema conformance
│       └── critic.py           - reasoning + patch generation
│
├── api/                  ← FastAPI endpoints
│   ├── routes_chat.py       - POST /chat  → invoke agent
│   ├── routes_data.py       - GET data for UI panels
│   └── streaming.py         - SSE streaming of agent steps
│
├── config/
│   ├── settings.py          - centralized env loader
│   └── prompts.py           - all LLM prompts
│
├── core/
│   ├── db.py                - SQLAlchemy engine, session
│   ├── models.py            - ORM models for business_data tables
│   ├── llm.py               - ChatVertexAI factory
│   ├── checkpointer.py      - PostgresSaver factory
│   └── tracer.py            - Langfuse v3 wrapper
│
├── graph/
│   ├── state.py             - PO state TypedDict
│   ├── builder.py           - composes Composer + Auditor subgraphs
│   └── self_correction.py   - patch + loop logic
│
├── scripts/
│   ├── test_db.py           - quick DB sanity check
│   └── smoke_test.py        - end-to-end agent run from CLI
│
├── main.py                  - uvicorn entry point
└── pyproject.toml
```

---

## The Two Agents

This system uses two specialized agents that collaborate. The **Composer**
builds, the **Auditor** verifies. This separation is what makes the system
trustworthy in production: even if the Composer hallucinates a price or picks
the wrong vendor, the Auditor catches it against ground truth in the database.

| Agent | Role | Goal |
|---|---|---|
| **Composer** | Builder | Convert natural-language request into a structured draft PO |
| **Auditor** | Verifier | Check the draft against deterministic rules and produce a verdict |

---

## Composer Agent — 5 nodes that build the PO

The Composer takes a free-form text request and produces a structured,
ERP-ready draft. Each node is one specialized step in the pipeline.

### Node 1 — `intake.py`

**What it does:** Parses the user's natural-language message into structured JSON.

**Input:** A sentence like *"Order 15 Dell OptiPlex 7010 desktops for the Hyderabad office. Use budget PO-2026-Q2-0847."*

**What it extracts:**
- Requester (email or name, if mentioned)
- Delivery location (city or office)
- Budget code
- A list of items, each with `description` and `quantity`

**Uses LLM:** Yes — the LLM is given a strict prompt asking for JSON output.

**Why it's separate:** Free-form text is messy. By isolating this step, the
rest of the pipeline only deals with clean, structured data. If parsing
fails, the failure point is unambiguous.

### Node 2 — `enrichment.py`

**What it does:** Resolves each item description to an actual SKU in the catalog.

**Input:** The list of items from intake (e.g., `"Dell OptiPlex 7010 desktops"`, quantity 15).

**Steps for each item:**
1. Fetches the entire product catalog from `business_data.products`
2. Asks the LLM: *"Match this item description to one of these 15 SKUs"*
3. The LLM returns the matching SKU with a confidence level (high/medium/low)
4. Looks up the matched SKU's full record (price, vendor, category)

**Uses LLM:** Yes — fuzzy matching needs language understanding. Users say
"Dell OptiPlex 7010 desktops" or "those Dell PCs we ordered last quarter,"
not "DELL-OPT-7010".

### Node 3 — `vendor_mapping.py`

**What it does:** Confirms the approved vendor for each item and attaches vendor details.

**Input:** Enriched items with `approved_vendor_id`.

**What it does:** For each unique vendor, fetches the vendor's full record
from `business_data.vendors` (name, address, payment terms, contact). Attaches
this to the item so the final PO contains real vendor data, not just IDs.

**Uses LLM:** No — pure database lookup, deterministic.

### Node 4 — `tax_calc.py`

**What it does:** Computes GST (Indian sales tax) for each line item based on the delivery region.

**Input:** Enriched items + delivery location.

**Steps:**
1. Looks up the GST rate for each (region, category) combination from `business_data.tax_rules`
2. For Telangana + desktops: rate is 18%
3. Calculates: `tax_amount = quantity × unit_price × rate / 100`
4. Adds `tax_rate` and `tax_amount` to each line item

**Uses LLM:** No — pure calculation against the rules table.

**Note:** This is the node the **self-correction loop returns to** —
because if a price or quantity changes during correction, taxes need to be
recomputed before re-auditing.

### Node 5 — `assembler.py`

**What it does:** Builds the final PO JSON in the exact shape the ERP expects.

**Input:** All the enriched data from previous nodes.

**Steps:**
1. Generates a unique PO number (`PO-20260509-XXXXXX`)
2. Sums line item totals into `subtotal`
3. Sums tax amounts into `gst_amount`
4. Computes `total_amount = subtotal + gst_amount`
5. Wraps everything in the ERP's expected JSON structure
6. Sets initial status to `"draft"`

**Uses LLM:** No — pure assembly.

**Why it's a separate node:** The ERP has a specific schema. This node is
the single source of truth for that schema. If the ERP changes its required
fields, you only update this node.

---

## Auditor Agent — 5 nodes that verify the PO

The Auditor takes the draft PO and runs four independent checks, then a
critic that reasons over all findings to produce a verdict + patch list.

### Node 1 — `inventory_check.py`

**What it does:** Verifies that requested quantities are actually available in the warehouse.

**Steps for each line item:**
1. Queries `business_data.inventory` for the SKU
2. Compares `quantity` requested to `units_in_stock`
3. Three possible outcomes:
   - **PASS** if stock ≥ quantity AND remaining stock > reorder threshold
   - **WARNING** if stock ≥ quantity BUT remaining stock would dip below reorder threshold
   - **FAIL** if stock < quantity, with `suggested_fix: {action: "reduce_quantity", new_quantity: <stock>}`

**Uses LLM:** No — pure SQL comparison.

**Why the suggested fix is a structured JSON object:** the self-correction
node can apply it mechanically. The LLM doesn't decide what to do — the rule does.

### Node 2 — `price_check.py`

**What it does:** Verifies that the PO's unit prices match the current catalog.

**Steps for each line item:**
1. Fetches current `unit_price` from `business_data.products`
2. Compares to PO's price
3. If different, FAIL with `suggested_fix: {action: "update_price", new_price: <catalog_price>}`

**Uses LLM:** No.

**Why it matters:** The Composer uses the latest catalog price during
enrichment, so this check usually passes. But if catalog prices change
between drafting and submission (or if the user states a wrong price
in their request), this catches the drift.

### Node 3 — `policy_check.py`

**What it does:** Enforces business rules, budget limits, and vendor approvals.

**What it checks (in order):**
1. **Budget exists:** Does `budget_code` resolve to a real budget in `business_data.budget_codes`?
2. **Budget capacity:** Does `(approved_amount - spent_amount) ≥ total_amount`?
3. **Quantity limits:** For each line, is quantity ≤ `max_qty_per_line` from `business_data.business_rules`? (e.g., laptops capped at 100/PO)
4. **Value limits:** Is `total_amount` ≤ `max_po_value` rule?
5. **Vendor approval:** Is the chosen vendor in the approved list for this category?

**For each violation:** Generates a finding with a `suggested_fix` of type
`manual_approval_required` (NOT `update_price` or `reduce_quantity`). This
signals to the critic that the failure isn't auto-fixable.

**Uses LLM:** No.

**Why this is the most important check:** Policy violations are exactly
what shouldn't be auto-corrected. An agent that bypasses budget or quantity
limits is a bug, not a feature. The Auditor catches these and refuses to
self-correct them.

### Node 4 — `schema_check.py`

**What it does:** Validates that the draft PO conforms to the ERP's expected JSON schema.

**What it checks:**
- Required fields present (po_number, requester, line_items, total_amount, etc.)
- Data types correct (numbers are numbers, dates are dates, strings non-empty)
- Numeric constraints (quantities > 0, prices ≥ 0)
- Sums consistent (subtotal + gst_amount = total_amount)

**Uses LLM:** No — usually a Pydantic model validation.

**Why it's last:** If previous checks modified anything via patches, this
catches any structural drift before submission. It's the final guard
against malformed JSON reaching the ERP.

### Node 5 — `critic.py`

**What it does:** Reads all four check findings and produces a single verdict + patch list.

**Steps:**
1. Sends the findings to the LLM with a critic prompt
2. The LLM reasons: *"Looking at these findings, what's the right action?"*
3. Returns one of four verdicts:

| Verdict | When | What happens next |
|---|---|---|
| `PASS` | All checks passed | Goto `finalize`, submit PO |
| `PASS_WITH_WARNINGS` | All FAIL-free, but warnings present | Goto `finalize`, submit anyway |
| `FAIL_FIXABLE` | Fixable failure (price/quantity), iter < max | Goto `self_correction`, apply patches, loop back |
| `FAIL_REJECT` | Unfixable failures (policy/schema) or max iterations exhausted | Goto `finalize`, mark as `needs_human` |

**Also returns:** A list of `patches` to apply (only when verdict is
`FAIL_FIXABLE`). Patches are the structured fixes from earlier checks
(`update_price`, `reduce_quantity`).

**Uses LLM:** Yes — this is the agent's "reflection" moment. The system
reasons about its own intermediate output. Not "what did the user ask?"
but *"given what we found, what should we do about it?"*

**Why use an LLM here:** Could be hand-coded with rules, but the LLM makes
verdict logic flexible. New check types can be added without hardcoding new
verdict rules — the critic adapts.

---

## After the Auditor — what happens next

The graph branches based on the critic's verdict:

| Critic verdict | Routed to | Result |
|---|---|---|
| `PASS` / `PASS_WITH_WARNINGS` / `FAIL_REJECT` | `finalize` node | Final state recorded; agent done |
| `FAIL_FIXABLE` (and iter < max) | `self_correction` node | Patches applied; loop back to `tax_calc`; full audit re-runs |

**`self_correction` node:**
1. Takes each patch (`update_price`, `reduce_quantity`) and modifies the corresponding line item in the draft PO
2. Increments `iteration_count`
3. Returns control to `tax_calc` — because changing price or quantity invalidates tax calculations

**`finalize` node:**
1. Sets the PO's final status (`submitted` / `needs_human` / `rejected`)
2. Persists the PO and audit log in `business_data`
3. Returns the response to the API

---

## Quick reference — what each node uses

| Agent | Node | LLM? | Reads from DB | Writes anything |
|---|---|---|---|---|
| Composer | intake | ✅ | – | – |
| Composer | enrichment | ✅ | products | – |
| Composer | vendor_mapping | ❌ | vendors | – |
| Composer | tax_calc | ❌ | tax_rules | – |
| Composer | assembler | ❌ | – | – |
| Auditor | inventory_check | ❌ | inventory | – |
| Auditor | price_check | ❌ | products | – |
| Auditor | policy_check | ❌ | budget_codes, business_rules | – |
| Auditor | schema_check | ❌ | – | – |
| Auditor | critic | ✅ | – | – |
| (post) | self_correction | ❌ | – | Modifies state |
| (post) | finalize | ❌ | – | Saves PO + audit_log |

The pattern: **LLM at the boundaries** (parsing fuzzy input, reasoning over
findings), **deterministic SQL in the middle** (reliable lookups). LLMs
handle ambiguity; SQL handles ground truth.

---

# What this demonstrates
This single use case demonstrates every important agentic AI concept:

- Workflow — the Composer's deterministic pipeline (intake → enrichment → vendor → tax → assembler)
- AI Agent — each node that uses the LLM to make decisions
- Multi-agent system — Composer and Auditor with different roles, prompts, and shared state
- Reflection — the critic reasoning over its own intermediate findings
- Self-correction — patches grounded in deterministic data sources, applied automatically
- Persistent state — LangGraph checkpointing for fault-tolerant resume
- Observability — Langfuse traces showing every LLM call and node execution
---


## Setup

### Install dependencies

```bash
cd backend
poetry install
```

If you don't use Poetry:

```bash
pip install -e .
```

### Configure environment

The backend reads `../.env` from the project root. Copy `../.env.example` to `../.env` and fill in your values.

### Authenticate with Vertex AI

One-time setup:

```bash
gcloud auth application-default login
```

This creates `~/.config/gcloud/application_default_credentials.json`. The backend uses Application Default Credentials — no API keys in code.

### Verify database connection

```bash
poetry run python scripts/test_db.py
```

Expected output: a row count summary of all 8 business tables.

## Run

```bash
python -m uvicorn main:app --reload --port 8000
```

- Backend: <http://localhost:8000>
- Interactive docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

## Smoke test

Run the agent end-to-end without the UI:

```bash
python scripts/smoke_test.py
```

This submits a hardcoded PO request, runs both agents, and prints the trace.

## Key endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/chat` | Submit a PO request, get the final PO |
| POST | `/api/chat/stream` | Same, but streams agent steps via SSE |
| GET | `/api/products` | List products (for UI Reference Data page) |
| GET | `/api/vendors` | List vendors |
| GET | `/api/inventory` | List inventory snapshot |
| GET | `/api/orders` | List recent purchase orders |
| GET | `/api/orders/{po_number}/audit` | Audit findings for a PO |

## Resuming a failed run

If the agent crashes mid-execution, re-invoke with the same `thread_id`:

```python
config = {"configurable": {"thread_id": "po-2026-007"}}
graph.invoke(state, config=config)   # resumes from last checkpoint
```

This is exposed via `POST /api/chat/resume?thread_id=...` in the API.
