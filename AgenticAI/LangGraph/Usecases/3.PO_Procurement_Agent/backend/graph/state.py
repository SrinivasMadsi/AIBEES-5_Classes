"""
graph/state.py
The shared state passed between all nodes in the graph.
Each node reads what it needs and returns a partial dict to merge.
"""
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class POState(TypedDict, total=False):
    """
    State for the Purchase Order agent graph.

    Composer nodes populate the early fields; Auditor nodes read them
    and populate findings; self-correction reads patches and updates
    the relevant fields, then loops back into Composer.
    """

    # ── Conversation ─────────────────────────────────────────────────────────
    messages: Annotated[list[BaseMessage], add_messages]
    user_request: str

    # ── Composer outputs ─────────────────────────────────────────────────────
    parsed_intake: dict           # {requester, delivery_location, budget_code, items[]}
    enriched_items: list[dict]    # [{sku, name, category, quantity, unit_price, vendor_id}]
    selected_vendors: dict        # {sku: vendor_info}
    tax_breakdown: dict           # {region, gst_amount, breakdown[]}
    draft_po: dict                # the full PO JSON

    # ── Auditor outputs ──────────────────────────────────────────────────────
    findings: list[dict]          # [{check_name, status, finding, suggested_fix}]
    verdict: str                  # PASS | PASS_WITH_WARNINGS | FAIL_FIXABLE | FAIL_REJECT
    critic_summary: str
    patches: list[dict]           # patches to apply if verdict == FAIL_FIXABLE

    # ── Control flow ─────────────────────────────────────────────────────────
    iteration_count: int          # increments each time self-correction loops
    max_iterations: int

    # ── Final output ─────────────────────────────────────────────────────────
    final_po: dict | None
    final_status: str             # submitted | rejected | needs_human


def initial_state(user_request: str, max_iterations: int = 1) -> POState:
    """Build a fresh state dict for a new PO request."""
    return {
        "messages": [],
        "user_request": user_request,
        "parsed_intake": {},
        "enriched_items": [],
        "selected_vendors": {},
        "tax_breakdown": {},
        "draft_po": {},
        "findings": [],
        "verdict": "",
        "critic_summary": "",
        "patches": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "final_po": None,
        "final_status": "",
    }
