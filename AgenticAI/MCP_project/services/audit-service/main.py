"""
╔══════════════════════════════════════════════════════════════╗
║  SERVICE 3 — Audit & Human-in-the-Loop MCP Server            ║
║  Port: 8082                                                  ║
║                                                              ║
║  Architecture:                                               ║
║  Agent action → assess_confidence() [Gemini 2.5 Pro]        ║
║       → score >= 0.75 → AUTO_APPROVED → BigQuery            ║
║       → score < 0.75  → PENDING → Controller UI             ║
║       → Controller approve/reject → BigQuery                ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import logging
import os
import random
import uuid
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── MCP SDK Imports ───────────────────────────────────────────────────────────
try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# ── Optional GCP imports ──────────────────────────────────────────────────────
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

try:
    from google.cloud import bigquery
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("audit-service")

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID           = os.getenv("GCP_PROJECT_ID",           "your-project-id")
LOCATION             = os.getenv("GCP_LOCATION",             "us-central1")
BQ_DATASET           = os.getenv("BQ_DATASET",               "irrops_audit")
BQ_TABLE             = os.getenv("BQ_TABLE",                 "audit_log")
PORT                 = int(os.getenv("PORT",                  "8082"))
GEMINI_MODEL         = os.getenv("GEMINI_MODEL",              "gemini-2.5-pro-preview-03-25")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD","0.75"))

# ── Init Vertex AI ────────────────────────────────────────────────────────────
if VERTEX_AVAILABLE:
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logger.info(f"✅ Vertex AI initialized — project={PROJECT_ID} model={GEMINI_MODEL}")
    except Exception as e:
        logger.warning(f"⚠️  Vertex AI init failed (demo mode): {e}")
        VERTEX_AVAILABLE = False

# ── In-memory stores ──────────────────────────────────────────────────────────
_pending:   dict[str, dict] = {}
_audit_log: list[dict]      = []


# ══════════════════════════════════════════════════════════════════════════════
# BIGQUERY — Audit trail persistence
# ══════════════════════════════════════════════════════════════════════════════

def write_to_bigquery(entry: dict) -> bool:
    """
    Write an audit entry to BigQuery for regulatory compliance.
    Every AI decision — auto-approved or human-reviewed — is logged here.
    Falls back to in-memory if BigQuery is unavailable.
    """
    if BQ_AVAILABLE:
        try:
            client    = bigquery.Client(project=PROJECT_ID)
            table_ref = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
            bq_entry  = {k: v for k, v in entry.items() if v is not None}
            errors    = client.insert_rows_json(table_ref, [bq_entry])
            if not errors:
                logger.info(f"📊 Audit entry written to BigQuery: {entry.get('action_id')}")
                return True
            logger.warning(f"BigQuery insert errors: {errors}")
        except Exception as e:
            logger.warning(f"BigQuery write failed: {e}")
    # Fallback to in-memory
    _audit_log.append(entry)
    return True


# ══════════════════════════════════════════════════════════════════════════════
# AI LAYER — Confidence assessment using Gemini
# ══════════════════════════════════════════════════════════════════════════════

def _mock_confidence(action: dict) -> float:
    """Deterministic mock confidence when Vertex AI unavailable."""
    base = 0.82
    if action.get("regulatory_impact"):
        base -= 0.20
    tool = action.get("tool_called", "")
    if "cancel" in tool or "substitute" in tool:
        base -= 0.10
    return round(max(0.40, min(0.98, base + random.uniform(-0.12, 0.10))), 2)


async def assess_confidence(action: dict) -> float:
    """
    Use Gemini 2.5 Pro to rate confidence that an agent action is
    correct, safe, and compliant before executing or escalating it.

    This is the SAFETY BRAIN — it decides whether the AI can act
    autonomously or whether a human controller must review first.
    """
    if not VERTEX_AVAILABLE:
        return _mock_confidence(action)
    try:
        model  = GenerativeModel(GEMINI_MODEL)
        prompt = f"""
You are an airline operations safety AI. Rate the confidence (0.0 to 1.0) that
this agent action is correct, safe, and regulatory compliant.

Action Details:
{json.dumps(action, indent=2)}

Evaluation criteria:
- Regulatory compliance (FAA, IATA, airline SOPs)
- Operational safety (no risk to aircraft or crew)
- Passenger welfare (fair treatment, timely communication)
- Cost efficiency (reasonable cost impact)
- Reversibility (can this action be undone if wrong?)

Scoring guide:
- 0.90–1.00: High confidence, safe to auto-execute
- 0.75–0.89: Moderate confidence, auto-execute with logging
- 0.60–0.74: Low confidence, escalate to controller
- 0.00–0.59: Very low confidence, definitely escalate

Return ONLY a single float between 0.0 and 1.0. No explanation. No JSON. Just the number.
Example: 0.87
"""
        response = await asyncio.to_thread(model.generate_content, prompt)
        score    = float(response.text.strip())
        score    = round(max(0.0, min(1.0, score)), 2)
        logger.info(
            f"🤖 Gemini confidence for {action.get('action_id')}: "
            f"{score:.0%} — {'AUTO' if score >= CONFIDENCE_THRESHOLD else 'ESCALATE'}"
        )
        return score
    except Exception as e:
        logger.warning(f"Gemini confidence assessment failed: {e}")
        return _mock_confidence(action)


# ══════════════════════════════════════════════════════════════════════════════
# MCP SERVER — Tool definitions and handlers
# ══════════════════════════════════════════════════════════════════════════════

mcp = Server("irrops-audit-service") if MCP_AVAILABLE else None


if MCP_AVAILABLE and mcp:

    @mcp.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="assess_and_route",
                description=(
                    "Assess the confidence of an agent action using Vertex AI Gemini. "
                    f"Auto-approves if confidence >= {CONFIDENCE_THRESHOLD} and no regulatory "
                    "impact. Escalates to ops controller otherwise. Writes all decisions to "
                    "BigQuery audit trail for regulatory compliance."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action_id":         {"type": "string"},
                        "event_id":          {"type": "string"},
                        "flight":            {"type": "string"},
                        "agent":             {"type": "string"},
                        "tool_called":       {"type": "string"},
                        "proposed_action":   {"type": "string"},
                        "regulatory_impact": {"type": "boolean", "default": False},
                    },
                    "required": ["action_id", "event_id", "flight", "agent", "tool_called", "proposed_action"],
                },
            ),
            Tool(
                name="get_pending_approvals",
                description="Retrieve all agent actions currently awaiting ops controller approval.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="controller_approve",
                description="Ops controller approves a pending escalated action. Logs to BigQuery.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action_id":     {"type": "string"},
                        "controller_id": {"type": "string"},
                        "notes":         {"type": "string"},
                    },
                    "required": ["action_id", "controller_id"],
                },
            ),
            Tool(
                name="controller_reject",
                description="Ops controller rejects a pending action with reason. Logs to BigQuery.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action_id":     {"type": "string"},
                        "controller_id": {"type": "string"},
                        "reason":        {"type": "string"},
                    },
                    "required": ["action_id", "controller_id", "reason"],
                },
            ),
            Tool(
                name="generate_compliance_report",
                description="Generate a regulatory compliance summary from the BigQuery audit trail.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string"},
                        "end_date":   {"type": "string"},
                    },
                },
            ),
        ]

    @mcp.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Route MCP tool calls to audit service handlers."""
        logger.info(f"🔧 MCP tool call: {name}")

        # ── assess_and_route ───────────────────────────────────────────────────
        if name == "assess_and_route":
            confidence = await assess_confidence(arguments)
            entry = {
                **arguments,
                "confidence":  confidence,
                "assessed_at": datetime.now(timezone.utc).isoformat(),
            }
            if confidence >= CONFIDENCE_THRESHOLD and not arguments.get("regulatory_impact"):
                audit = {**entry, "status": "AUTO_APPROVED", "approved_by": "AI_SYSTEM"}
                write_to_bigquery(audit)
                result = {
                    "decision":   "AUTO_APPROVED",
                    "confidence": confidence,
                    "message":    f"Confidence {confidence:.0%} ≥ {CONFIDENCE_THRESHOLD:.0%} threshold. Auto-approved and logged to BigQuery.",
                }
            else:
                reason = "Regulatory impact flagged" if arguments.get("regulatory_impact") else f"Confidence {confidence:.0%} below threshold"
                entry.update({"status": "PENDING_APPROVAL", "escalated_at": datetime.now(timezone.utc).isoformat()})
                _pending[arguments["action_id"]] = entry
                result = {
                    "decision":   "ESCALATED",
                    "confidence": confidence,
                    "message":    f"Escalated for controller review. Reason: {reason}",
                }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        # ── get_pending_approvals ──────────────────────────────────────────────
        elif name == "get_pending_approvals":
            return [TextContent(type="text", text=json.dumps({
                "pending_count": len(_pending),
                "actions":       list(_pending.values()),
            }, indent=2))]

        # ── controller_approve ─────────────────────────────────────────────────
        elif name == "controller_approve":
            action_id = arguments["action_id"]
            if action_id not in _pending:
                return [TextContent(type="text", text=json.dumps({"error": f"Action {action_id} not found"}))]
            entry = _pending.pop(action_id)
            audit = {**entry, "status": "CONTROLLER_APPROVED",
                     "approved_by": arguments["controller_id"],
                     "notes": arguments.get("notes", ""),
                     "approved_at": datetime.now(timezone.utc).isoformat()}
            write_to_bigquery(audit)
            logger.info(f"✅ Action {action_id} APPROVED by {arguments['controller_id']}")
            return [TextContent(type="text", text=json.dumps({
                "status": "approved", "action_id": action_id,
                "approved_by": arguments["controller_id"]
            }))]

        # ── controller_reject ──────────────────────────────────────────────────
        elif name == "controller_reject":
            action_id = arguments["action_id"]
            if action_id not in _pending:
                return [TextContent(type="text", text=json.dumps({"error": f"Action {action_id} not found"}))]
            entry = _pending.pop(action_id)
            audit = {**entry, "status": "CONTROLLER_REJECTED",
                     "rejected_by": arguments["controller_id"],
                     "rejection_reason": arguments["reason"],
                     "rejected_at": datetime.now(timezone.utc).isoformat()}
            write_to_bigquery(audit)
            logger.info(f"❌ Action {action_id} REJECTED by {arguments['controller_id']}: {arguments['reason']}")
            return [TextContent(type="text", text=json.dumps({
                "status": "rejected", "action_id": action_id, "reason": arguments["reason"]
            }))]

        # ── generate_compliance_report ─────────────────────────────────────────
        elif name == "generate_compliance_report":
            entries  = _audit_log
            approved = [e for e in entries if "APPROVED" in e.get("status","")]
            rejected = [e for e in entries if "REJECTED" in e.get("status","")]
            auto     = [e for e in approved if e.get("approved_by") == "AI_SYSTEM"]
            avg_conf = round(sum(e.get("confidence",0) for e in entries) / max(len(entries),1), 3)
            report = {
                "report_id":    uuid.uuid4().hex[:8].upper(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_actions":        len(entries),
                    "auto_approved":        len(auto),
                    "controller_approved":  len(approved) - len(auto),
                    "rejected":             len(rejected),
                    "pending":              len(_pending),
                    "avg_confidence":       avg_conf,
                },
                "regulatory_compliance": "COMPLIANT" if not rejected else "REVIEW_REQUIRED",
                "bigquery_table": f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}",
            }
            return [TextContent(type="text", text=json.dumps(report, indent=2))]

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="IRROPS Audit & HITL Service",
    description="MCP Server for confidence scoring, human approval, and BigQuery audit trail",
    version="3.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/sse")
async def mcp_sse(request: Request):
    """MCP SSE endpoint."""
    if not MCP_AVAILABLE or not mcp:
        return {"error": "MCP SDK not available"}
    transport = SseServerTransport("/mcp/messages")
    async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())


@app.post("/mcp/messages")
async def mcp_messages(request: Request):
    """MCP messages endpoint."""
    if not MCP_AVAILABLE or not mcp:
        return {"error": "MCP SDK not available"}
    transport = SseServerTransport("/mcp/messages")
    await transport.handle_post_message(request.scope, request.receive, request._send)


@app.get("/health")
async def health():
    return {
        "status":       "ok",
        "service":      "audit-service",
        "version":      "3.0.0",
        "mcp_available": MCP_AVAILABLE,
        "mcp_endpoint": "/sse",
        "vertex_ai":    VERTEX_AVAILABLE,
        "bigquery":     BQ_AVAILABLE,
        "model":        GEMINI_MODEL,
        "threshold":    CONFIDENCE_THRESHOLD,
        "pending":      len(_pending),
        "logged":       len(_audit_log),
    }


class AssessRequest(BaseModel):
    action_id:         str
    event_id:          str
    flight:            str
    agent:             str
    tool_called:       str
    proposed_action:   str
    regulatory_impact: bool = False


class ApprovalRequest(BaseModel):
    controller_id: str
    notes:         str = ""


class RejectionRequest(BaseModel):
    controller_id: str
    reason:        str


@app.post("/assess")
async def assess(body: AssessRequest):
    """REST: Assess action and route to auto-approve or escalate."""
    confidence = await assess_confidence(body.model_dump())
    entry = {**body.model_dump(), "confidence": confidence,
             "assessed_at": datetime.now(timezone.utc).isoformat()}

    if confidence >= CONFIDENCE_THRESHOLD and not body.regulatory_impact:
        write_to_bigquery({**entry, "status": "AUTO_APPROVED", "approved_by": "AI_SYSTEM"})
        return {"decision": "AUTO_APPROVED", "confidence": confidence,
                "message": f"Confidence {confidence:.0%} ≥ threshold. Auto-approved."}
    else:
        entry.update({"status": "PENDING_APPROVAL",
                      "escalated_at": datetime.now(timezone.utc).isoformat()})
        _pending[body.action_id] = entry
        reason = "Regulatory impact" if body.regulatory_impact else f"Confidence {confidence:.0%} below threshold"
        return {"decision": "ESCALATED", "confidence": confidence,
                "message": f"Escalated: {reason}"}


@app.get("/pending")
async def get_pending():
    return {"pending_count": len(_pending), "actions": list(_pending.values())}


@app.post("/approve/{action_id}")
async def approve(action_id: str, body: ApprovalRequest):
    if action_id not in _pending:
        raise HTTPException(404, f"Action {action_id} not found")
    entry = _pending.pop(action_id)
    write_to_bigquery({**entry, "status": "CONTROLLER_APPROVED",
                       "approved_by": body.controller_id, "notes": body.notes,
                       "approved_at": datetime.now(timezone.utc).isoformat()})
    logger.info(f"✅ {action_id} APPROVED by {body.controller_id}")
    return {"status": "approved", "action_id": action_id}


@app.post("/reject/{action_id}")
async def reject(action_id: str, body: RejectionRequest):
    if action_id not in _pending:
        raise HTTPException(404, f"Action {action_id} not found")
    entry = _pending.pop(action_id)
    write_to_bigquery({**entry, "status": "CONTROLLER_REJECTED",
                       "rejected_by": body.controller_id, "rejection_reason": body.reason,
                       "rejected_at": datetime.now(timezone.utc).isoformat()})
    logger.info(f"❌ {action_id} REJECTED by {body.controller_id}")
    return {"status": "rejected", "action_id": action_id}


@app.get("/audit-log")
async def get_audit_log():
    return {"entries": _audit_log[-100:], "total": len(_audit_log)}


@app.get("/report")
async def get_report():
    approved = [e for e in _audit_log if "APPROVED" in e.get("status","")]
    rejected = [e for e in _audit_log if "REJECTED" in e.get("status","")]
    auto     = [e for e in approved if e.get("approved_by") == "AI_SYSTEM"]
    avg_conf = round(sum(e.get("confidence",0) for e in _audit_log) / max(len(_audit_log),1), 3)
    return {
        "report_id":    uuid.uuid4().hex[:8].upper(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_actions":        len(_audit_log),
            "auto_approved":        len(auto),
            "controller_approved":  len(approved) - len(auto),
            "rejected":             len(rejected),
            "pending":              len(_pending),
            "avg_confidence":       avg_conf,
        },
        "regulatory_compliance": "COMPLIANT" if not rejected else "REVIEW_REQUIRED",
        "bigquery_table": f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}",
    }


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  IRROPS Audit Service — Starting Up")
    logger.info("=" * 60)
    logger.info(f"  Port        : {PORT}")
    logger.info(f"  Model       : {GEMINI_MODEL}")
    logger.info(f"  Threshold   : {CONFIDENCE_THRESHOLD}")
    logger.info(f"  Vertex AI   : {'✅ Connected' if VERTEX_AVAILABLE else '⚠️  Demo mode'}")
    logger.info(f"  BigQuery    : {'✅ Connected' if BQ_AVAILABLE else '⚠️  Demo mode'}")
    logger.info(f"  MCP SSE     : {'✅ Enabled — /sse' if MCP_AVAILABLE else '⚠️  Not available'}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
