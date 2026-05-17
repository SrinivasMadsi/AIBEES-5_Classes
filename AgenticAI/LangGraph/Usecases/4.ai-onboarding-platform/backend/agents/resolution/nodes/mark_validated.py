"""
agents/resolution/nodes/mark_validated.py
Node: mark_validated

Terminal-leaf node in the Resolution subgraph for the happy path —
all checks passed (or only warnings remained).
"""
from graph.state import MainState


def mark_validated_node(state: MainState) -> dict:
    """Mark the submission as fully validated."""
    iter_count = state.get("iteration_count", 0)
    auto_fixed = iter_count > 0
    status = "validated_with_fixes" if auto_fixed else "validated_pass"

    print(f"[resolution.mark_validated] ✅ final_status={status}")

    return {"final_status": status}
