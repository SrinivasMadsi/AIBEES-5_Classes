"""
nodes/supervisor.py
───────────────────
Orchestrator — sits at root of nodes/, above nodes/agents/.
No tools bound. Reads agent_findings and decides next sub-agent.
Returns JSON: {"next": "agent_name", "instruction": "..."} or FINISH.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from graph.state import PatientHistoryState
from core.prompts import SUPERVISOR_PROMPT
from utils.llm import get_llm
from config import FINISH_SIGNAL


def supervisor_node(state: PatientHistoryState) -> dict:
    print("\n[supervisor]")

    messages        = state["messages"]
    agent_findings  = state.get("agent_findings", {})
    iteration_count = state.get("iteration_count", 0)
    patient_name    = state.get("patient_name", "the patient")

    findings_context = ""
    if agent_findings:
        findings_context = "\n\nSUB-AGENT FINDINGS SO FAR:\n"
        for agent, findings in agent_findings.items():
            findings_context += f"\n--- {agent.upper()} ---\n{findings}\n"

    system          = SystemMessage(content=SUPERVISOR_PROMPT)
    decision_prompt = HumanMessage(
        content=findings_context + f"\nDecide the next action for patient: {patient_name}."
        if agent_findings else
        f"Begin patient history analysis for: {patient_name}. Start with retriever."
    )

    response = get_llm().invoke([system] + list(messages) + [decision_prompt])

    try:
        raw      = response.content.strip().lstrip("```json").rstrip("```").strip()
        decision = json.loads(raw)
        next_agent  = decision.get("next", FINISH_SIGNAL)
        instruction = decision.get("instruction", "")
        summary     = decision.get("summary", "")
    except (json.JSONDecodeError, AttributeError):
        next_agent  = FINISH_SIGNAL
        summary     = response.content
        instruction = ""

    print(f"  Supervisor → {next_agent}")

    if next_agent == FINISH_SIGNAL:
        final = summary or response.content
        print("  [FINISH] Patient summary produced.")
        return {
            "messages":        [AIMessage(content=f"PATIENT SUMMARY:\n{final}")],
            "next_agent":      FINISH_SIGNAL,
            "iteration_count": iteration_count + 1,
        }

    return {
        "messages":        [HumanMessage(content=instruction or f"Analyse records for {patient_name}.")],
        "next_agent":      next_agent,
        "iteration_count": iteration_count + 1,
    }
