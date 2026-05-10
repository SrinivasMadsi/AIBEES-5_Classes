"""
nodes/agents/analyser.py — Sub-agent: analyser_node
Identifies trends in lab results and medication history. Uses ANALYSER_TOOLS.
"""

from langchain_core.messages import AIMessage
from graph.state import PatientHistoryState
from core.tools import ANALYSER_TOOLS
from nodes.agents.retriever import _run_sub_agent


def analyser_node(state: PatientHistoryState) -> dict:
    print("\n[analyser]")
    findings = _run_sub_agent(state, "analyser", ANALYSER_TOOLS)
    existing = state.get("agent_findings", {})
    existing_ctx = state.get("retrieved_context", "")
    return {
        "agent_findings":   {**existing, "analyser": findings},
        "retrieved_context": existing_ctx + "\n\n" + findings,
        "messages":         [AIMessage(content=f"[analyser] {findings[:200]}...")],
    }
