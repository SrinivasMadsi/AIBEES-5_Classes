"""
nodes/agents/summariser.py — Sub-agent: summariser_node
Produces structured summary sections from retrieved records. Uses SUMMARISER_TOOLS.
"""

from langchain_core.messages import AIMessage
from graph.state import PatientHistoryState
from core.tools import SUMMARISER_TOOLS
from nodes.agents.retriever import _run_sub_agent


def summariser_node(state: PatientHistoryState) -> dict:
    print("\n[summariser]")
    findings = _run_sub_agent(state, "summariser", SUMMARISER_TOOLS)
    existing = state.get("agent_findings", {})
    return {
        "agent_findings": {**existing, "summariser": findings},
        "messages":       [AIMessage(content=f"[summariser] {findings[:200]}...")],
    }
