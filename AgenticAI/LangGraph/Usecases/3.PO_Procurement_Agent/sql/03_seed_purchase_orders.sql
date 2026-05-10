-- =============================================================================
-- 03_seed_purchase_orders.sql
-- Seeds 6 purchase orders covering every realistic state:
--   - submitted (success)
--   - validated (awaiting submission)
--   - draft (audit pending)
--   - rejected (failed audit)
--   - submitted (after self-correction)
--   - validated (with warnings)
-- Run this AFTER 02_seed_master_data.sql.
-- =============================================================================

SET search_path TO business_data;


-- -----------------------------------------------------------------------------
-- PO 1 — Successfully submitted to ERP
-- -----------------------------------------------------------------------------
INSERT INTO purchase_orders (po_number, requester, status, total_amount, budget_code, payload, created_at) VALUES
('PO-2026-001',
 'priya.sharma@aibees.com',
 'submitted',
 1180000.00,
 'PO-2026-Q2-0847',
 '{
   "po_number": "PO-2026-001",
   "requester": "priya.sharma@aibees.com",
   "delivery_address": "AIBees HQ, HITEC City, Hyderabad, Telangana",
   "delivery_date": "2026-04-25",
   "line_items": [
     {"sku": "DELL-LAT-5450", "name": "Dell Latitude 5450",       "quantity": 15, "unit_price": 62000.00, "line_total": 930000.00},
     {"sku": "LOG-MX-MASTER", "name": "Logitech MX Master 3S",    "quantity": 15, "unit_price":  8500.00, "line_total": 127500.00},
     {"sku": "LOG-K380",      "name": "Logitech K380 Keyboard",   "quantity": 15, "unit_price":  3200.00, "line_total":  48000.00}
   ],
   "subtotal": 1105500.00,
   "gst_amount": 199990.00,
   "total_amount": 1180000.00,
   "currency": "INR"
 }'::jsonb,
 NOW() - INTERVAL '12 days');


-- -----------------------------------------------------------------------------
-- PO 2 — Validated, awaiting ERP submission
-- -----------------------------------------------------------------------------
INSERT INTO purchase_orders (po_number, requester, status, total_amount, budget_code, payload, created_at) VALUES
('PO-2026-002',
 'rajesh.kumar@aibees.com',
 'validated',
 692100.00,
 'PO-2026-Q2-0912',
 '{
   "po_number": "PO-2026-002",
   "requester": "rajesh.kumar@aibees.com",
   "delivery_address": "AIBees Engineering, Whitefield, Bangalore, Karnataka",
   "delivery_date": "2026-05-15",
   "line_items": [
     {"sku": "HP-ELITE-840", "name": "HP EliteBook 840 G10",      "quantity":  8, "unit_price": 78000.00, "line_total": 624000.00},
     {"sku": "DELL-MON-27",  "name": "Dell 27-inch UltraSharp",   "quantity":  4, "unit_price": 18500.00, "line_total":  74000.00}
   ],
   "subtotal": 698000.00,
   "gst_amount": 125640.00,
   "total_amount": 692100.00,
   "currency": "INR"
 }'::jsonb,
 NOW() - INTERVAL '3 days');


-- -----------------------------------------------------------------------------
-- PO 3 — Draft, awaiting audit
-- -----------------------------------------------------------------------------
INSERT INTO purchase_orders (po_number, requester, status, total_amount, budget_code, payload, created_at) VALUES
('PO-2026-003',
 'ananya.reddy@aibees.com',
 'draft',
 354000.00,
 'PO-2026-Q2-0445',
 '{
   "po_number": "PO-2026-003",
   "requester": "ananya.reddy@aibees.com",
   "delivery_address": "AIBees Sales, MG Road, Bangalore, Karnataka",
   "delivery_date": "2026-05-20",
   "line_items": [
     {"sku": "LEN-T14-G4",  "name": "Lenovo ThinkPad T14 Gen 4",  "quantity":  3, "unit_price": 89000.00, "line_total": 267000.00},
     {"sku": "LOG-MX-KEYS", "name": "Logitech MX Keys",           "quantity":  3, "unit_price":  9800.00, "line_total":  29400.00},
     {"sku": "LOG-C920",    "name": "Logitech C920 Webcam",       "quantity":  3, "unit_price":  6500.00, "line_total":  19500.00}
   ],
   "subtotal": 315900.00,
   "gst_amount": 56862.00,
   "total_amount": 354000.00,
   "currency": "INR"
 }'::jsonb,
 NOW() - INTERVAL '4 hours');


-- -----------------------------------------------------------------------------
-- PO 4 — REJECTED: insufficient inventory + over budget
-- -----------------------------------------------------------------------------
INSERT INTO purchase_orders (po_number, requester, status, total_amount, budget_code, payload, created_at) VALUES
('PO-2026-004',
 'vikram.singh@aibees.com',
 'rejected',
 6200000.00,
 'PO-2026-Q2-0623',
 '{
   "po_number": "PO-2026-004",
   "requester": "vikram.singh@aibees.com",
   "delivery_address": "AIBees Operations, Cyber Towers, Hyderabad",
   "delivery_date": "2026-05-10",
   "line_items": [
     {"sku": "DELL-LAT-5450", "name": "Dell Latitude 5450", "quantity": 100, "unit_price": 62000.00, "line_total": 6200000.00}
   ],
   "subtotal": 6200000.00,
   "gst_amount": 1116000.00,
   "total_amount": 6200000.00,
   "currency": "INR",
   "rejection_reason": "Insufficient inventory and exceeds budget allocation"
 }'::jsonb,
 NOW() - INTERVAL '6 days');


-- -----------------------------------------------------------------------------
-- PO 5 — SELF-CORRECTED then submitted (key teaching example)
-- -----------------------------------------------------------------------------
INSERT INTO purchase_orders (po_number, requester, status, total_amount, budget_code, payload, created_at) VALUES
('PO-2026-005',
 'priya.sharma@aibees.com',
 'submitted',
 826960.00,
 'PO-2026-Q2-0847',
 '{
   "po_number": "PO-2026-005",
   "requester": "priya.sharma@aibees.com",
   "delivery_address": "AIBees HQ, HITEC City, Hyderabad, Telangana",
   "delivery_date": "2026-05-08",
   "line_items": [
     {"sku": "DELL-MON-32",  "name": "Dell 32-inch 4K Monitor", "quantity": 10, "unit_price": 34000.00, "line_total": 340000.00},
     {"sku": "DELL-LAT-7440","name": "Dell Latitude 7440",      "quantity":  4, "unit_price": 94000.00, "line_total": 376000.00}
   ],
   "subtotal": 716000.00,
   "gst_amount": 128880.00,
   "total_amount": 826960.00,
   "currency": "INR",
   "self_correction_count": 1,
   "self_correction_notes": "Initial price for DELL-MON-32 was outdated; auto-corrected from 32000 to 34000"
 }'::jsonb,
 NOW() - INTERVAL '1 day');


-- -----------------------------------------------------------------------------
-- PO 6 — Validated with a low-stock warning
-- -----------------------------------------------------------------------------
INSERT INTO purchase_orders (po_number, requester, status, total_amount, budget_code, payload, created_at) VALUES
('PO-2026-006',
 'meera.iyer@aibees.com',
 'validated',
 1640220.00,
 'PO-2026-Q2-0912',
 '{
   "po_number": "PO-2026-006",
   "requester": "meera.iyer@aibees.com",
   "delivery_address": "AIBees Engineering, Whitefield, Bangalore",
   "delivery_date": "2026-05-30",
   "line_items": [
     {"sku": "HP-ELITE-1040", "name": "HP EliteBook 1040 G10",     "quantity": 10, "unit_price": 115000.00, "line_total": 1150000.00},
     {"sku": "SAM-MON-32",    "name": "Samsung 32-inch ViewFinity","quantity": 10, "unit_price":  29500.00, "line_total":  295000.00},
     {"sku": "HP-LJ-M404",    "name": "HP LaserJet Pro M404",      "quantity":  2, "unit_price":  24500.00, "line_total":   49000.00}
   ],
   "subtotal": 1494000.00,
   "gst_amount": 268920.00,
   "total_amount": 1640220.00,
   "currency": "INR"
 }'::jsonb,
 NOW() - INTERVAL '2 days');


-- -----------------------------------------------------------------------------
-- Verify
-- -----------------------------------------------------------------------------
SELECT po_number, requester, status, total_amount, budget_code
FROM purchase_orders
ORDER BY created_at DESC;
