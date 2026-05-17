"""
agents/validation/graph.py
Builds the Validation Agent as a LangGraph subgraph.

Flow:
  fetch_sops_via_mcp → apply_rules_to_answers → collect_findings

This is the agent that demonstrates MCP — fetch_sops_via_mcp talks to
the sop-mcp server (a separate process) via the Model Context Protocol.
"""
from langgraph.graph import END, START, StateGraph

from agents.validation.nodes import (
    apply_rules_to_answers_node,
    collect_findings_node,
    fetch_sops_via_mcp_node,
)
from graph.state import MainState


def build_validation_agent():
    """Build and compile the Validation Agent subgraph."""
    g = StateGraph(MainState)

    g.add_node("fetch_sops_via_mcp", fetch_sops_via_mcp_node)
    g.add_node("apply_rules_to_answers", apply_rules_to_answers_node)
    g.add_node("collect_findings", collect_findings_node)

    g.add_edge(START, "fetch_sops_via_mcp")
    g.add_edge("fetch_sops_via_mcp", "apply_rules_to_answers")
    g.add_edge("apply_rules_to_answers", "collect_findings")
    g.add_edge("collect_findings", END)

    return g.compile()
