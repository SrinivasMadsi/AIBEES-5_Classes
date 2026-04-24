"""
╔══════════════════════════════════════════════════════════════╗
║  SERVICE 2 — Resolution Agent MCP Server                     ║
║  Port: 8081                                                  ║
║                                                              ║
║  Architecture:                                               ║
║  MCP Client → /sse → Orchestrator (Gemini 2.5 Pro)          ║
║       → decompose_irrops() → resolution DAG                 ║
║       → FLIGHT_AGENT tools (rebook, cancel, notify)         ║
║       → CREW_AGENT tools (fdp, find_crew, reassign)         ║
║       → OPS_AGENT tools (gate, aircraft, aodb)              ║
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

# ── Vertex AI ─────────────────────────────────────────────────────────────────
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
logger = logging.getLogger("resolution-agent")

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID   = os.getenv("GCP_PROJECT_ID", "your-project-id")
LOCATION     = os.getenv("GCP_LOCATION",   "us-central1")
PORT         = int(os.getenv("PORT",        "8081"))
GEMINI_MODEL = os.getenv("GEMINI_MODEL",    "gemini-2.5-pro-preview-03-25")

# ── Init Vertex AI ────────────────────────────────────────────────────────────
if VERTEX_AVAILABLE:
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        logger.info(f"✅ Vertex AI initialized — project={PROJECT_ID} model={GEMINI_MODEL}")
    except Exception as e:
        logger.warning(f"⚠️  Vertex AI init failed (demo mode): {e}")
        VERTEX_AVAILABLE = False

# ── In-memory task store ──────────────────────────────────────────────────────
_tasks: dict[str, dict] = {}


# ══════════════════════════════════════════════════════════════════════════════
# SPECIALIST AGENT TOOL IMPLEMENTATIONS
# In production: each function makes a real API call to enterprise systems
# (Amadeus, Jeppesen, FIDS, AODB, etc.)
# In demo: returns realistic simulated responses
# ══════════════════════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    # ── ORCHESTRATOR ──────────────────────────────────────────────────────────
    "ORCHESTRATOR": {
        "decompose_irrops": lambda f: {
            "status": "SUCCESS", "sub_tasks": 5,
            "dag_created": True, "flight": f
        },
        "delegate_to_agent": lambda f: {
            "status": "SUCCESS", "delegated": True, "flight": f
        },
        "assess_confidence": lambda f: {
            "status": "SUCCESS",
            "confidence": round(random.uniform(0.75, 0.98), 2)
        },
    },

    # ── FLIGHT AGENT ──────────────────────────────────────────────────────────
    # Production: calls Amadeus GDS / Sabre / DCS
    "FLIGHT_AGENT": {
        "rebook_passengers": lambda f: {
            "status":      "SUCCESS",
            "pax_rebooked": random.randint(80, 180),
            "next_flight":  f"{f.split('-')[0]}-{int(f.split('-')[-1]) + 1}",
            "cost_usd":     random.randint(10000, 25000),
            "api":          "Amadeus GDS [SIMULATED]",
        },
        "cancel_flight": lambda f: {
            "status":               "SUCCESS",
            "flight_cancelled":     True,
            "accommodation_arranged": True,
            "vouchers_issued":      random.randint(100, 200),
            "api":                  "DCS API [SIMULATED]",
        },
        "find_alternate_routing": lambda f: {
            "status":          "SUCCESS",
            "alternate_routes": ["via ORD +2h", "via DFW +3h"],
            "earliest_arrival": f"+{random.randint(2, 5)}h",
            "api":              "GDS API [SIMULATED]",
        },
        "notify_passengers": lambda f: {
            "status":        "SUCCESS",
            "channels":      ["SMS", "EMAIL", "APP_PUSH"],
            "notified":      random.randint(100, 180),
            "delivery_rate": round(random.uniform(0.94, 0.99), 2),
            "api":           "Twilio + SendGrid [SIMULATED]",
        },
    },

    # ── CREW AGENT ────────────────────────────────────────────────────────────
    # Production: calls Jeppesen / AIMS / Sabre CrewTrac
    "CREW_AGENT": {
        "check_fdp_limits": lambda f: {
            "status":            "SUCCESS",
            "max_fdp_hours":     9.0,
            "used_fdp_hours":    round(random.uniform(4.0, 7.0), 1),
            "fdp_remaining":     round(random.uniform(2.0, 5.0), 1),
            "rest_compliant":    True,
            "regulatory_body":   "FAA Part 117",
            "api":               "Jeppesen CrewPlan [SIMULATED]",
        },
        "check_crew_legality": lambda f: {
            "status":          "SUCCESS",
            "legal_to_fly":    True,
            "rest_hours_taken": round(random.uniform(10, 14), 1),
            "regulatory_body": "FAA Part 117",
            "api":             "Jeppesen CrewPlan [SIMULATED]",
        },
        "find_available_crew": lambda f: {
            "status":        "SUCCESS",
            "crew_found":    True,
            "captain":       f"CAP-{random.randint(1000, 9999)}",
            "first_officer": f"FO-{random.randint(1000, 9999)}",
            "base":          random.choice(["ORD", "JFK", "DFW", "ATL", "LAX"]),
            "eta_minutes":   random.randint(30, 90),
            "api":           "Sabre CrewTrac [SIMULATED]",
        },
        "reassign_crew": lambda f: {
            "status":          "SUCCESS",
            "crew_assigned":   True,
            "briefing_time":   "T-90min",
            "hotel_released":  True,
            "confirmation_id": f"CRW-{random.randint(10000, 99999)}",
            "api":             "Sabre CrewTrac [SIMULATED]",
        },
    },

    # ── OPS AGENT ─────────────────────────────────────────────────────────────
    # Production: calls Airport FIDS / Fleet Management / AODB / ACARS
    "OPS_AGENT": {
        "swap_gate": lambda f: {
            "status":               "SUCCESS",
            "old_gate":             f"B{random.randint(1, 20)}",
            "new_gate":             f"C{random.randint(1, 20)}",
            "ground_crew_notified": True,
            "fids_updated":         True,
            "api":                  "Airport FIDS API [SIMULATED]",
        },
        "substitute_aircraft": lambda f: {
            "status":      "SUCCESS",
            "original":    "B737-800",
            "substitute":  "B737-MAX8",
            "tail_number": f"N{random.randint(10000, 99999)}",
            "ready_time":  "T-60min",
            "api":         "Fleet Management API [SIMULATED]",
        },
        "update_aodb": lambda f: {
            "status":             "SUCCESS",
            "aodb_updated":       True,
            "acars_sent":         True,
            "downstream_systems": ["DCS", "RES", "OPS", "FIDS"],
            "api":                "AODB + ACARS API [SIMULATED]",
        },
        "coordinate_ground_ops": lambda f: {
            "status":             "SUCCESS",
            "fueling_scheduled":  True,
            "catering_updated":   True,
            "jetbridge_assigned": f"C{random.randint(1, 20)}-JB{random.randint(1, 4)}",
            "api":                "Ground Handling API [SIMULATED]",
        },
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# AI LAYER — Orchestrator using Gemini 2.5 Pro
# ══════════════════════════════════════════════════════════════════════════════

def _mock_plan(event: dict) -> dict:
    """Fallback resolution plan when Vertex AI is unavailable."""
    severity = event.get("severity", "MEDIUM")
    return {
        "task_id": f"TASK-{uuid.uuid4().hex[:8].upper()}",
        "resolution_steps": [
            {"agent": "ORCHESTRATOR", "tool": "decompose_irrops",    "rationale": "Decompose IRROPS into actionable sub-tasks with dependencies",  "priority": 0},
            {"agent": "CREW_AGENT",   "tool": "check_fdp_limits",    "rationale": "Verify crew FDP legality BEFORE any reassignment (FAA Part 117)", "priority": 1},
            {"agent": "CREW_AGENT",   "tool": "find_available_crew", "rationale": "Source replacement crew from reserve pool at nearest base",       "priority": 2},
            {"agent": "FLIGHT_AGENT", "tool": "rebook_passengers",   "rationale": "Reaccommodate all affected passengers on next available service", "priority": 3},
            {"agent": "OPS_AGENT",    "tool": "update_aodb",         "rationale": "Update AODB and dispatch ACARS message to downstream systems",    "priority": 4},
            {"agent": "FLIGHT_AGENT", "tool": "notify_passengers",   "rationale": "Notify all passengers via SMS, email, and app push",              "priority": 5},
        ],
        "estimated_resolution_time_min": {"LOW":15,"MEDIUM":30,"HIGH":60,"CRITICAL":90}.get(severity, 45),
        "confidence_score":              {"LOW":0.95,"MEDIUM":0.85,"HIGH":0.75,"CRITICAL":0.65}.get(severity, 0.8),
        "requires_human_approval":       severity == "CRITICAL",
        "source":                        "mock",
    }


async def orchestrate_with_gemini(event: dict) -> dict:
    """
    Send the IRROPS event to Vertex AI Gemini 2.5 Pro for intelligent orchestration.

    This is WHERE THE REASONING HAPPENS. Gemini reads the event context and decides:
    - Which specialist agents to involve
    - Which specific tools to call
    - The correct execution order (respecting regulatory dependencies like FDP checks)
    - Estimated resolution time and confidence

    Notice: Gemini knows to check FDP limits BEFORE crew reassignment
    without being explicitly told — that's domain reasoning from training.
    """
    if not VERTEX_AVAILABLE:
        logger.info("Using mock orchestration plan (Vertex AI unavailable)")
        return _mock_plan(event)
    try:
        model  = GenerativeModel(GEMINI_MODEL)
        prompt = f"""
You are a senior airline operations AI orchestrating IRROPS resolution.

An irregular operation has been detected. Create a detailed multi-agent resolution plan.

Event Details:
{json.dumps(event, indent=2)}

Available specialist agents and their tools:
- ORCHESTRATOR: [decompose_irrops, delegate_to_agent, assess_confidence]
- FLIGHT_AGENT: [rebook_passengers, cancel_flight, find_alternate_routing, notify_passengers]
- CREW_AGENT:   [check_fdp_limits, check_crew_legality, find_available_crew, reassign_crew]
- OPS_AGENT:    [swap_gate, substitute_aircraft, update_aodb, coordinate_ground_ops]

IMPORTANT RULES:
1. Always verify FDP limits BEFORE crew reassignment (FAA Part 117 requirement)
2. Always notify passengers LAST, after all operational steps are complete
3. For CRITICAL severity, set requires_human_approval to true
4. Keep resolution_steps ordered by priority (0 = first to execute)

Return ONLY valid JSON:
{{
  "task_id": "TASK-XXXXXXXX",
  "resolution_steps": [
    {{"agent": "AGENT_NAME", "tool": "tool_name", "rationale": "why this step is needed", "priority": 0}}
  ],
  "estimated_resolution_time_min": 45,
  "confidence_score": 0.85,
  "requires_human_approval": false,
  "source": "gemini"
}}
"""
        response = await asyncio.to_thread(model.generate_content, prompt)
        text     = response.text.strip().strip("```json").strip("```").strip()
        plan     = json.loads(text)
        logger.info(
            f"🧠 Gemini created plan {plan.get('task_id')} — "
            f"{len(plan.get('resolution_steps', []))} steps, "
            f"confidence={plan.get('confidence_score', 0):.0%}"
        )
        return plan
    except Exception as e:
        logger.warning(f"Gemini orchestration failed: {e} — using mock plan")
        return _mock_plan(event)


# ══════════════════════════════════════════════════════════════════════════════
# MCP SERVER — Tool definitions and handlers
# ══════════════════════════════════════════════════════════════════════════════

mcp = Server("irrops-resolution-agent") if MCP_AVAILABLE else None


if MCP_AVAILABLE and mcp:

    @mcp.list_tools()
    async def list_tools() -> list[Tool]:
        """
        Expose all orchestrator + specialist agent tools to MCP Clients.
        The Orchestrator reads these to understand the full capability set.
        """
        tools = []

        # ── Orchestrator tool ─────────────────────────────────────────────────
        tools.append(Tool(
            name="decompose_irrops",
            description=(
                "PRIMARY ORCHESTRATION TOOL. Send an IRROPS event to Vertex AI Gemini 2.5 Pro "
                "to create a multi-agent resolution plan. Gemini determines which specialist "
                "agents to involve, which tools to call, and the correct execution order "
                "respecting regulatory dependencies (e.g. FDP checks before crew reassignment)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id":    {"type": "string"},
                    "flight":      {"type": "string"},
                    "irrops_type": {"type": "string"},
                    "severity":    {"type": "string", "enum": ["LOW","MEDIUM","HIGH","CRITICAL"]},
                },
                "required": ["event_id", "flight", "irrops_type", "severity"],
            },
        ))

        # ── Specialist agent tools ─────────────────────────────────────────────
        tool_descriptions = {
            # FLIGHT_AGENT
            "FLIGHT_AGENT_rebook_passengers":     "Reaccommodate affected passengers on next available flight. Calls airline reservation system.",
            "FLIGHT_AGENT_cancel_flight":         "Cancel the flight and arrange hotel accommodation + issue vouchers.",
            "FLIGHT_AGENT_find_alternate_routing":"Find alternate routing options for affected passengers.",
            "FLIGHT_AGENT_notify_passengers":     "Notify all affected passengers via SMS, email, and app push notifications.",
            # CREW_AGENT
            "CREW_AGENT_check_fdp_limits":        "Check crew Flight Duty Period limits per FAA Part 117. MUST be called before any crew reassignment.",
            "CREW_AGENT_check_crew_legality":     "Full regulatory legality check for crew assignment including rest requirements.",
            "CREW_AGENT_find_available_crew":     "Search reserve crew pool at the nearest base for qualified replacement crew.",
            "CREW_AGENT_reassign_crew":           "Assign replacement crew to the disrupted flight and release hotel hold.",
            # OPS_AGENT
            "OPS_AGENT_swap_gate":               "Reassign departure gate and update FIDS. Notifies ground crew automatically.",
            "OPS_AGENT_substitute_aircraft":      "Swap aircraft tail number. Coordinates maintenance and ground handling.",
            "OPS_AGENT_update_aodb":              "Update Airport Operations Database and send ACARS message to downstream systems.",
            "OPS_AGENT_coordinate_ground_ops":    "Schedule fueling, update catering, and assign jetbridge for the disrupted flight.",
        }

        for key, description in tool_descriptions.items():
            agent, tool_name = key.split("_", 1)
            tools.append(Tool(
                name=f"{agent}_{tool_name}",
                description=description,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string"},
                        "flight":   {"type": "string"},
                        "params":   {"type": "object", "description": "Optional additional parameters"},
                    },
                    "required": ["event_id", "flight"],
                },
            ))

        return tools

    @mcp.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Route MCP tool calls to the appropriate agent implementation."""
        logger.info(f"🔧 MCP tool call: {name} — flight={arguments.get('flight','?')}")

        # ── Orchestrator: decompose_irrops ─────────────────────────────────────
        if name == "decompose_irrops":
            plan = await orchestrate_with_gemini({
                "event_id":    arguments["event_id"],
                "flight":      arguments["flight"],
                "irrops_type": arguments.get("irrops_type", "DELAY"),
                "severity":    arguments.get("severity", "HIGH"),
            })
            plan.update({
                "event_id":   arguments["event_id"],
                "flight":     arguments["flight"],
                "status":     "RESOLVING",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            for step in plan.get("resolution_steps", []):
                step["status"] = "PENDING"
            _tasks[plan["task_id"]] = plan
            return [TextContent(type="text", text=json.dumps(plan, indent=2))]

        # ── Specialist agent tool dispatch ─────────────────────────────────────
        for agent_name in TOOL_REGISTRY:
            prefix = f"{agent_name}_"
            if name.startswith(prefix):
                tool_name = name[len(prefix):]
                tool_fn   = TOOL_REGISTRY[agent_name].get(tool_name)

                if not tool_fn:
                    return [TextContent(type="text", text=json.dumps({
                        "error": f"Unknown tool: {tool_name} for agent {agent_name}"
                    }))]

                await asyncio.sleep(random.uniform(0.2, 0.8))  # realistic latency
                result = tool_fn(arguments.get("flight", "UNKNOWN"))
                logger.info(f"✅ {agent_name}.{tool_name}() → {result.get('status')}")

                return [TextContent(type="text", text=json.dumps({
                    "agent":       agent_name,
                    "tool":        tool_name,
                    "event_id":    arguments.get("event_id"),
                    "flight":      arguments.get("flight"),
                    "result":      result,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                }, indent=2))]

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="IRROPS Resolution Agent",
    description="MCP Server with Orchestrator + Specialist Agents for IRROPS resolution",
    version="3.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/sse")
async def mcp_sse(request: Request):
    """MCP SSE endpoint — ADK Orchestrator connects here."""
    if not MCP_AVAILABLE or not mcp:
        return {"error": "MCP SDK not available"}
    transport = SseServerTransport("/mcp/messages")
    async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())


@app.post("/mcp/messages")
async def mcp_messages(request: Request):
    """MCP messages endpoint — handles tool call requests."""
    if not MCP_AVAILABLE or not mcp:
        return {"error": "MCP SDK not available"}
    transport = SseServerTransport("/mcp/messages")
    await transport.handle_post_message(request.scope, request.receive, request._send)


@app.get("/health")
async def health():
    return {
        "status":      "ok",
        "service":     "resolution-agent",
        "version":     "3.0.0",
        "mcp_available": MCP_AVAILABLE,
        "mcp_endpoint": "/sse",
        "vertex_ai":   VERTEX_AVAILABLE,
        "model":       GEMINI_MODEL,
        "agents":      list(TOOL_REGISTRY.keys()),
        "tasks":       len(_tasks),
    }


class DecomposeRequest(BaseModel):
    event_id:    str
    flight:      str
    irrops_type: str = "DELAY"
    severity:    str = "HIGH"


class ExecuteRequest(BaseModel):
    agent:    str
    tool:     str
    event_id: str
    flight:   str


@app.post("/decompose")
async def decompose(body: DecomposeRequest):
    """REST: Decompose IRROPS event into resolution plan (called by React UI)."""
    logger.info(f"REST /decompose — flight={body.flight} type={body.irrops_type} severity={body.severity}")
    plan = await orchestrate_with_gemini(body.model_dump())
    plan.update({
        "event_id":   body.event_id,
        "flight":     body.flight,
        "status":     "RESOLVING",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    for step in plan.get("resolution_steps", []):
        step["status"] = "PENDING"
    _tasks[plan["task_id"]] = plan
    return plan


@app.post("/execute")
async def execute(body: ExecuteRequest):
    """REST: Execute a single agent tool call (called by React UI)."""
    agent   = body.agent.upper()
    tool_fn = TOOL_REGISTRY.get(agent, {}).get(body.tool)
    if not tool_fn:
        raise HTTPException(400, f"Unknown: {agent}.{body.tool}")
    logger.info(f"REST /execute — {agent}.{body.tool}() for {body.flight}")
    await asyncio.sleep(random.uniform(0.3, 1.0))
    result = tool_fn(body.flight)
    return {"agent": agent, "tool": body.tool, "event_id": body.event_id,
            "flight": body.flight, "result": result,
            "executed_at": datetime.now(timezone.utc).isoformat()}


@app.get("/tasks")
async def get_tasks():
    return {"tasks": list(_tasks.values()), "total": len(_tasks)}


@app.get("/agents")
async def get_agents():
    return {"agents": {a: list(t.keys()) for a, t in TOOL_REGISTRY.items()}}


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  IRROPS Resolution Agent — Starting Up")
    logger.info("=" * 60)
    logger.info(f"  Port       : {PORT}")
    logger.info(f"  Model      : {GEMINI_MODEL}")
    logger.info(f"  Vertex AI  : {'✅ Connected' if VERTEX_AVAILABLE else '⚠️  Demo mode'}")
    logger.info(f"  MCP SSE    : {'✅ Enabled — /sse' if MCP_AVAILABLE else '⚠️  Not available'}")
    logger.info(f"  Agents     : {list(TOOL_REGISTRY.keys())}")
    logger.info("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
