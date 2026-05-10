-- =============================================================================
-- 04_seed_audit_log.sql
-- Seeds audit_log with realistic findings for each PO.
-- Includes the full self-correction sequence for PO-2026-005 — the key
-- teaching example showing how the agent catches and fixes its own mistake.
-- Run this AFTER 03_seed_purchase_orders.sql.
-- =============================================================================

SET search_path TO business_data;


-- -----------------------------------------------------------------------------
-- PO-2026-001 — Clean run, all four checks passed
-- -----------------------------------------------------------------------------
INSERT INTO audit_log (po_number, check_name, status, finding, suggested_fix, created_at) VALUES
('PO-2026-001', 'inventory_check', 'pass',
 'All line items have sufficient stock', NULL,
 NOW() - INTERVAL '12 days'),

('PO-2026-001', 'price_check',     'pass',
 'All prices match catalog', NULL,
 NOW() - INTERVAL '12 days'),

('PO-2026-001', 'policy_check',    'pass',
 'Total within budget; vendor approved for all categories', NULL,
 NOW() - INTERVAL '12 days'),

('PO-2026-001', 'schema_check',    'pass',
 'PO payload conforms to ERP schema', NULL,
 NOW() - INTERVAL '12 days');


-- -----------------------------------------------------------------------------
-- PO-2026-002 — Clean run
-- -----------------------------------------------------------------------------
INSERT INTO audit_log (po_number, check_name, status, finding, suggested_fix, created_at) VALUES
('PO-2026-002', 'inventory_check', 'pass',
 'Stock available for all items', NULL,
 NOW() - INTERVAL '3 days'),

('PO-2026-002', 'price_check',     'pass',
 'Prices verified against catalog', NULL,
 NOW() - INTERVAL '3 days'),

('PO-2026-002', 'policy_check',    'pass',
 'Within budget limits', NULL,
 NOW() - INTERVAL '3 days'),

('PO-2026-002', 'schema_check',    'pass',
 'Schema valid', NULL,
 NOW() - INTERVAL '3 days');


-- -----------------------------------------------------------------------------
-- PO-2026-004 — REJECTED with multiple failures
-- -----------------------------------------------------------------------------
INSERT INTO audit_log (po_number, check_name, status, finding, suggested_fix, created_at) VALUES
('PO-2026-004', 'inventory_check', 'fail',
 'Requested 100 units of DELL-LAT-5450 but only 30 in stock at Hyderabad-WH1',
 '{"action": "reduce_quantity", "sku": "DELL-LAT-5450", "max_available": 30}'::jsonb,
 NOW() - INTERVAL '6 days'),

('PO-2026-004', 'price_check',     'pass',
 'Prices match catalog', NULL,
 NOW() - INTERVAL '6 days'),

('PO-2026-004', 'policy_check',    'fail',
 'PO total ₹61,00,000 exceeds remaining budget on PO-2026-Q2-0847 (₹37,60,000 available)',
 '{"action": "split_po", "remaining_budget": 3760000, "po_amount": 6200000}'::jsonb,
 NOW() - INTERVAL '6 days'),

('PO-2026-004', 'policy_check',    'fail',
 'Quantity 100 hits max_qty_per_line for laptops (limit: 100, requested: 100 — manual approval required)',
 '{"action": "manual_approval_required", "category": "laptops", "limit": 100}'::jsonb,
 NOW() - INTERVAL '6 days');


-- -----------------------------------------------------------------------------
-- PO-2026-005 — SELF-CORRECTION SEQUENCE (key teaching example)
-- The order matters: fail → patch → pass on re-validation.
-- -----------------------------------------------------------------------------
INSERT INTO audit_log (po_number, check_name, status, finding, suggested_fix, created_at) VALUES
('PO-2026-005', 'inventory_check', 'pass',
 'All items in stock', NULL,
 NOW() - INTERVAL '1 day'),

('PO-2026-005', 'price_check',     'fail',
 'Catalog price for DELL-MON-32 is ₹34,000 but PO has ₹32,000 (price was updated 14 days ago)',
 '{"action": "update_price", "sku": "DELL-MON-32", "old_price": 32000, "new_price": 34000}'::jsonb,
 NOW() - INTERVAL '1 day' - INTERVAL '15 minutes'),

('PO-2026-005', 'self_correction', 'pass',
 'Patch applied: DELL-MON-32 price updated to ₹34,000; PO total recomputed',
 '{"applied_fixes": ["update_price:DELL-MON-32"], "iteration": 1}'::jsonb,
 NOW() - INTERVAL '1 day' - INTERVAL '12 minutes'),

('PO-2026-005', 'price_check',     'pass',
 'Re-validation: prices match catalog after correction', NULL,
 NOW() - INTERVAL '1 day' - INTERVAL '10 minutes'),

('PO-2026-005', 'policy_check',    'pass',
 'Within budget after correction', NULL,
 NOW() - INTERVAL '1 day' - INTERVAL '10 minutes'),

('PO-2026-005', 'schema_check',    'pass',
 'Schema valid', NULL,
 NOW() - INTERVAL '1 day' - INTERVAL '9 minutes');


-- -----------------------------------------------------------------------------
-- PO-2026-006 — Validated with a low-stock warning
-- -----------------------------------------------------------------------------
INSERT INTO audit_log (po_number, check_name, status, finding, suggested_fix, created_at) VALUES
('PO-2026-006', 'inventory_check', 'warning',
 'HP-ELITE-1040 stock is 6 units; requested 10. Backorder window: 5 days',
 '{"action": "accept_with_partial_delivery", "available_now": 6, "backorder": 4}'::jsonb,
 NOW() - INTERVAL '2 days'),

('PO-2026-006', 'price_check',     'pass',
 'Prices match catalog', NULL,
 NOW() - INTERVAL '2 days'),

('PO-2026-006', 'policy_check',    'pass',
 'Within Engineering budget allocation', NULL,
 NOW() - INTERVAL '2 days'),

('PO-2026-006', 'schema_check',    'pass',
 'Schema valid', NULL,
 NOW() - INTERVAL '2 days');


-- -----------------------------------------------------------------------------
-- Verify — show all findings grouped by PO
-- -----------------------------------------------------------------------------
SELECT
    po_number,
    COUNT(*)                                         AS total_checks,
    SUM((status = 'pass')::int)                      AS passed,
    SUM((status = 'fail')::int)                      AS failed,
    SUM((status = 'warning')::int)                   AS warnings,
    SUM((status = 'self_correction')::int)           AS corrections
FROM audit_log
GROUP BY po_number
ORDER BY po_number;
