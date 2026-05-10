-- =============================================================================
-- 02_seed_master_data.sql
-- Seeds master/reference data: vendors, products, inventory, budgets,
-- tax rules, business rules.
-- Run this AFTER 01_create_tables.sql.
-- =============================================================================

SET search_path TO business_data;


-- -----------------------------------------------------------------------------
-- VENDORS (6 rows)
-- -----------------------------------------------------------------------------
INSERT INTO vendors (name, approved_categories, payment_terms_days) VALUES
('Dell India Pvt Ltd',     'laptops,monitors,desktops',         45),
('Logitech Distributors',  'peripherals,accessories',           30),
('HP Enterprise India',    'laptops,printers',                  45),
('Compu-Mart Wholesale',   'peripherals,accessories,laptops',   30),
('Lenovo India',           'laptops,desktops,monitors',         60),
('Samsung B2B',            'monitors,phones,tablets',           30);


-- -----------------------------------------------------------------------------
-- PRODUCTS (15 rows)
-- -----------------------------------------------------------------------------
INSERT INTO products (sku, name, category, unit_price, approved_vendor_id) VALUES
('DELL-LAT-5450',  'Dell Latitude 5450',          'laptops',     62000.00,  1),
('DELL-LAT-7440',  'Dell Latitude 7440',          'laptops',     94000.00,  1),
('DELL-MON-27',    'Dell 27-inch UltraSharp',     'monitors',    18500.00,  1),
('DELL-MON-32',    'Dell 32-inch 4K Monitor',     'monitors',    34000.00,  1),
('DELL-OPT-7010',  'Dell OptiPlex 7010',          'desktops',    52000.00,  1),
('LOG-MX-MASTER',  'Logitech MX Master 3S',       'peripherals',  8500.00,  2),
('LOG-K380',       'Logitech K380 Keyboard',      'peripherals',  3200.00,  2),
('LOG-MX-KEYS',    'Logitech MX Keys',            'peripherals',  9800.00,  2),
('LOG-C920',       'Logitech C920 Webcam',        'accessories',  6500.00,  2),
('HP-ELITE-840',   'HP EliteBook 840 G10',        'laptops',     78000.00,  3),
('HP-ELITE-1040',  'HP EliteBook 1040 G10',       'laptops',    115000.00,  3),
('HP-LJ-M404',     'HP LaserJet Pro M404',        'printers',    24500.00,  3),
('LEN-X1-CARBON',  'Lenovo ThinkPad X1 Carbon',   'laptops',    142000.00,  5),
('LEN-T14-G4',     'Lenovo ThinkPad T14 Gen 4',   'laptops',     89000.00,  5),
('SAM-MON-32',     'Samsung 32-inch ViewFinity',  'monitors',    29500.00,  6);


-- -----------------------------------------------------------------------------
-- INVENTORY (15 rows — one per SKU)
-- -----------------------------------------------------------------------------
INSERT INTO inventory (sku, warehouse, units_in_stock, reorder_threshold) VALUES
('DELL-LAT-5450',  'Hyderabad-WH1',  30,  20),
('DELL-LAT-7440',  'Hyderabad-WH1',  18,  10),
('DELL-MON-27',    'Hyderabad-WH1',  45,  20),
('DELL-MON-32',    'Hyderabad-WH1',  12,  10),
('DELL-OPT-7010',  'Hyderabad-WH1',   8,  10),
('LOG-MX-MASTER',  'Hyderabad-WH1', 200,  50),
('LOG-K380',       'Hyderabad-WH1', 150,  50),
('LOG-MX-KEYS',    'Hyderabad-WH1',  80,  30),
('LOG-C920',       'Hyderabad-WH1',  60,  20),
('HP-ELITE-840',   'Bangalore-WH2',  12,  15),
('HP-ELITE-1040',  'Bangalore-WH2',   6,  10),
('HP-LJ-M404',     'Bangalore-WH2',  22,  10),
('LEN-X1-CARBON',  'Mumbai-WH3',      9,  10),
('LEN-T14-G4',     'Mumbai-WH3',     25,  15),
('SAM-MON-32',     'Hyderabad-WH1',  35,  15);


-- -----------------------------------------------------------------------------
-- BUDGET_CODES (4 rows)
-- -----------------------------------------------------------------------------
INSERT INTO budget_codes (code, department, approved_amount, spent_amount, fiscal_quarter) VALUES
('PO-2026-Q2-0847',  'IT-Hyderabad',     5000000.00,  1240000.00,  'Q2-2026'),
('PO-2026-Q2-0912',  'Engineering',      8500000.00,  3200000.00,  'Q2-2026'),
('PO-2026-Q2-0445',  'Sales-Bangalore',  2200000.00,   180000.00,  'Q2-2026'),
('PO-2026-Q2-0623',  'Operations',       3500000.00,  1100000.00,  'Q2-2026');


-- -----------------------------------------------------------------------------
-- TAX_RULES (11 rows — Indian GST by region and category)
-- -----------------------------------------------------------------------------
INSERT INTO tax_rules (region, category, gst_rate) VALUES
('Telangana',    'laptops',     18.00),
('Telangana',    'monitors',    18.00),
('Telangana',    'peripherals', 18.00),
('Telangana',    'accessories', 18.00),
('Telangana',    'desktops',    18.00),
('Telangana',    'printers',    18.00),
('Karnataka',    'laptops',     18.00),
('Karnataka',    'monitors',    18.00),
('Karnataka',    'peripherals', 18.00),
('Maharashtra',  'laptops',     18.00),
('Maharashtra',  'monitors',    18.00);


-- -----------------------------------------------------------------------------
-- BUSINESS_RULES (3 rows)
-- -----------------------------------------------------------------------------
INSERT INTO business_rules (rule_name, rule_type, rule_value, description) VALUES
('max_qty_per_line',
 'qty_limit',
 '{"laptops": 100, "monitors": 200, "peripherals": 500}'::jsonb,
 'Maximum units allowed per line item by category.'),

('po_value_approval',
 'value_limit',
 '{"auto_approve_below": 500000, "manager_approval": 2000000, "cfo_approval_above": 2000000}'::jsonb,
 'PO total approval thresholds in INR.'),

('vendor_min_rating',
 'approval',
 '{"min_active_status": true}'::jsonb,
 'Vendor must be active to be selected on a PO.');


-- -----------------------------------------------------------------------------
-- Verify counts
-- -----------------------------------------------------------------------------
SELECT 'vendors'        AS table_name, COUNT(*) AS rows FROM vendors
UNION ALL SELECT 'products',         COUNT(*) FROM products
UNION ALL SELECT 'inventory',        COUNT(*) FROM inventory
UNION ALL SELECT 'budget_codes',     COUNT(*) FROM budget_codes
UNION ALL SELECT 'tax_rules',        COUNT(*) FROM tax_rules
UNION ALL SELECT 'business_rules',   COUNT(*) FROM business_rules;
