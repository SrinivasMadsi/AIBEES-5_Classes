# ============================================================
#  IRROPS Platform — BigQuery Setup (Windows PowerShell)
#  Creates datasets, tables, and seeds flight data
# ============================================================

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  IRROPS Platform — BigQuery Setup                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = gcloud config get-value project
Write-Host "  Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host ""

# ── Create dataset ────────────────────────────────────────────────────────────
Write-Host "📦 Creating dataset irrops_audit..." -ForegroundColor Yellow
bq --project_id=$PROJECT_ID mk --dataset --location=US irrops_audit 2>$null
Write-Host "  ✅ Dataset ready" -ForegroundColor Green

# ── Create audit_log table ────────────────────────────────────────────────────
Write-Host ""
Write-Host "📋 Creating audit_log table..." -ForegroundColor Yellow
bq --project_id=$PROJECT_ID mk --table irrops_audit.audit_log `
    action_id:STRING,event_id:STRING,flight:STRING,agent:STRING,`
    tool_called:STRING,proposed_action:STRING,confidence:FLOAT,`
    status:STRING,approved_by:STRING,rejected_by:STRING,`
    rejection_reason:STRING,regulatory_impact:BOOLEAN,`
    assessed_at:TIMESTAMP,escalated_at:TIMESTAMP,`
    approved_at:TIMESTAMP,rejected_at:TIMESTAMP,notes:STRING 2>$null
Write-Host "  ✅ audit_log table ready" -ForegroundColor Green

# ── Create flight_streams table ───────────────────────────────────────────────
Write-Host ""
Write-Host "✈️  Creating flight_streams table..." -ForegroundColor Yellow
bq --project_id=$PROJECT_ID mk --table irrops_audit.flight_streams `
    flight:STRING,route:STRING,delay_min:INTEGER,`
    crew_status:STRING,weather:STRING,updated_at:TIMESTAMP 2>$null
Write-Host "  ✅ flight_streams table ready" -ForegroundColor Green

# ── Seed flight data ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "🌱 Seeding flight data..." -ForegroundColor Yellow

$insertSQL = @"
INSERT INTO irrops_audit.flight_streams VALUES
  ('AA-301', 'JFK-LAX',  0,   'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('UA-445', 'ORD-MIA',  165, 'SICK',    'CLEAR', CURRENT_TIMESTAMP()),
  ('DL-892', 'DFW-SEA',  0,   'OK',      'STORM', CURRENT_TIMESTAMP()),
  ('SW-1201','ATL-BOS',  0,   'NO_SHOW', 'CLEAR', CURRENT_TIMESTAMP()),
  ('BA-178', 'LHR-JFK',  45,  'OK',      'WIND',  CURRENT_TIMESTAMP()),
  ('LH-454', 'FRA-ORD',  90,  'OK',      'FOG',   CURRENT_TIMESTAMP()),
  ('AA-999', 'ORD-JFK',  180, 'SICK',    'STORM', CURRENT_TIMESTAMP()),
  ('DL-777', 'ATL-LAX',  200, 'NO_SHOW', 'STORM', CURRENT_TIMESTAMP()),
  ('UA-555', 'DEN-ORD',  120, 'SICK',    'FOG',   CURRENT_TIMESTAMP()),
  ('EK-201', 'DXB-LHR',  0,   'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('AF-612', 'CDG-JFK',  130, 'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('SQ-904', 'SIN-LAX',  0,   'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('SW-667', 'PHX-DEN',  0,   'SICK',    'CLEAR', CURRENT_TIMESTAMP()),
  ('B6-412', 'BOS-LAX',  0,   'NO_SHOW', 'CLEAR', CURRENT_TIMESTAMP()),
  ('AS-221', 'SEA-ANC',  30,  'OK',      'WIND',  CURRENT_TIMESTAMP())
"@

bq --project_id=$PROJECT_ID query --use_legacy_sql=false $insertSQL
Write-Host "  ✅ 15 flight records seeded" -ForegroundColor Green

# ── Verify ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "🔍 Verifying tables..." -ForegroundColor Yellow
bq --project_id=$PROJECT_ID ls irrops_audit

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ BigQuery Setup Complete!                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Tables created:" -ForegroundColor White
Write-Host "  → $PROJECT_ID.irrops_audit.audit_log" -ForegroundColor Cyan
Write-Host "  → $PROJECT_ID.irrops_audit.flight_streams (15 records)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Query audit logs:" -ForegroundColor Yellow
Write-Host "  bq query --project_id=$PROJECT_ID --use_legacy_sql=false \" -ForegroundColor White
Write-Host "    'SELECT * FROM irrops_audit.audit_log ORDER BY assessed_at DESC LIMIT 10'" -ForegroundColor White
Write-Host ""
Write-Host "  Update a flight for live demo:" -ForegroundColor Yellow
Write-Host "  bq query --project_id=$PROJECT_ID --use_legacy_sql=false \" -ForegroundColor White
Write-Host "    'UPDATE irrops_audit.flight_streams SET delay_min=210, updated_at=CURRENT_TIMESTAMP() WHERE flight=''AA-301'''" -ForegroundColor White
Write-Host ""
