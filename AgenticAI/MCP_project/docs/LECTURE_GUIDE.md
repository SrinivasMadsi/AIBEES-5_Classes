# MCP Lecture Guide — Airline IRROPS Platform

Complete teaching notes for explaining MCP concepts using the IRROPS demo.

---

## 1. What is MCP?

**Model Context Protocol (MCP)** is an open standard protocol introduced by Anthropic that defines how AI models communicate with external tools, data sources, and services in a structured, stateful, and secure way.

Think of it as **USB-C for AI** — just as USB-C is a universal connector that works with any device regardless of manufacturer, MCP is a universal connector that lets any AI agent talk to any tool regardless of how it was built.

In the IRROPS platform, MCP is the nervous system — it's what allows the Orchestrator Agent to discover and call the Flight Agent, Crew Agent, and Ops Agent without any hardcoded wiring between them.

---

## 2. MCP vs Traditional Function Calling

This is the most important concept to get right.

### Traditional — Deterministic / Rule-Based
- Developer explicitly defines which function to call and when
- Logic is hardcoded: `if delay > 120 then call rebook_passengers()`
- Same input always produces same output
- System doesn't understand intent — it only matches conditions
- Adding a new tool requires code changes everywhere
- No context awareness — each function call is isolated
- Brittle — one edge case the rules didn't anticipate = system fails

### Modern AI Way — Intent-Driven with Context Awareness
- The LLM reads the tool schema and *understands* what each tool does
- No hardcoding — model reasons about which tool to call based on context
- Agent discovers tools dynamically at runtime from MCP registry
- Adding a new tool just means registering it — agent finds it automatically
- Model maintains context across multiple tool calls in a session
- Decisions are intent-driven, not rule-driven

### Concrete Example from the Demo

**Traditional:**
```python
if crew_status == "NO_SHOW" and delay > 0:
    call_find_available_crew()
    call_reassign_crew()
    call_notify_passengers()
```

**MCP + Gemini:**
> Gemini reads the IRROPS event and reasons:
> "This is a crew shortage on a critical flight. I need to check FDP limits
> first for regulatory compliance, then find available reserve crew, then
> rebook passengers, then notify them. Let me call these tools in this order."

The model figured out the sequence, the regulatory consideration, and the
passenger impact — none of that was programmed.

---

## 3. When Should You Go for MCP?

### Use MCP when:
- You have multiple tools agents need to discover and use dynamically
- Tool availability changes at runtime
- You need stateful multi-turn conversations with tool calls
- Multiple AI agents need to collaborate and share tools
- You want to build once and connect many
- You need standardised auth, logging, and schema validation
- Your enterprise has existing APIs you want AI to consume intelligently

### Stick with traditional function calling when:
- You have a simple, fixed, predictable workflow
- Latency is critical and you cannot afford LLM reasoning overhead
- The rules are 100% deterministic and will never change
- You have a single tool with a single purpose

---

## 4. The Four MCP Layers

```
┌─────────────────────────────────────────────┐
│           APPLICATION LAYER                  │
│   React UI · Ops Controller · Dashboards     │
│   What the human sees and interacts with     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              MCP CLIENT                      │
│   Orchestrator Agent (ADK + Gemini 2.5 Pro)  │
│   Sends tool requests · Maintains session    │
│   Understands tool schemas · Reasons         │
└──────────────────┬──────────────────────────┘
                   │  MCP Protocol (SSE)
┌──────────────────▼──────────────────────────┐
│               MCP HOST                       │
│   Session Manager · Tool Registry · Auth     │
│   Routes requests to correct MCP Server      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│             MCP SERVERS                      │
│  ┌─────────────┐ ┌──────────┐ ┌──────────┐  │
│  │Flight Agent │ │Crew Agent│ │Ops Agent │  │
│  │  TOOLS:     │ │  TOOLS:  │ │  TOOLS:  │  │
│  │ rebook_pax  │ │check_fdp │ │swap_gate │  │
│  │ cancel_flt  │ │find_crew │ │sub_acft  │  │
│  │ notify_pax  │ │reassign  │ │upd_aodb  │  │
│  └─────────────┘ └──────────┘ └──────────┘  │
│            ENTERPRISE CAPABILITY             │
│   BigQuery · Pub/Sub · Vertex AI · Firestore │
└─────────────────────────────────────────────┘
```

**Application Layer** — what humans interact with. Your React UI, approval screens.

**MCP Client** — the AI agent that consumes tools. The Orchestrator running ADK
with Gemini 2.5 Pro. It reads tool schemas, reasons about which tools to call,
and manages conversation state.

**MCP Host** — middleware managing sessions, routing requests, validating schemas,
and handling authentication.

**MCP Server** — where actual tools live. Each specialist agent (Flight, Crew, Ops)
is an MCP server exposing a set of tools. BigQuery and Pub/Sub sit behind these servers.

---

## 5. The 70-20-10 ROI Model

This is the business case that sells MCP to enterprise leadership.

```
100% of IRROPS Events
         │
         ▼
┌────────────────────────────────────────────┐
│  70% AUTO-RESOLVED BY AI                   │
│  High confidence · No human needed         │
│  Saves ~4 FTEs per hub per shift           │
└────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  20% HUMAN-IN-THE-LOOP                     │
│  Low confidence · Regulatory flags         │
│  Decision time: 45min → 5min               │
└────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  10% ITSM / INCIDENT QUEUE                 │
│  Novel situations · System failures        │
│  Full audit trail already captured         │
└────────────────────────────────────────────┘
```

**Business impact:**
- Average IRROPS event costs $10,000–$50,000
- Major hub handles 50–200 IRROPS events per day
- 70% auto-resolution = bulk handled with zero human delay
- 20% HITL = humans only touch hard cases with AI context already prepared
- Resolution time: 45–90 minutes → under 10 minutes per event

---

## 6. Demo Walkthrough Script

### Demo 1 — Anomaly Detection (5 min)
1. Click **Start Live Stream**
2. Show events streaming in from ACARS/crew/weather feeds
3. Point out severity classification — LOW / MEDIUM / HIGH / CRITICAL
4. Explain: *"Gemini is classifying these in real time — not rules, understanding"*
5. Discuss the MCP `scan_flight_streams` tool call schema

### Demo 2 — Multi-Agent Resolution (8 min)
1. Click **Trigger IRROPS → Resolve**
2. Show the Orchestrator creating a resolution plan using Gemini 2.5 Pro
3. Walk through each specialist agent tool call step by step
4. **Pause here and say:**
   > "Nobody told Gemini to check FDP limits before reassigning crew.
   > Nobody programmed that regulatory awareness. The model reasoned
   > that in an airline crew reassignment, regulatory compliance comes
   > before operational convenience. That's MCP."
5. Show confidence scores — high = auto, low = escalate

### Demo 3 — Audit & HITL (5 min)
1. Click **Simulate Agent Actions**
2. Show auto-approved vs escalated split
3. Approve and reject pending actions as the ops controller
4. Click **Compliance Report** — show the BigQuery audit trail
5. Explain: *"Every AI decision is logged, immutable, and regulatorily compliant"*

---

## 7. Key Teaching Moments

**On MCP discovery:**
> "The Orchestrator didn't know which agents existed at startup.
> It queried the MCP registry at runtime and discovered them.
> This is what makes the platform extensible — add a Hotels Agent
> for stranded passengers and the Orchestrator finds it automatically."

**On intent vs rules:**
> "Traditional systems fail on edge cases because nobody wrote a rule
> for that scenario. Gemini doesn't need a rule — it understands the
> situation and reasons about the best action. That's the fundamental
> shift MCP enables."

**On the audit trail:**
> "Airlines are heavily regulated. Every crew reassignment, every
> rebooking decision needs to be auditable. BigQuery gives us an
> immutable, queryable record of every AI decision with confidence
> scores, timestamps, and controller sign-offs."
