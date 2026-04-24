# ✈️ Airline MCP_IRROPS_Lab — Airline IRROPS Agentic AI Platform

> **Enterprise-grade MCP (Model Context Protocol) platform for Airline Irregular Operations management**
> Built for educational purposes — AIBEES Labs · MCP_IRROPS_Lab · MCP Enterprise AI Series

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini%202.5%20Pro-orange.svg)](https://cloud.google.com/vertex-ai)
[![MCP](https://img.shields.io/badge/MCP-SSE%20Protocol-green.svg)](https://modelcontextprotocol.io)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4.svg)](https://cloud.google.com/run)

---

## 📖 What This Platform Demonstrates

This platform teaches **Model Context Protocol (MCP)** through a real-world airline operations use case. When flights are disrupted, the platform:

1. **Detects anomalies** from streaming flight/crew/weather data in BigQuery
2. **Resolves disruptions** using AI agents coordinated via true MCP tool calls
3. **Audits every decision** with confidence scoring and human-in-the-loop oversight

### The MCP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React UI  :3000                           │
│        Demo 1       │       Demo 2       │      Demo 3       │
│   Anomaly Detection │ Agent Resolution  │  Audit & HITL    │
└──────────┬──────────┴────────┬───────────┴────────┬─────────┘
           │ REST              │ REST               │ REST
    :8080  ▼           :8081   ▼            :8082   ▼
┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐
│   Anomaly    │  │   Resolution      │  │  Audit Service   │
│   Detector   │  │   Agent           │  │  MCP Server      │
│  MCP Server  │  │   MCP Server      │  │                  │
│              │  │  ┌─────────────┐  │  │  assess_route()  │
│ scan()       │  │  │ORCHESTRATOR │  │  │  approve()       │
│ classify()   │  │  │FLIGHT_AGENT │  │  │  reject()        │
│ publish()    │  │  │CREW_AGENT   │  │  │  audit_log()     │
│              │  │  │OPS_AGENT    │  │  │                  │
└──────┬───────┘  └───────┬───────────┘  └────────┬─────────┘
       │                  │                        │
       └──────────────────┴────────────────────────┘
                          │
              ┌───────────▼────────────┐
              │   MCP Protocol (SSE)   │
              │  /sse  +  /messages    │
              └───────────┬────────────┘
                          │
              ┌───────────▼────────────┐
              │    Google Cloud        │
              │  Vertex AI · BigQuery  │
              │  Pub/Sub · Cloud Run   │
              └────────────────────────┘
```

---

## 🏗️ Project Structure

```
MCP_IRROPS_Lab/
│
├── 📁 services/                    # Python MCP Backend Services
│   ├── 📁 anomaly-detector/        # Service 1 — Port 8080
│   │   ├── main.py                 # FastAPI + MCP Server (SSE)
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── 📁 resolution-agent/        # Service 2 — Port 8081
│   │   ├── main.py                 # Orchestrator + 3 Specialist Agents
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── 📁 audit-service/           # Service 3 — Port 8082
│       ├── main.py                 # HITL + BigQuery audit trail
│       ├── requirements.txt
│       └── Dockerfile
│
├── 📁 frontend/                    # React TypeScript UI
│   ├── 📁 src/
│   │   ├── App.tsx                 # Main UI — all 3 demos
│   │   └── index.tsx
│   ├── 📁 public/
│   │   └── index.html
│   └── package.json
│
├── 📁 scripts/                     # Setup & deployment scripts
│   ├── setup-gcp.ps1               # Windows: GCP + venv setup
│   ├── setup-gcp.sh                # Mac/Linux: GCP + venv setup
│   ├── create-bigquery.ps1         # Windows: BigQuery setup
│   ├── create-bigquery.sh          # Mac/Linux: BigQuery setup
│   └── seed-flight-data.sql        # Flight stream data
│
├── 📁 docs/                        # Teaching documentation
│   ├── SETUP_GUIDE.md              # Step-by-step student setup
│   ├── LECTURE_GUIDE.md            # MCP concepts for teaching
│   └── ARCHITECTURE.md             # Deep dive architecture
│
├── 📁 .github/workflows/
│   └── deploy.yml                  # CI/CD to Cloud Run
│
├── .gitignore
├── deploy.sh                       # One-command Cloud Run deploy
└── README.md                       # This file
```

---

## ⚡ Quick Start (Local Development)

> **Full step-by-step instructions**: See [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/MCP_IRROPS_Lab.git
cd MCP_IRROPS_Lab

# 2. Setup GCP
./scripts/setup-gcp.sh          # Mac/Linux
# OR
.\scripts\setup-gcp.ps1        # Windows PowerShell

# 3. Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Mac/Linux
.venv\Scripts\Activate.ps1     # Windows

# 4. Start services (4 separate terminals)
cd services/anomaly-detector && pip install -r requirements.txt && python main.py
cd services/resolution-agent && pip install -r requirements.txt && python main.py
cd services/audit-service    && pip install -r requirements.txt && python main.py
cd frontend && npm install --legacy-peer-deps && npm start

# 5. Open http://localhost:3000
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCP_PROJECT_ID` | `your-project-id` | Your GCP project ID |
| `GCP_LOCATION` | `us-central1` | GCP region |
| `PORT` | `8080/8081/8082` | Service port |
| `GEMINI_MODEL` | `gemini-2.5-pro-preview-03-25` | Gemini model version |
| `BQ_DATASET` | `irrops_audit` | BigQuery dataset |
| `BQ_TABLE` | `audit_log` | BigQuery audit table |
| `BQ_STREAM_TABLE` | `flight_streams` | BigQuery flight data table |

---

## 🛠️ MCP Tool Registry

### Service 1 — Anomaly Detector (:8080)
| Tool | Description |
|------|-------------|
| `scan_flight_streams` | Fetch from BigQuery + detect anomalies |
| `classify_irrops_event` | Gemini classifies event type and priority |
| `publish_to_resolution_queue` | Dispatch to Pub/Sub |

### Service 2 — Resolution Agent (:8081)
| Agent | Tool | Description |
|-------|------|-------------|
| ORCHESTRATOR | `decompose_irrops` | Gemini creates resolution DAG |
| FLIGHT_AGENT | `rebook_passengers` | Reaccommodate passengers |
| FLIGHT_AGENT | `cancel_flight` | Cancel + vouchers |
| FLIGHT_AGENT | `notify_passengers` | SMS/email/app alerts |
| CREW_AGENT | `check_fdp_limits` | FAA Part 117 legality |
| CREW_AGENT | `find_available_crew` | Reserve crew search |
| CREW_AGENT | `reassign_crew` | Crew assignment |
| OPS_AGENT | `swap_gate` | Gate reassignment |
| OPS_AGENT | `substitute_aircraft` | Tail swap |
| OPS_AGENT | `update_aodb` | Ops database update |

### Service 3 — Audit Service (:8082)
| Tool | Description |
|------|-------------|
| `assess_and_route` | Confidence scoring → approve or escalate |
| `log_to_audit_trail` | Write to BigQuery |
| `controller_approve` | HITL approval |
| `controller_reject` | HITL rejection |
| `generate_compliance_report` | Regulatory summary |

---

## 🚀 Deploy to Cloud Run

```bash
export GCP_PROJECT_ID="your-project-id"
chmod +x deploy.sh
./deploy.sh
```

---

## 📚 Teaching Resources

- [`docs/SETUP_GUIDE.md`](docs/SETUP_GUIDE.md) — Complete student setup walkthrough
- [`docs/LECTURE_GUIDE.md`](docs/LECTURE_GUIDE.md) — MCP concepts, 70-20-10 ROI model, demo script
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Data flow, API mapping, design decisions

---

## 🐛 Common Issues

| Error | Fix |
|-------|-----|
| `npm not recognized` | Install Node.js 18+ from nodejs.org, restart VS Code |
| `Can't resolve './App'` | Move frontend to path without `#` character |
| `ajv module not found` | `npm install ajv@^8 --legacy-peer-deps` |
| `gemini model not found` | `gcloud services enable aiplatform.googleapis.com` |
| `BigQuery dataset not found` | Run `scripts/create-bigquery.ps1` |
| `signal aborted` timeout | Already handled — 30s timeout in App.tsx |
| `dict() deprecated` | Already fixed — uses `model_dump()` |
| `vertexai version conflict` | Use `vertexai==1.71.1` + `google-cloud-aiplatform==1.71.1` |

---

*AIBEES Labs · MCP_IRROPS_Lab · MCP Enterprise AI Series · Built with Python · React · Vertex AI · Google ADK · Cloud Run · BigQuery*
