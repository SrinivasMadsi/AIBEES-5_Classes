# Neon Postgres Setup Guide
## Cloud database backbone for the Intelligent Purchase Order Agent

**Audience:** AIBees Academy students and instructors
**Time required:** ~15 minutes end-to-end
**Outcome:** A fully populated, cloud-hosted Postgres database holding business data and ready to back LangGraph agent state.

---

## Table of Contents

1. [Why Neon](#1-why-neon)
2. [Prerequisites](#2-prerequisites)
3. [Sign Up and Create Your Project](#3-sign-up-and-create-your-project)
4. [Retrieve and Save Your Connection String](#4-retrieve-and-save-your-connection-string)
5. [Create the Two Schemas](#5-create-the-two-schemas)
6. [Create the Business Tables](#6-create-the-business-tables)
7. [Insert the Seed Data](#7-insert-the-seed-data)
8. [Verify Everything Works](#8-verify-everything-works)
9. [Connecting from Python](#9-connecting-from-python)
10. [Useful Day-to-Day Queries](#10-useful-day-to-day-queries)
11. [Troubleshooting](#11-troubleshooting)
12. [Folder Structure for Your Repo](#12-folder-structure-for-your-repo)

---

## 1. Why Neon

Neon is an open-source, serverless Postgres hosted in the cloud. We chose it for this project because:

- **Open source** — the data is portable; you can move to self-hosted Postgres any time without rewriting a line of code.
- **Generous free tier** — 10 projects, 0.5 GB storage each, no credit card, no expiry.
- **Real Postgres** — not a clone, not a fork. Same SQL students will use in industry.
- **Web SQL editor and table browser** — log in, see your data, run queries from the browser.
- **CSV import via the dashboard** — no Python required to seed data.
- **Compatible with LangGraph's `PostgresSaver`** — one database can hold both business data and agent checkpoint state, in separate schemas.

You will **not pay anything** for the workload in this guide.

---

## 2. Prerequisites

- A Google or GitHub account (used for Neon sign-up)
- A web browser
- Optional but recommended: Python 3.10+ if you plan to connect from code later

That's it. No local Postgres install. No Docker.

---

## 3. Sign Up and Create Your Project

### 3.1 Create your account

1. Open [https://neon.tech](https://neon.tech) in your browser.
2. Click **Sign Up** in the top right.
3. Choose **Continue with Google** or **Continue with GitHub** — fastest path.
4. Authorize Neon to read your basic profile.
5. You'll land on the Neon dashboard.

### 3.2 Create a project

1. Click **Create project** (or **New Project** if you already have one).
2. Fill in the project details:

   | Field | Value |
   |---|---|
   | Project name | `aibees-academy` |
   | Postgres version | Leave default (latest stable, currently 16) |
   | Cloud provider | AWS (default is fine) |
   | Region | **AWS Asia Pacific (Mumbai)** — closest to Hyderabad. Pick the region nearest you to minimize query latency. |
   | Database name | `neondb` (default) |

3. Click **Create project**.
4. Wait approximately 30–60 seconds for provisioning.

When done, you'll be on the project's main dashboard with a connection string visible.

---

## 4. Retrieve and Save Your Connection String

The connection string is the single piece of information your application needs to talk to the database. Treat it like a password — never commit it to Git.

### 4.1 Find the connection string

On your project dashboard, locate the **Connection string** card. It will look like:

```
postgresql://aibees_user:AbCdEf12345@ep-cool-mountain-12345.ap-south-1.aws.neon.tech/neondb?sslmode=require
```

Click **Show password** to reveal the full string, then click **Copy**.

### 4.2 Save it to a `.env` file

In your project folder, create a file named `.env` (note the leading dot) with this content:

```bash
# .env  — do not commit this file
NEON_DB_URL=postgresql://aibees_user:AbCdEf12345@ep-cool-mountain-12345.ap-south-1.aws.neon.tech/neondb?sslmode=require
```

Replace the value with your actual connection string.

### 4.3 Add `.env` to `.gitignore`

In the same folder, create or edit `.gitignore`:

```
.env
.env.*
```

This prevents the credential from ever being pushed to GitHub.

### 4.4 Anatomy of the connection string

Understanding the parts helps when you debug or rotate credentials:

```
postgresql://aibees_user:AbCdEf12345@ep-cool-mountain-12345.ap-south-1.aws.neon.tech/neondb?sslmode=require
└─protocol─┘ └──user──┘ └─password─┘ └────────────host────────────────────────┘ └──db──┘ └────params────┘
```

- **Protocol**: always `postgresql://` for Postgres
- **User / password**: Neon-generated; rotate from the dashboard if leaked
- **Host**: ends in `.neon.tech` and includes your region
- **Database**: defaults to `neondb`
- **Params**: `sslmode=require` is mandatory — Neon refuses unencrypted connections

---

## 5. Create the Two Schemas

We use two schemas inside one database. This is the standard production pattern: business data and agent state cleanly separated, but managed as one operational unit.

### 5.1 Open the SQL Editor

1. In the Neon dashboard left navigation, click **SQL Editor**.
2. You'll see an editor pane at the top and a results pane below.

### 5.2 Run the schema creation SQL

Paste this into the SQL Editor and click **Run**:

```sql
-- Two logical schemas inside one database
CREATE SCHEMA IF NOT EXISTS business_data;
CREATE SCHEMA IF NOT EXISTS agent_state;

-- Make business_data the default search path so unqualified table names
-- resolve there. The agent_state schema will be used explicitly by
-- LangGraph's PostgresSaver later.
ALTER DATABASE neondb SET search_path TO business_data, public;
```

Expected output: `Success. No rows returned.`

> **What this does:** Creates two namespaces. From now on, when you write `SELECT * FROM products`, Postgres looks in `business_data` automatically. LangGraph's checkpoint tables will live in `agent_state` and are queried with their schema explicitly named — no collisions.

---

## 6. Create the Business Tables

### 6.1 Run the schema SQL

Open the file `sql/01_create_tables.sql` from your repo and copy its contents.

Paste it into the Neon SQL Editor and click **Run**.

Expected output: `Success. No rows returned.`

### 6.2 Verify the tables were created

Click **Tables** in the left navigation. You should see this tree under `business_data`:

```
business_data
├── audit_log
├── budget_codes
├── business_rules
├── inventory
├── products
├── purchase_orders
├── tax_rules
└── vendors
```

If any are missing, re-run `01_create_tables.sql`.

---

## 7. Insert the Seed Data

The seed data is split across three SQL files for clarity:

| File | Inserts into | Rows |
|---|---|---|
| `sql/02_seed_master_data.sql` | vendors, products, inventory, budget_codes, tax_rules, business_rules | 56 |
| `sql/03_seed_purchase_orders.sql` | purchase_orders | 6 |
| `sql/04_seed_audit_log.sql` | audit_log | 24 |

### 7.1 Run them in order

For each file in order:

1. Open the file in a text editor
2. Copy all the contents
3. Paste into the Neon SQL Editor
4. Click **Run**
5. Confirm "Success" message

Run them in this exact order — later files reference data inserted by earlier ones.

### 7.2 Why the order matters

- `02` populates products and budget codes that `03` references via foreign keys.
- `03` creates purchase orders that `04` references.
- Running them out of order produces foreign-key errors.

If you ever want to reset and start over:

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

This clears all rows and resets auto-increment counters. Then re-run the three seed files.

---

## 8. Verify Everything Works

### 8.1 Quick row count check

Paste into the SQL Editor:

```sql
SET search_path TO business_data;

SELECT 'vendors'           AS table_name, COUNT(*) AS rows FROM vendors
UNION ALL SELECT 'products',          COUNT(*) FROM products
UNION ALL SELECT 'inventory',         COUNT(*) FROM inventory
UNION ALL SELECT 'budget_codes',      COUNT(*) FROM budget_codes
UNION ALL SELECT 'tax_rules',         COUNT(*) FROM tax_rules
UNION ALL SELECT 'business_rules',    COUNT(*) FROM business_rules
UNION ALL SELECT 'purchase_orders',   COUNT(*) FROM purchase_orders
UNION ALL SELECT 'audit_log',         COUNT(*) FROM audit_log;
```

Expected output:

| table_name | rows |
|---|---|
| vendors | 6 |
| products | 15 |
| inventory | 15 |
| budget_codes | 4 |
| tax_rules | 11 |
| business_rules | 3 |
| purchase_orders | 6 |
| audit_log | 24 |

### 8.2 Joined dashboard query

This is the kind of query your Auditor agent will run against multiple tables at once. If it works, your relationships are wired correctly.

```sql
SET search_path TO business_data;

SELECT
    po.po_number,
    po.requester,
    po.status,
    po.total_amount,
    bc.department,
    COUNT(al.id) AS audit_findings
FROM purchase_orders po
LEFT JOIN budget_codes bc ON po.budget_code = bc.code
LEFT JOIN audit_log    al ON po.po_number = al.po_number
GROUP BY po.po_number, po.requester, po.status, po.total_amount, bc.department
ORDER BY po.created_at DESC;
```

You should see 6 rows, one per PO, with finding counts ranging from 0 to 6.

### 8.3 Self-correction story query

This is the killer demo query — it shows what your agent will produce live.

```sql
SET search_path TO business_data;

SELECT check_name, status, finding, suggested_fix, created_at
FROM audit_log
WHERE po_number = 'PO-2026-005'
ORDER BY created_at;
```

Trace through the rows: a price check fails with a structured patch, the self-correction step applies the patch, the re-validation passes. This is the audit trail an agentic system produces during a successful self-correction loop.

---

## 9. Connecting from Python

### 9.1 Install the driver

```bash
pip install psycopg2-binary python-dotenv
```

For SQLAlchemy users (recommended for the agent code):

```bash
pip install sqlalchemy psycopg2-binary python-dotenv
```

### 9.2 Minimum working example

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("NEON_DB_URL"))
cursor = conn.cursor(cursor_factory=RealDictCursor)

cursor.execute("""
    SELECT p.sku, p.name, p.unit_price, i.units_in_stock
    FROM business_data.products p
    LEFT JOIN business_data.inventory i ON p.sku = i.sku
    WHERE p.sku = %s
""", ("DELL-LAT-5450",))

print(cursor.fetchone())

conn.close()
```

Expected output:

```python
{'sku': 'DELL-LAT-5450', 'name': 'Dell Latitude 5450', 'unit_price': Decimal('62000.00'), 'units_in_stock': 30}
```

### 9.3 Notes on the Python integration

- Use `%s` as the placeholder, not `?` — Postgres convention.
- Always close connections, or use a `with` block: `with psycopg2.connect(...) as conn:`.
- For production, use a connection pool (`psycopg2.pool.SimpleConnectionPool` or SQLAlchemy's `create_engine` with `pool_size`).
- `RealDictCursor` returns dicts instead of tuples — easier to work with in agent code.

---

## 10. Useful Day-to-Day Queries

These are queries you and your students will run constantly. Save them.

### 10.1 Show all products with current stock and vendor

```sql
SET search_path TO business_data;

SELECT
    p.sku,
    p.name,
    p.category,
    p.unit_price,
    v.name           AS vendor,
    i.units_in_stock,
    i.warehouse
FROM products p
LEFT JOIN vendors   v ON p.approved_vendor_id = v.id
LEFT JOIN inventory i ON p.sku = i.sku
ORDER BY p.category, p.name;
```

### 10.2 Find products that are low on stock

```sql
SELECT p.name, i.units_in_stock, i.reorder_threshold, i.warehouse
FROM products p
JOIN inventory i ON p.sku = i.sku
WHERE i.units_in_stock < i.reorder_threshold
ORDER BY i.units_in_stock ASC;
```

### 10.3 Budget utilization by department

```sql
SELECT
    department,
    code,
    approved_amount,
    spent_amount,
    approved_amount - spent_amount AS available,
    ROUND(100.0 * spent_amount / approved_amount, 1) AS percent_used
FROM budget_codes
ORDER BY percent_used DESC;
```

### 10.4 All findings from a specific PO

```sql
SELECT
    check_name,
    status,
    finding,
    suggested_fix
FROM audit_log
WHERE po_number = 'PO-2026-004'
ORDER BY created_at;
```

### 10.5 Vendor performance — count of POs per vendor

```sql
SELECT
    v.name AS vendor,
    COUNT(DISTINCT po.po_number) AS total_pos,
    SUM(po.total_amount)         AS total_value
FROM vendors v
JOIN products p ON p.approved_vendor_id = v.id
JOIN purchase_orders po
  ON (po.payload -> 'line_items') @> jsonb_build_array(jsonb_build_object('sku', p.sku))
GROUP BY v.name
ORDER BY total_value DESC NULLS LAST;
```

This one uses Postgres JSONB operators to look inside the PO payload — a real-world technique.

---

## 11. Troubleshooting

### "FATAL: password authentication failed"

Your connection string is wrong or the password rotated. Go to Neon dashboard → **Project Settings → Connection Details** → click **Reset password**. Update your `.env`.

### "no pg_hba.conf entry for host"

You're missing `?sslmode=require` at the end of your connection string. Add it.

### Tables not found in queries

You haven't set the search path. Either:
- Add `SET search_path TO business_data;` before queries, **or**
- Qualify table names: `SELECT * FROM business_data.products`

### Foreign key violation when inserting

You're inserting into a child table before the parent has data. Run seed files in order: `02 → 03 → 04`.

### Free tier limits

Neon's free tier auto-pauses idle databases after 5 minutes of no activity. The first query after a pause takes 1–2 seconds to wake up. Subsequent queries are instant. This is normal and not a bug.

### Want to reset everything

```sql
DROP SCHEMA business_data CASCADE;
DROP SCHEMA agent_state   CASCADE;
```

Then re-run section 5 onward.

---

## 12. Folder Structure for Your Repo

When you commit this to your project repo, organize it like this:

```
your-project/
├── .env                          ← never commit
├── .gitignore                    ← contains .env
├── docs/
│   └── NEON_SETUP_GUIDE.md       ← this file
└── sql/
    ├── 01_create_tables.sql
    ├── 02_seed_master_data.sql
    ├── 03_seed_purchase_orders.sql
    └── 04_seed_audit_log.sql
```

Anyone cloning your repo can:

1. Read `docs/NEON_SETUP_GUIDE.md`
2. Sign up for Neon (steps 3–4)
3. Run the four SQL files in order (steps 5–7)
4. Be ready to run the Python agent code in under 20 minutes

That is the operational baseline before any agent code is written.

---

## What's Next

Once your database is verified and seeded, you're ready to wire it into the LangGraph agent. The next step is creating:

- `core/db.py` — SQLAlchemy engine pointing at `business_data`
- `core/checkpointer.py` — LangGraph `PostgresSaver` pointing at `agent_state`
- `agents/composer/` and `agents/auditor/` — the two parent agents
- `graph/builder.py` — the wired graph with self-correction loop

Reach out when your database checks pass on section 8 and we'll move on.
