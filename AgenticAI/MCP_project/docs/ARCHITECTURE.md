# IRROPS Platform — Architecture Deep Dive

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   INPUT LAYER                                 │
│   Flight ACARS  ·  Crew Rosters  ·  Weather/NOTAMs           │
│   Cloud Pub/Sub topic: irrops-events                         │
└─────────────────────────┬────────────────────────────────────┘
                          │ streaming events
┌─────────────────────────▼────────────────────────────────────┐
│              SERVICE 1: ANOMALY DETECTOR  :8080               │
│   • Scans streaming data for IRROPS anomalies                 │
│   • Rule-based detection + Gemini 2.5 Pro classification      │
│   • MCP Tools: scan_flight_streams, classify_irrops_event     │
│                publish_to_resolution_queue                    │
└─────────────────────────┬────────────────────────────────────┘
                          │ classified event
┌─────────────────────────▼────────────────────────────────────┐
│             SERVICE 2: RESOLUTION AGENT  :8081                │
│   ORCHESTRATOR (ADK + Gemini 2.5 Pro)                        │
│   • Decomposes event into multi-agent resolution plan         │
│   • Delegates to specialist agents via MCP                    │
│                                                               │
│   FLIGHT_AGENT    CREW_AGENT       OPS_AGENT                  │
│   rebook_pax      check_fdp        swap_gate                  │
│   cancel_flight   find_crew        sub_aircraft               │
│   notify_pax      reassign_crew    update_aodb                │
└─────────────────────────┬────────────────────────────────────┘
                          │ action results
┌─────────────────────────▼────────────────────────────────────┐
│              SERVICE 3: AUDIT SERVICE  :8082                  │
│   • Gemini 2.5 Pro assesses confidence of each action         │
│   • Auto-approve (≥75%) or escalate to controller            │
│   • Writes every decision to BigQuery audit log               │
│   • Ops controller approves/rejects via UI                    │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│                  GOOGLE CLOUD PLATFORM                        │
│   Vertex AI (Gemini 2.5 Pro)  ·  Cloud Pub/Sub               │
│   BigQuery (audit_log)         ·  Cloud Run                   │
│   Firestore (state)            ·  IAM (auth)                  │
└──────────────────────────────────────────────────────────────┘
```

---

## MCP Protocol Flow

```
UI / User
   │
   │  1. Trigger IRROPS event
   ▼
Orchestrator Agent (MCP Client)
   │
   │  2. query_tool_registry()  →  discovers available tools
   │  3. decompose_irrops()     →  Gemini creates resolution DAG
   ▼
MCP Host (Session Manager)
   │
   │  4. Routes tool calls to correct MCP Server
   ▼
Specialist MCP Servers
   │  5. flight_agent.rebook_passengers()
   │  6. crew_agent.check_fdp_limits()
   │  7. ops_agent.update_aodb()
   ▼
Enterprise Systems
   │  8. BigQuery, Pub/Sub, AODB, ACARS
   ▼
Audit Service (MCP Server)
   │  9. assess_confidence()  →  auto-approve or escalate
   │  10. log_to_bigquery()   →  immutable audit trail
   ▼
Ops Controller (Human-in-the-Loop)
   │  11. approve() / reject()  →  for escalated actions
   ▼
BigQuery Audit Log
   12. Full regulatory record of every AI decision
```

---

## Data Flow — Demo 1 (Anomaly Detection)

```
BASE_FLIGHT_DATA (simulated ACARS/AODB)
   │
   ▼
detect_anomaly()          ← rule-based: delay > 120min, crew NO_SHOW, weather STORM
   │
   ▼
classify_with_gemini()    ← Gemini 2.5 Pro: irrops_type, priority_score, auto_resolve
   │
   ▼
_detected_events{}        ← in-memory store (Firestore in production)
   │
   ▼
/scan REST endpoint       ← UI polls every 4 seconds
   │
   ▼
React UI                  ← renders live event feed with severity badges
```

---

## Data Flow — Demo 2 (Resolution)

```
IRROPS Event
   │
   ▼
/decompose endpoint
   │
   ▼
orchestrate_with_gemini() ← Gemini 2.5 Pro creates resolution_steps DAG
   │
   ▼
resolution_steps[]        ← ordered list: [{agent, tool, rationale, priority}]
   │
   ├─▶ /execute  ORCHESTRATOR.decompose_irrops()
   ├─▶ /execute  CREW_AGENT.check_fdp_limits()
   ├─▶ /execute  CREW_AGENT.find_available_crew()
   ├─▶ /execute  FLIGHT_AGENT.rebook_passengers()
   ├─▶ /execute  OPS_AGENT.update_aodb()
   └─▶ /execute  FLIGHT_AGENT.notify_passengers()
   │
   ▼
React UI shows each step: PENDING → RUNNING → SUCCESS/FAILED
```

---

## Data Flow — Demo 3 (Audit)

```
Agent Action
   │
   ▼
/assess endpoint
   │
   ▼
assess_confidence()       ← Gemini 2.5 Pro rates 0.0–1.0
   │
   ├─ confidence ≥ 0.75 AND no regulatory_impact
   │   └─▶ AUTO_APPROVED → write_to_bigquery()
   │
   └─ confidence < 0.75 OR regulatory_impact = True
       └─▶ PENDING_APPROVAL → _pending{} queue
               │
               ▼
           Ops Controller (UI)
               │
               ├─▶ /approve/{action_id} → CONTROLLER_APPROVED → BigQuery
               └─▶ /reject/{action_id}  → CONTROLLER_REJECTED → BigQuery
```

---

## GCP Services Used

| Service | Purpose | Where Used |
|---------|---------|-----------|
| **Vertex AI** | Gemini 2.5 Pro inference | All 3 services |
| **Cloud Run** | Serverless container hosting | All 4 services |
| **Pub/Sub** | Event streaming | Anomaly Detector |
| **BigQuery** | Audit log storage | Audit Service |
| **Firestore** | Task state persistence | Resolution Agent |
| **Artifact Registry** | Docker image storage | Deployment |
| **IAM** | Authentication & authorization | All services |
| **Cloud Scheduler** | Periodic scan triggers | Production |

---

## Key Design Decisions

**Why MCP instead of direct API calls?**
MCP gives the Orchestrator tool *discovery* — it doesn't need to know upfront which agents exist. New specialist agents register themselves and are discovered automatically at runtime.

**Why Gemini 2.5 Pro for orchestration?**
The resolution plan requires understanding airline operations context — FDP regulations, passenger welfare, operational priorities. Gemini's training includes this domain knowledge, eliminating the need to encode it as rules.

**Why separate Cloud Run services?**
Each service scales independently. During a hub-wide IRROPS event, the Resolution Agent may need 10x instances while the Audit Service stays at 1. Independent deployments also allow zero-downtime updates per service.

**Why BigQuery for audit logs?**
Airline regulators require queryable, tamper-evident records. BigQuery provides columnar storage, SQL querying, and integration with compliance tools. It also enables analytics — which IRROPS types occur most, average confidence scores, controller approval rates.
