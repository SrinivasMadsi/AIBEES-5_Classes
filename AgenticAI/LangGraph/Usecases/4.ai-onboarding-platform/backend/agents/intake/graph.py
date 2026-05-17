"""
agents/intake/graph.py
Builds the Intake Agent as a LangGraph subgraph.

Flow:
  parse_submission → check_completeness → [conditional]
                                          ├── missing required → return_incomplete_error
                                          └── all required filled → classify_plan_type
                                                                    → detect_risk_signals
                                                                    → group_by_domain
"""
from langgraph.graph import END, START, StateGraph

from agents.intake.nodes import (
    check_completeness_node,
    classify_plan_type_node,
    detect_risk_signals_node,
    group_by_domain_node,
    parse_submission_node,
    return_incomplete_error_node,
)
from graph.state import MainState


def _route_after_completeness(state: MainState) -> str:
    """Branch based on whether all required fields are filled."""
    if state.get("is_complete", False):
        return "classify_plan_type"
    return "return_incomplete_error"


def build_intake_agent():
    """Build and compile the Intake Agent subgraph."""
    g = StateGraph(MainState)

    g.add_node("parse_submission", parse_submission_node)
    g.add_node("check_completeness", check_completeness_node)
    g.add_node("classify_plan_type", classify_plan_type_node)
    g.add_node("detect_risk_signals", detect_risk_signals_node)
    g.add_node("group_by_domain", group_by_domain_node)
    g.add_node("return_incomplete_error", return_incomplete_error_node)

    g.add_edge(START, "parse_submission")
    g.add_edge("parse_submission", "check_completeness")

    g.add_conditional_edges(
        "check_completeness",
        _route_after_completeness,
        {
            "classify_plan_type": "classify_plan_type",
            "return_incomplete_error": "return_incomplete_error",
        },
    )

    g.add_edge("classify_plan_type", "detect_risk_signals")
    g.add_edge("detect_risk_signals", "group_by_domain")
    g.add_edge("group_by_domain", END)
    g.add_edge("return_incomplete_error", END)

    return g.compile()
