"""
agents/resolution/graph.py
Builds the Resolution Agent as a LangGraph subgraph.

Flow:
  categorize_findings → generate_fix_suggestions → review_suggestions
                                                        ↓
                            ┌───────────────────────────┴───────────────┐
                       PASS │                       FAIL_FIXABLE │  FAIL_REJECT
                       mark_validated         apply_auto_fixes        escalate_to_BOM
"""
from langgraph.graph import END, START, StateGraph

from agents.resolution.nodes import (
    apply_auto_fixes_node,
    categorize_findings_node,
    escalate_to_BOM_node,
    generate_fix_suggestions_node,
    mark_validated_node,
    review_suggestions_node,
)
from graph.state import MainState


def _route_after_review(state: MainState) -> str:
    """Branch based on critic's verdict."""
    verdict = state.get("verdict", "")
    if verdict == "PASS":
        return "mark_validated"
    if verdict == "FAIL_REJECT":
        return "escalate_to_BOM"
    # FAIL_FIXABLE or anything else
    return "apply_auto_fixes"


def build_resolution_agent():
    """Build and compile the Resolution Agent subgraph."""
    g = StateGraph(MainState)

    g.add_node("categorize_findings", categorize_findings_node)
    g.add_node("generate_fix_suggestions", generate_fix_suggestions_node)
    g.add_node("review_suggestions", review_suggestions_node)
    g.add_node("apply_auto_fixes", apply_auto_fixes_node)
    g.add_node("mark_validated", mark_validated_node)
    g.add_node("escalate_to_BOM", escalate_to_BOM_node)

    g.add_edge(START, "categorize_findings")
    g.add_edge("categorize_findings", "generate_fix_suggestions")
    g.add_edge("generate_fix_suggestions", "review_suggestions")

    g.add_conditional_edges(
        "review_suggestions",
        _route_after_review,
        {
            "mark_validated":   "mark_validated",
            "apply_auto_fixes": "apply_auto_fixes",
            "escalate_to_BOM":  "escalate_to_BOM",
        },
    )

    g.add_edge("mark_validated", END)
    g.add_edge("apply_auto_fixes", END)
    g.add_edge("escalate_to_BOM", END)

    return g.compile()
