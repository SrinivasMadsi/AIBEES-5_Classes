# Classroom Demo Script

A 15-minute walkthrough you can use to teach the five concepts in one go.

## Pre-class setup (5 min before students arrive)

1. Both backend and frontend running
2. Neon SQL Editor open in a separate tab
3. Langfuse dashboard open (if using)
4. The frontend's `Submit Request` page visible

## Demo flow

### Part 1 — Show the workflow (3 min)

Open the **Product Catalog** page.

> *"This is the source-of-truth our agent will check against. Real product names, real prices, real stock levels — pulled from a real Postgres database in the cloud."*

Open the **Budgets** page.

> *"And these are the budget allocations. The agent will check PO totals against these."*

This sets context: students see the *truth* before they see the agent reasoning about it.

### Part 2 — A clean run (3 min)

Go to **Submit Request** and paste:

> *"Order 5 Dell Latitude 5450 laptops, 5 Logitech MX Master mice, and 5 Logitech K380 keyboards for the Hyderabad office. Charge to budget PO-2026-Q2-0847."*

While it runs, narrate:

> *"Watch the right panel. The Composer agent extracts the items, finds them in the catalog, picks the right vendors, computes GST. Then the Auditor agent runs four parallel checks. Then a critic synthesizes the verdict."*

Show the result — should be PASS, all green.

### Part 3 — Self-correction (the headline moment, 5 min)

Switch to the **Neon SQL Editor** tab. Run:

```sql
SET search_path TO business_data;

UPDATE products
SET unit_price = 36000
WHERE sku = 'DELL-MON-32';

-- Verify
SELECT sku, name, unit_price FROM products WHERE sku = 'DELL-MON-32';
```

> *"I just changed the catalog price. The PO request the user is about to send will use the OLD price they think is correct. The agent's job is to catch this."*

Switch back to the frontend and submit:

> *"Order 10 Dell 32-inch 4K Monitors at ₹34,000 each for the Hyderabad office. Use budget PO-2026-Q2-0847."*

Watch carefully. You should see:

1. Composer assembles the PO with the user's stated price
2. Auditor's price check **FAILS** — finding the catalog mismatch
3. Critic emits a patch: `{"action": "update_price", "sku": "DELL-MON-32", "new_price": 36000}`
4. Self-correction node applies the patch
5. Pipeline loops back through tax_calc, re-audits
6. Now PASSES
7. Final PO submitted with the corrected price

The Findings panel shows the full audit trail including the `self_correction` step — visually, students see the agent catch and fix its own mistake.

### Part 4 — Open Langfuse (2 min)

Show the trace in Langfuse. Point out:

- The full graph execution as a tree
- Each node's input/output
- Token counts and latency
- The two iterations clearly visible

> *"This is what production observability looks like. Every decision the agent made is captured, traceable, debuggable."*

### Part 5 — The teaching wrap-up (2 min)

Bring back the architecture diagram and connect:

| What we just saw | What it's called |
|---|---|
| Composer's 5-step pipeline | Workflow |
| Each step calling an LLM with tools | AI Agent |
| Composer + Auditor handoff | Multi-Agent System |
| Critic synthesizing findings | Reflection |
| Catalog-grounded patch application | Self-Correction |

> *"All five concepts in one project, against a real database, with real fault tolerance. This is what enterprise agentic AI actually looks like."*

## Cleanup

Reset the catalog price for next time:

```sql
SET search_path TO business_data;

UPDATE products SET unit_price = 34000 WHERE sku = 'DELL-MON-32';
```

## Variations to try

Once students are comfortable, ask "what would happen if…" questions:

| Modification | Expected behavior |
|---|---|
| User asks for 100 of something with stock 30 | Auditor flags `reduce_quantity` patch, self-corrects |
| User uses a non-existent budget code | `FAIL_REJECT` (no auto-fix possible) |
| User asks for 200 laptops | Hits `max_qty_per_line` rule → `FAIL_REJECT` |
| Two simultaneous price mismatches | Multiple patches applied in one self-correction iteration |
| Set `MAX_SELF_CORRECTION_ITERATIONS=0` in `.env` | Even fixable failures become `FAIL_REJECT` — students see why the loop matters |

Each variation deepens understanding without writing new code.
