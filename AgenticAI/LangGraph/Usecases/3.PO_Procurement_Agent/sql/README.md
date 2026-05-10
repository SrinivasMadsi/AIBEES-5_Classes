# SQL Files for Neon Postgres Setup

Run these in order, top to bottom, in the **Neon SQL Editor**.

| # | File | Purpose | Rows inserted |
|---|---|---|---|
| 1 | `01_create_tables.sql` | Creates all 8 business tables, constraints, and indexes | — |
| 2 | `02_seed_master_data.sql` | Seeds vendors, products, inventory, budgets, tax rules, business rules | 54 |
| 3 | `03_seed_purchase_orders.sql` | Seeds 6 purchase orders covering every realistic state | 6 |
| 4 | `04_seed_audit_log.sql` | Seeds 24 audit findings, including the self-correction sequence for PO-005 | 24 |

**Order matters.** Files 03 and 04 reference data inserted by earlier files via foreign keys.

For full setup instructions including Neon signup, schema creation, and verification, see `../docs/NEON_SETUP_GUIDE.md`.

## Quick reset

To clear everything and start over:

```sql
SET search_path TO business_data;

TRUNCATE TABLE
    audit_log,
    purchase_orders,
    business_rules,
    tax_rules,
    budget_codes,
    inventory,
    products,
    vendors
RESTART IDENTITY CASCADE;
```

Then re-run files 02, 03, 04 (the table structure stays intact).

To drop everything including tables:

```sql
DROP SCHEMA business_data CASCADE;
DROP SCHEMA agent_state   CASCADE;
```

Then re-run files 01 through 04.
