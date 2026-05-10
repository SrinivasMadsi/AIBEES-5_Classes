-- =============================================================================
-- 01_create_tables.sql
-- Creates all 8 business-data tables for the Purchase Order Agent
-- Run this AFTER creating schemas (see NEON_SETUP_GUIDE.md section 5)
-- =============================================================================

SET search_path TO business_data;

-- Drop existing tables in reverse dependency order (safe to re-run)
DROP TABLE IF EXISTS audit_log         CASCADE;
DROP TABLE IF EXISTS purchase_orders   CASCADE;
DROP TABLE IF EXISTS business_rules    CASCADE;
DROP TABLE IF EXISTS tax_rules         CASCADE;
DROP TABLE IF EXISTS budget_codes      CASCADE;
DROP TABLE IF EXISTS inventory         CASCADE;
DROP TABLE IF EXISTS products          CASCADE;
DROP TABLE IF EXISTS vendors           CASCADE;


-- -----------------------------------------------------------------------------
-- VENDORS — vendor master data
-- -----------------------------------------------------------------------------
CREATE TABLE vendors (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    approved_categories TEXT NOT NULL,
    payment_terms_days  INT  DEFAULT 30,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  vendors IS 'Approved vendor master. The Auditor verifies vendor selections against this table.';
COMMENT ON COLUMN vendors.approved_categories IS 'Comma-separated list of product categories this vendor is approved to supply.';


-- -----------------------------------------------------------------------------
-- PRODUCTS — product catalog with current pricing
-- -----------------------------------------------------------------------------
CREATE TABLE products (
    sku                 TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    category            TEXT NOT NULL,
    unit_price          NUMERIC(12, 2) NOT NULL,
    currency            TEXT DEFAULT 'INR',
    approved_vendor_id  INT REFERENCES vendors(id),
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  products IS 'Product catalog. Source of truth for prices the Auditor checks against.';
COMMENT ON COLUMN products.unit_price IS 'Current catalog price. May change; the Auditor catches stale prices in POs.';

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_vendor   ON products(approved_vendor_id);


-- -----------------------------------------------------------------------------
-- INVENTORY — current stock per SKU per warehouse
-- -----------------------------------------------------------------------------
CREATE TABLE inventory (
    sku                 TEXT PRIMARY KEY REFERENCES products(sku),
    warehouse           TEXT NOT NULL,
    units_in_stock      INT NOT NULL CHECK (units_in_stock >= 0),
    reorder_threshold   INT DEFAULT 10,
    last_updated        TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE inventory IS 'Real-time inventory levels. The Auditor checks PO quantities against availability here.';

CREATE INDEX idx_inventory_warehouse ON inventory(warehouse);


-- -----------------------------------------------------------------------------
-- BUDGET_CODES — approved budgets per department/quarter
-- -----------------------------------------------------------------------------
CREATE TABLE budget_codes (
    code                TEXT PRIMARY KEY,
    department          TEXT,
    approved_amount     NUMERIC(14, 2) NOT NULL,
    spent_amount        NUMERIC(14, 2) DEFAULT 0,
    fiscal_quarter      TEXT,
    is_active           BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE budget_codes IS 'Approved budget allocations. The Auditor checks PO totals against remaining budget.';


-- -----------------------------------------------------------------------------
-- TAX_RULES — region-aware GST rates by category
-- -----------------------------------------------------------------------------
CREATE TABLE tax_rules (
    id                  SERIAL PRIMARY KEY,
    region              TEXT NOT NULL,
    category            TEXT NOT NULL,
    gst_rate            NUMERIC(5, 2) NOT NULL,
    UNIQUE (region, category)
);

COMMENT ON TABLE tax_rules IS 'Indian GST rates per state and category. Used by the Composer to calculate tax.';


-- -----------------------------------------------------------------------------
-- BUSINESS_RULES — configurable approval thresholds and limits
-- -----------------------------------------------------------------------------
CREATE TABLE business_rules (
    id                  SERIAL PRIMARY KEY,
    rule_name           TEXT NOT NULL UNIQUE,
    rule_type           TEXT NOT NULL,
    rule_value          JSONB NOT NULL,
    description         TEXT
);

COMMENT ON TABLE  business_rules IS 'Soft-coded business rules. Edit values without changing agent code.';
COMMENT ON COLUMN business_rules.rule_value IS 'Rule payload as JSONB; structure depends on rule_type.';


-- -----------------------------------------------------------------------------
-- PURCHASE_ORDERS — output table; one row per PO
-- -----------------------------------------------------------------------------
CREATE TABLE purchase_orders (
    po_number           TEXT PRIMARY KEY,
    requester           TEXT,
    status              TEXT DEFAULT 'draft',
    total_amount        NUMERIC(14, 2),
    budget_code         TEXT REFERENCES budget_codes(code),
    payload             JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  purchase_orders IS 'Generated POs. Status: draft, validated, submitted, rejected.';
COMMENT ON COLUMN purchase_orders.payload IS 'Full PO body as JSONB — line items, addresses, totals, currency.';

CREATE INDEX idx_po_status      ON purchase_orders(status);
CREATE INDEX idx_po_budget      ON purchase_orders(budget_code);
CREATE INDEX idx_po_created_at  ON purchase_orders(created_at DESC);


-- -----------------------------------------------------------------------------
-- AUDIT_LOG — every Auditor finding for every PO
-- -----------------------------------------------------------------------------
CREATE TABLE audit_log (
    id                  SERIAL PRIMARY KEY,
    po_number           TEXT REFERENCES purchase_orders(po_number),
    check_name          TEXT,
    status              TEXT,
    finding             TEXT,
    suggested_fix       JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  audit_log IS 'Every Auditor finding. Pairs with Langfuse traces for full observability.';
COMMENT ON COLUMN audit_log.suggested_fix IS 'Structured patch the self-correction node can apply.';

CREATE INDEX idx_audit_po       ON audit_log(po_number);
CREATE INDEX idx_audit_status   ON audit_log(status);


-- -----------------------------------------------------------------------------
-- Verify: list all tables created in business_data schema
-- -----------------------------------------------------------------------------
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'business_data'
ORDER BY table_name;
