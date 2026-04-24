-- ============================================================
--  IRROPS Platform — Flight Stream Data Seed
--  Run with: bq --project_id=YOUR_PROJECT query --use_legacy_sql=false < scripts/seed-flight-data.sql
-- ============================================================

-- Normal operations (no anomaly expected)
INSERT INTO irrops_audit.flight_streams VALUES
  ('AA-301', 'JFK→LAX',  0,   'OK', 'CLEAR', CURRENT_TIMESTAMP()),
  ('DL-101', 'ATL→JFK',  0,   'OK', 'CLEAR', CURRENT_TIMESTAMP()),
  ('UA-202', 'ORD→DEN',  0,   'OK', 'CLEAR', CURRENT_TIMESTAMP()),
  ('SW-303', 'DAL→PHX',  0,   'OK', 'CLEAR', CURRENT_TIMESTAMP()),
  ('EK-803', 'DXB→JFK',  0,   'OK', 'CLEAR', CURRENT_TIMESTAMP());

-- Delays (Medium/High severity)
INSERT INTO irrops_audit.flight_streams VALUES
  ('UA-445', 'ORD→MIA',  165, 'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('LH-454', 'FRA→ORD',  180, 'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('BA-178', 'LHR→JFK',   45, 'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('AF-612', 'CDG→JFK',  130, 'OK',      'CLEAR', CURRENT_TIMESTAMP()),
  ('AA-789', 'DFW→LAX',  150, 'OK',      'CLEAR', CURRENT_TIMESTAMP());

-- Crew sick (High severity)
INSERT INTO irrops_audit.flight_streams VALUES
  ('UA-445', 'ORD→MIA',    0, 'SICK',    'CLEAR', CURRENT_TIMESTAMP()),
  ('SW-667', 'PHX→DEN',    0, 'SICK',    'CLEAR', CURRENT_TIMESTAMP()),
  ('AA-221', 'JFK→MIA',   30, 'SICK',    'CLEAR', CURRENT_TIMESTAMP()),
  ('LH-881', 'MUC→JFK',    0, 'SICK',    'CLEAR', CURRENT_TIMESTAMP());

-- Crew no-show (Critical severity)
INSERT INTO irrops_audit.flight_streams VALUES
  ('SW-1201','ATL→BOS',    0, 'NO_SHOW', 'CLEAR', CURRENT_TIMESTAMP()),
  ('AA-334', 'DFW→ORD',    0, 'NO_SHOW', 'CLEAR', CURRENT_TIMESTAMP()),
  ('B6-412', 'BOS→LAX',    0, 'NO_SHOW', 'CLEAR', CURRENT_TIMESTAMP());

-- Weather storm (High severity)
INSERT INTO irrops_audit.flight_streams VALUES
  ('DL-892', 'DFW→SEA',    0, 'OK',      'STORM', CURRENT_TIMESTAMP()),
  ('AA-113', 'ORD→BOS',    0, 'OK',      'STORM', CURRENT_TIMESTAMP()),
  ('UA-667', 'EWR→MIA',    0, 'OK',      'STORM', CURRENT_TIMESTAMP());

-- Weather fog (Medium severity)
INSERT INTO irrops_audit.flight_streams VALUES
  ('LH-454', 'FRA→ORD',   90, 'OK',      'FOG',   CURRENT_TIMESTAMP()),
  ('EK-201', 'DXB→LHR',    0, 'OK',      'FOG',   CURRENT_TIMESTAMP()),
  ('KL-661', 'AMS→JFK',    0, 'OK',      'FOG',   CURRENT_TIMESTAMP());

-- Combined worst-case IRROPS
INSERT INTO irrops_audit.flight_streams VALUES
  ('AA-999', 'ORD→JFK',  180, 'SICK',    'STORM', CURRENT_TIMESTAMP()),
  ('DL-777', 'ATL→LAX',  200, 'NO_SHOW', 'STORM', CURRENT_TIMESTAMP()),
  ('UA-555', 'DEN→ORD',  120, 'SICK',    'FOG',   CURRENT_TIMESTAMP());
