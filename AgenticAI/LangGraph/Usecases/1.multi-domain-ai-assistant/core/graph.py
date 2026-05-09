"""
core/graph.py
LangGraph graph builder — wires all nodes and edges together.

This is the ONLY place that knows about the full graph topology.
Individual agents, supervisor, and merger don't know about each other —
they only know about state. The graph wires them together.

Graph structure:
  START → supervisor → [conditional] → domain_agents → merger → END
"""

from langgraph.graph import StateGraph, START, END
from core.state import AgentState
from core.supervisor import supervisor_node, route_to_domain
from core.merger import merger_node
from agents.licensing.agent import licensing_agent_node
from agents.onprem.agent import onprem_agent_node
from agents.kb.agent import kb_agent_node


def build_graph():
    """
    Builds and compiles the full multi-agent LangGraph.

    Adding a new domain = add one node + one edge here.
    No other files need to change.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("supervisor",       supervisor_node)
    graph.add_node("licensing_agent",  licensing_agent_node)
    graph.add_node("onprem_agent",     onprem_agent_node)
    graph.add_node("kb_agent",         kb_agent_node)
    graph.add_node("merger",           merger_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.add_edge(START, "supervisor")

    # ── Conditional routing (supervisor → domain agents) ──────────────────────
    graph.add_conditional_edges(
        "supervisor",
        route_to_domain,
        {
            "licensing_agent": "licensing_agent",
            "onprem_agent":    "onprem_agent",
            "kb_agent":        "kb_agent",
        }
    )

    # ── All domain agents feed into merger ────────────────────────────────────
    graph.add_edge("licensing_agent", "merger")
    graph.add_edge("onprem_agent",    "merger")
    graph.add_edge("kb_agent",        "merger")

    # ── Merger leads to END ───────────────────────────────────────────────────
    graph.add_edge("merger", END)

    return graph.compile()
