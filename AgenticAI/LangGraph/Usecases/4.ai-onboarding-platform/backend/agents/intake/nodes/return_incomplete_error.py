"""
agents/intake/nodes/return_incomplete_error.py
Node: return_incomplete_error

Fast-fail node — runs when check_completeness finds missing required fields.
Marks the submission as needing the IPM to add missing data.
"""
from graph.state import MainState


def return_incomplete_error_node(state: MainState) -> dict:
    """Set state so the orchestrator routes to early-exit finalize."""
    check = state.get("completeness_check", {})
    missing = check.get("missing_required", [])

    print(f"[intake.return_incomplete_error] ❌ {len(missing)} required field(s) missing — halting")

    return {
        "final_status": "rejected",
        "verdict": "INCOMPLETE",
        "critic_summary": (
            f"Submission rejected: {len(missing)} required field(s) missing. "
            "IPM must complete the form before validation can proceed."
        ),
        "error": "incomplete_submission",
    }
