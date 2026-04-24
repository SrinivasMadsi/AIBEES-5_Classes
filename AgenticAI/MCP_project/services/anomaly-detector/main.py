"""
╔══════════════════════════════════════════════════════════════╗
║  SERVICE 1 — Anomaly Detector MCP Server                     ║
║  Port: 8080                                                  ║
║                                                              ║
║  Architecture:                                               ║
║  BigQuery (flight_streams) → detect_anomaly() [rules]        ║
║       → classify_with_gemini() [Vertex AI]                   ║
║       → MCP Tools [SSE Protocol]                             ║
║       → Pub/Sub [dispatch to resolution agent]               ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ── MCP SDK Imports ──────────────────────────────────────────────────────────
# These are the core MCP primitives:
#   Server          — the MCP server runtime that manages tool registration
#   SseServerTransport — SSE (Server-Sent Events) wire protocol for MCP
#   Tool            — schema definition for each tool
#   TextContent     — standard return type for tool call results
try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# ── Optional GCP imports with graceful fallback ───────────────────────────────
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

try:
    from google.cloud import bigquery, pubsub_v1
    BQ_AVAILABLE     = True
    PUBSUB_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE     = False
    PUBSUB_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("anomaly-detector")

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID       = os.getenv("GCP_PROJECT_ID",    "your-project-id")
LOCATION         = os.getenv("GCP_LOCATION",      "us-central1")
PUBSUB_TOPIC     = os.getenv("PUBSUB_TOPIC",      "irrops-events")
PORT             = int(os.getenv("PORT",           "8080"))
GEMINI_MODEL     = os.getenv("GEMINI_MODEL",       "gemini-2.5-pro-preview-03-25")
BQ_DATASET       = os.getenv("BQ_DATASET",         "irrops_audit")
BQ_STREAM_TABLE  = os.getenv("BQ_STREAM_TABLE",    "flight_streams")

# ── Init Vertex AI ────────────────────────────────────────────────────────────
if VERTEX_AVAILABLE:
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logger.info(f"✅ Vertex AI initialized — project={PROJECT_ID} model={GEMINI_MODEL}")
    except Exception as e:
        logger.warning(f"⚠️  Vertex AI init failed (demo mode active): {e}")
        VERTEX_AVAILABLE = False

# ── In-memory event store ─────────────────────────────────────────────────────
_detected_events: dict[str, dict] = {}

# ── Fallback data (used when BigQuery unavailable) ────────────────────────────
FALLBACK_DATA = [
    {"flight": "AA-301",  "route": "JFK→LAX", "delay_min": 0,   "crew_status": "OK",      "weather": "CLEAR"},
    {"flight": "UA-445",  "route": "ORD→MIA", "delay_min": 165, "crew_status": "SICK",    "weather": "CLEAR"},
    {"flight": "DL-892",  "route": "DFW→SEA", "delay_min": 0,   "crew_status": "OK",      "weather": "STORM"},
    {"flight": "SW-1201", "route": "ATL→BOS", "delay_min": 0,   "crew_status": "NO_SHOW", "weather": "CLEAR"},
    {"flight": "BA-178",  "route": "LHR→JFK", "delay_min": 45,  "crew_status": "OK",      "weather": "WIND"},
    {"flight": "LH-454",  "route": "FRA→ORD", "delay_min": 90,  "crew_status": "OK",      "weather": "FOG"},
]


# ══════════════════════════════════════════════════════════════════════════════
# DATA LAYER — BigQuery fetch
# ══════════════════════════════════════════════════════════════════════════════

def fetch_flight_data() -> list[dict]:
    """
    Fetch latest flight records from BigQuery flight_streams table.
    In production: this table is updated in real-time by ACARS/AODB feeds.
    Falls back to static data if BigQuery is unavailable.
    """
    if not BQ_AVAILABLE:
        logger.warning("BigQuery unavailable — using fallback static data")
        return FALLBACK_DATA

    try:
        client = bigquery.Client(project=PROJECT_ID)
        query  = f"""
            SELECT flight, route, delay_min, crew_status, weather, updated_at
            FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_STREAM_TABLE}`
            ORDER BY updated_at DESC
        """
        logger.info(f"📊 Fetching from BigQuery: {BQ_DATASET}.{BQ_STREAM_TABLE}")
        rows = [dict(row) for row in client.query(query).result()]

        if not rows:
            logger.warning("BigQuery returned 0 rows — using fallback data")
            return FALLBACK_DATA

        # Simulate real-time variance in delay values
        for row in rows:
            row["delay_min"] = max(0, row["delay_min"] + random.randint(-5, 15))

        logger.info(f"✅ Fetched {len(rows)} records from BigQuery")
        return rows

    except Exception as e:
        logger.warning(f"BigQuery fetch failed: {e} — using fallback data")
        return FALLBACK_DATA


# ══════════════════════════════════════════════════════════════════════════════
# DETECTION LOGIC — Rule-based anomaly detection
# ══════════════════════════════════════════════════════════════════════════════

def detect_anomaly(record: dict) -> dict | None:
    """
    Rule-based anomaly detection.
    Returns an anomaly dict if an IRROPS condition is found, else None.

    Rules:
    - delay_min >= 120  → MAJOR_DELAY (HIGH)
    - delay_min >= 45   → DELAY (MEDIUM)
    - crew == NO_SHOW   → CREW_ISSUE (CRITICAL)
    - crew == SICK      → CREW_ISSUE (HIGH)
    - weather == STORM  → WEATHER_ALERT (HIGH)
    - weather == FOG    → WEATHER_ALERT (MEDIUM)
    """
    anomalies      = []
    severity       = "LOW"
    severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def escalate(new_level: str):
        nonlocal severity
        severity = severity_order[max(
            severity_order.index(severity),
            severity_order.index(new_level)
        )]

    # Check delay
    delay = record.get("delay_min", 0)
    if delay >= 120:
        anomalies.append(f"MAJOR_DELAY: {delay}min delay detected")
        escalate("HIGH")
    elif delay >= 45:
        anomalies.append(f"DELAY: {delay}min delay")
        escalate("MEDIUM")

    # Check crew status
    crew = record.get("crew_status", "OK")
    if crew == "NO_SHOW":
        anomalies.append("CREW_ISSUE: NO_SHOW — captain unavailable at departure")
        escalate("CRITICAL")
    elif crew == "SICK":
        anomalies.append("CREW_ISSUE: SICK — crew member reported sick")
        escalate("HIGH")

    # Check weather
    weather = record.get("weather", "CLEAR")
    if weather == "STORM":
        anomalies.append("WEATHER_ALERT: Severe convective storm at destination")
        escalate("HIGH")
    elif weather == "FOG":
        anomalies.append("WEATHER_ALERT: Low visibility FOG — may be below minimums")
        escalate("MEDIUM")

    if not anomalies:
        return None

    event_id = (
        f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        f"-{record['flight'].replace('-', '')}"
        f"-{random.randint(100, 999)}"
    )

    return {
        "event_id":   event_id,
        "flight":     record["flight"],
        "route":      record.get("route", "UNKNOWN"),
        "severity":   severity,
        "anomalies":  anomalies,
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "source":     "BigQuery" if BQ_AVAILABLE else "fallback",
        "raw_record": {k: v for k, v in record.items() if k != "updated_at"},
    }


# ══════════════════════════════════════════════════════════════════════════════
# AI LAYER — Vertex AI Gemini classification
# ══════════════════════════════════════════════════════════════════════════════

def _mock_classification(event: dict) -> dict:
    """Deterministic mock when Vertex AI is unavailable."""
    severity     = event.get("severity", "MEDIUM")
    priority_map = {"LOW": 3, "MEDIUM": 5, "HIGH": 8, "CRITICAL": 10}
    has_crew     = any("CREW" in a for a in event.get("anomalies", []))
    return {
        "irrops_type":          "CREW_SHORTAGE" if has_crew else "DELAY",
        "resolution_agents":    ["FLIGHT_AGENT", "CREW_AGENT", "OPS_AGENT"],
        "estimated_pax_impact": random.randint(80, 180),
        "auto_resolve":         severity in ("LOW", "MEDIUM"),
        "priority_score":       priority_map.get(severity, 5),
    }


async def classify_with_gemini(event: dict) -> dict:
    """
    Send the anomaly event to Vertex AI Gemini for intelligent classification.
    Gemini determines: IRROPS type, which agents to invoke, priority, and
    whether it can be auto-resolved or needs human review.
    """
    if not VERTEX_AVAILABLE:
        logger.info("Using mock classification (Vertex AI unavailable)")
        return _mock_classification(event)
    try:
        model  = GenerativeModel(GEMINI_MODEL)
        prompt = f"""
You are an expert airline operations AI specializing in IRROPS classification.

Analyze this irregular operation event and classify it:

Event Details:
{json.dumps(event, indent=2)}

Return ONLY valid JSON with exactly these fields:
{{
  "irrops_type": "one of: DELAY | CANCELLATION | DIVERSION | CREW_SHORTAGE | WEATHER_HOLD",
  "resolution_agents": ["list from: FLIGHT_AGENT, CREW_AGENT, OPS_AGENT"],
  "estimated_pax_impact": <integer — estimated number of passengers affected>,
  "auto_resolve": <boolean — true if confidence > 0.85 and severity not CRITICAL>,
  "priority_score": <integer 1-10>
}}

Consider FAA Part 117 FDP regulations for crew-related events.
"""
        response = await asyncio.to_thread(model.generate_content, prompt)
        text     = response.text.strip().strip("```json").strip("```").strip()
        result   = json.loads(text)
        logger.info(
            f"🤖 Gemini classified {event['event_id']}: "
            f"{result.get('irrops_type')} — priority {result.get('priority_score')}/10"
        )
        return result
    except Exception as e:
        logger.warning(f"Gemini classification failed: {e} — using mock")
        return _mock_classification(event)


# ══════════════════════════════════════════════════════════════════════════════
# MCP SERVER — Tool definitions and handlers
# ══════════════════════════════════════════════════════════════════════════════

# Create the MCP Server instance
# This is the core MCP runtime that manages tool registration and routing
mcp = Server("irrops-anomaly-detector") if MCP_AVAILABLE else None


if MCP_AVAILABLE and mcp:

    @mcp.list_tools()
    async def list_tools() -> list[Tool]:
        """
        MCP tool registry — called by MCP Clients to discover available tools.
        The Orchestrator Agent reads these schemas to understand what this
        service can do and when to call each tool.
        """
        return [
            Tool(
                name="scan_flight_streams",
                description=(
                    "Fetch the latest flight status data from BigQuery and scan "
                    "for IRROPS anomalies. Detects delays, crew issues, and weather "
                    "alerts. Returns a list of detected anomaly events with severity."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "enum": ["ACARS", "CREW_ROSTER", "WEATHER", "ALL"],
                            "default": "ALL",
                            "description": "Data source to scan"
                        }
                    },
                },
            ),
            Tool(
                name="classify_irrops_event",
                description=(
                    "Use Vertex AI Gemini to intelligently classify a detected anomaly. "
                    "Determines IRROPS type, affected passenger count, which specialist "
                    "agents should handle it, and whether it can be auto-resolved."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "The event ID returned by scan_flight_streams"
                        }
                    },
                    "required": ["event_id"],
                },
            ),
            Tool(
                name="publish_to_resolution_queue",
                description=(
                    "Publish a classified IRROPS event to Google Cloud Pub/Sub "
                    "to trigger the Resolution Agent pipeline."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                        "agents":   {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of specialist agents to invoke"
                        },
                    },
                    "required": ["event_id", "priority", "agents"],
                },
            ),
        ]

    @mcp.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """
        MCP tool call handler — executes the requested tool and returns results.
        This is called by the Orchestrator Agent via the MCP SSE protocol.
        """
        logger.info(f"🔧 MCP tool call: {name}({json.dumps(arguments)[:80]}...)")

        # ── Tool: scan_flight_streams ──────────────────────────────────────────
        if name == "scan_flight_streams":
            flight_data = fetch_flight_data()
            detected    = []
            for record in flight_data:
                anomaly = detect_anomaly(record)
                if anomaly:
                    _detected_events[anomaly["event_id"]] = anomaly
                    detected.append(anomaly)

            result = {
                "anomalies_detected": len(detected),
                "scanned":            len(flight_data),
                "data_source":        f"BigQuery:{BQ_DATASET}.{BQ_STREAM_TABLE}",
                "events":             detected,
            }
            logger.info(f"Scan: {len(detected)}/{len(flight_data)} anomalies detected")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ── Tool: classify_irrops_event ────────────────────────────────────────
        elif name == "classify_irrops_event":
            event_id = arguments.get("event_id")
            event    = _detected_events.get(event_id)
            if not event:
                return [TextContent(type="text", text=json.dumps({
                    "error": f"Event {event_id} not found. Run scan_flight_streams first."
                }))]

            classification          = await classify_with_gemini(event)
            event["classification"] = classification
            _detected_events[event_id] = event

            result = {
                "event_id":       event_id,
                "flight":         event["flight"],
                "severity":       event["severity"],
                "classification": classification,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ── Tool: publish_to_resolution_queue ──────────────────────────────────
        elif name == "publish_to_resolution_queue":
            event_id = arguments["event_id"]
            event    = _detected_events.get(event_id, {})
            status   = "[DEMO MODE] No Pub/Sub available"

            if PUBSUB_AVAILABLE:
                try:
                    publisher  = pubsub_v1.PublisherClient()
                    topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
                    payload    = json.dumps({
                        "event_id":  event_id,
                        "flight":    event.get("flight", "UNKNOWN"),
                        "priority":  arguments["priority"],
                        "agents":    arguments["agents"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }).encode("utf-8")
                    msg_id = publisher.publish(topic_path, payload).result(timeout=10)
                    status = f"Published to Pub/Sub — message_id={msg_id}"
                except Exception as e:
                    status = f"Pub/Sub error: {e}"

            result = {
                "event_id":        event_id,
                "status":          status,
                "agents_notified": arguments["agents"],
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP — REST endpoints + MCP SSE transport
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="IRROPS Anomaly Detector",
    description="MCP Server for real-time airline IRROPS anomaly detection",
    version="3.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── MCP SSE Endpoints ────────────────────────────────────────────────────────
# These are the true MCP protocol endpoints.
# An ADK Orchestrator Agent connects to /sse to discover and call tools.

@app.get("/sse")
async def mcp_sse(request: Request):
    """
    MCP SSE endpoint — MCP Clients connect here to establish a persistent
    session and discover available tools via the MCP protocol.

    Usage: An ADK agent connects with:
      mcp_client = MCPClient("http://localhost:8080/sse")
      tools = await mcp_client.list_tools()
    """
    if not MCP_AVAILABLE or not mcp:
        return {"error": "MCP SDK not available — install with: pip install mcp"}

    transport = SseServerTransport("/mcp/messages")
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(
            streams[0], streams[1],
            mcp.create_initialization_options()
        )


@app.post("/mcp/messages")
async def mcp_messages(request: Request):
    """
    MCP messages endpoint — handles incoming tool call requests from MCP Clients.
    This is the POST half of the SSE protocol.
    """
    if not MCP_AVAILABLE or not mcp:
        return {"error": "MCP SDK not available"}

    transport = SseServerTransport("/mcp/messages")
    await transport.handle_post_message(
        request.scope, request.receive, request._send
    )


# ── REST Endpoints ───────────────────────────────────────────────────────────
# These are convenience endpoints for the React UI and direct testing.
# In a pure MCP deployment, only the /sse and /mcp/messages endpoints are needed.

@app.get("/health")
async def health():
    """Health check — shows service status and capabilities."""
    return {
        "status":          "ok",
        "service":         "anomaly-detector",
        "version":         "3.0.0",
        "mcp_available":   MCP_AVAILABLE,
        "mcp_endpoint":    "/sse",
        "vertex_ai":       VERTEX_AVAILABLE,
        "bigquery":        BQ_AVAILABLE,
        "model":           GEMINI_MODEL,
        "project":         PROJECT_ID,
        "data_source":     f"{BQ_DATASET}.{BQ_STREAM_TABLE}",
        "events_detected": len(_detected_events),
        "tools": [
            "scan_flight_streams",
            "classify_irrops_event",
            "publish_to_resolution_queue",
        ],
    }


@app.get("/scan")
async def scan():
    """REST: Scan flight streams for anomalies (called by React UI)."""
    logger.info("REST /scan called")
    flight_data = fetch_flight_data()
    detected    = []
    for record in flight_data:
        anomaly = detect_anomaly(record)
        if anomaly:
            _detected_events[anomaly["event_id"]] = anomaly
            detected.append(anomaly)

    return {
        "anomalies_detected": len(detected),
        "scanned":            len(flight_data),
        "data_source":        f"BigQuery: {BQ_DATASET}.{BQ_STREAM_TABLE}" if BQ_AVAILABLE else "fallback",
        "events":             detected,
    }


@app.get("/stream-data")
async def stream_data():
    """REST: Return raw flight stream data currently in BigQuery."""
    data = fetch_flight_data()
    return {
        "source":     f"BigQuery: {PROJECT_ID}.{BQ_DATASET}.{BQ_STREAM_TABLE}",
        "records":    len(data),
        "flights":    data,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/classify/{event_id}")
async def classify(event_id: str):
    """REST: Classify a detected event using Vertex AI Gemini."""
    event = _detected_events.get(event_id)
    if not event:
        raise HTTPException(404, f"Event {event_id} not found")
    classification          = await classify_with_gemini(event)
    event["classification"] = classification
    return {"event_id": event_id, "flight": event["flight"], "classification": classification}


class PublishRequest(BaseModel):
    event_id: str
    priority: int
    agents:   list[str]


@app.post("/publish")
async def publish(body: PublishRequest):
    """REST: Publish event to Pub/Sub."""
    event  = _detected_events.get(body.event_id, {})
    status = "[DEMO] No Pub/Sub"
    if PUBSUB_AVAILABLE:
        try:
            publisher  = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
            payload    = json.dumps({
                "event_id":  body.event_id,
                "flight":    event.get("flight"),
                "priority":  body.priority,
                "agents":    body.agents,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }).encode()
            msg_id = publisher.publish(topic_path, payload).result(timeout=10)
            status = f"Published — message_id={msg_id}"
        except Exception as e:
            status = f"Pub/Sub error: {e}"
    return {"event_id": body.event_id, "status": status, "agents_notified": body.agents}


@app.get("/events")
async def get_events():
    """REST: Return all detected events in memory."""
    return {"events": list(_detected_events.values()), "total": len(_detected_events)}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  IRROPS Anomaly Detector — Starting Up")
    logger.info("=" * 60)
    logger.info(f"  Port       : {PORT}")
    logger.info(f"  Project    : {PROJECT_ID}")
    logger.info(f"  Model      : {GEMINI_MODEL}")
    logger.info(f"  Vertex AI  : {'✅ Connected' if VERTEX_AVAILABLE else '⚠️  Demo mode'}")
    logger.info(f"  BigQuery   : {'✅ Connected' if BQ_AVAILABLE else '⚠️  Demo mode'}")
    logger.info(f"  MCP SSE    : {'✅ Enabled — /sse' if MCP_AVAILABLE else '⚠️  Not available'}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
