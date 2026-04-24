#!/bin/bash
# ============================================================
#  IRROPS Platform — GCP Setup Script (Mac/Linux)
#  Run once to configure GCP + Python virtual environment
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  IRROPS Platform — GCP Setup (Mac/Linux)         ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Check prerequisites ───────────────────────────────────────────────────────
echo "📋 Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "  ❌ Python not found. Install from https://python.org/downloads"
    exit 1
fi
echo "  ✅ $(python3 --version)"

if ! command -v node &>/dev/null; then
    echo "  ❌ Node.js not found. Install from https://nodejs.org"
    exit 1
fi
echo "  ✅ Node.js $(node --version)"

if ! command -v gcloud &>/dev/null; then
    echo "  ❌ gcloud not found. Install from https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "  ✅ gcloud CLI found"

# ── Create virtual environment ────────────────────────────────────────────────
echo ""
echo "🐍 Creating Python virtual environment..."

if [ -d ".venv" ]; then
    echo "  ℹ️  .venv already exists — skipping"
else
    python3 -m venv .venv
    echo "  ✅ Virtual environment created"
fi

echo "  Activating .venv..."
source .venv/bin/activate
echo "  ✅ venv activated"

# ── GCP Authentication ────────────────────────────────────────────────────────
echo ""
echo "☁️  Setting up Google Cloud authentication..."
gcloud init

# ── Application Default Credentials ──────────────────────────────────────────
echo ""
echo "🔑 Setting Application Default Credentials..."
gcloud auth application-default login \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --no-launch-browser

# ── Get project ID ────────────────────────────────────────────────────────────
PROJECT_ID=$(gcloud config get-value project)
echo ""
echo "  ✅ Project: $PROJECT_ID"

# ── Enable APIs ───────────────────────────────────────────────────────────────
echo ""
echo "🔌 Enabling GCP APIs..."
for api in aiplatform bigquery pubsub run firestore artifactregistry; do
    echo -n "   Enabling ${api}.googleapis.com..."
    gcloud services enable ${api}.googleapis.com --project=$PROJECT_ID --quiet
    echo " ✅"
done

# ── BigQuery setup ────────────────────────────────────────────────────────────
echo ""
echo "📊 Setting up BigQuery..."
bq --project_id=$PROJECT_ID mk --dataset --location=US irrops_audit 2>/dev/null || true
bq --project_id=$PROJECT_ID mk --table irrops_audit.audit_log \
    action_id:STRING,event_id:STRING,flight:STRING,agent:STRING,\
    tool_called:STRING,proposed_action:STRING,confidence:FLOAT,\
    status:STRING,approved_by:STRING,regulatory_impact:BOOLEAN,\
    assessed_at:TIMESTAMP,escalated_at:TIMESTAMP,notes:STRING 2>/dev/null || true
bq --project_id=$PROJECT_ID mk --table irrops_audit.flight_streams \
    flight:STRING,route:STRING,delay_min:INTEGER,\
    crew_status:STRING,weather:STRING,updated_at:TIMESTAMP 2>/dev/null || true

# Seed flight data
bq --project_id=$PROJECT_ID query --use_legacy_sql=false \
"INSERT INTO irrops_audit.flight_streams VALUES
  ('AA-301','JFK→LAX',0,'OK','CLEAR',CURRENT_TIMESTAMP()),
  ('UA-445','ORD→MIA',165,'SICK','CLEAR',CURRENT_TIMESTAMP()),
  ('DL-892','DFW→SEA',0,'OK','STORM',CURRENT_TIMESTAMP()),
  ('SW-1201','ATL→BOS',0,'NO_SHOW','CLEAR',CURRENT_TIMESTAMP()),
  ('BA-178','LHR→JFK',45,'OK','WIND',CURRENT_TIMESTAMP()),
  ('LH-454','FRA→ORD',90,'OK','FOG',CURRENT_TIMESTAMP()),
  ('AA-999','ORD→JFK',180,'SICK','STORM',CURRENT_TIMESTAMP()),
  ('DL-777','ATL→LAX',200,'NO_SHOW','STORM',CURRENT_TIMESTAMP()),
  ('UA-555','DEN→ORD',120,'SICK','FOG',CURRENT_TIMESTAMP()),
  ('EK-201','DXB→LHR',0,'OK','CLEAR',CURRENT_TIMESTAMP())" 2>/dev/null || true

echo "  ✅ BigQuery ready"

# ── Create .env file ──────────────────────────────────────────────────────────
cat > .env << EOF
GCP_PROJECT_ID=${PROJECT_ID}
GCP_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-pro-preview-03-25
BQ_DATASET=irrops_audit
BQ_TABLE=audit_log
BQ_STREAM_TABLE=flight_streams
PUBSUB_TOPIC=irrops-events
CONFIDENCE_THRESHOLD=0.75
EOF
echo "  ✅ .env file created"

# ── Shell profile ─────────────────────────────────────────────────────────────
echo ""
echo "📝 Add these to your ~/.bashrc or ~/.zshrc for persistence:"
echo "   export GCP_PROJECT_ID=$PROJECT_ID"
echo "   export GCP_LOCATION=us-central1"
echo "   export GEMINI_MODEL=gemini-2.5-pro-preview-03-25"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✅ Setup Complete!                               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Project : $PROJECT_ID"
echo "  Region  : us-central1"
echo ""
echo "  Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. See docs/SETUP_GUIDE.md for full instructions"
echo ""
