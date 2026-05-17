"""
agents/resolution/nodes/escalate_to_BOM.py
Node: escalate_to_BOM

Creates human_reviews entries for each rejected finding and marks the
submission as pending_human_review. The graph will pause here (HITL
breakpoint) and resume only when the BOM analyst submits a decision.
"""
from core.db import get_session
from graph.state import MainState
from sqlalchemy import text as sql_text


def escalate_to_BOM_node(state: MainState) -> dict:
    """Insert human_reviews rows and mark for HITL pause."""
    buckets = state.get("finding_categories", {})
    rejects = buckets.get("reject", [])
    submission_id = state.get("submission_id", "")

    review_items = []

    if rejects:
        with get_session() as session:
            for finding in rejects:
                # Insert into human_reviews table
                result = session.execute(
                    sql_text("""
                        INSERT INTO business_data.human_reviews
                            (submission_id, rule_id, affected_field, issue_description, agent_recommendation)
                        VALUES (:sub, :rule, :field, :issue, :rec)
                        RETURNING id
                    """),
                    {
                        "sub":   submission_id,
                        "rule":  finding.get("rule_id"),
                        "field": str(finding.get("affected_field")),
                        "issue": finding.get("message", ""),
                        "rec":   f"Reject due to {finding.get('severity')} severity. SOP rule violation.",
                    },
                )
                review_id = result.scalar()
                review_items.append({
                    "review_id":         review_id,
                    "rule_id":           finding.get("rule_id"),
                    "rule_name":         finding.get("rule_name"),
                    "affected_field":    finding.get("affected_field"),
                    "issue_description": finding.get("message"),
                    "current_value":     finding.get("current_value"),
                })

    print(f"[resolution.escalate_to_BOM] 🛑 created {len(review_items)} human review(s) — graph will pause")

    return {
        "human_review_items": review_items,
        "final_status":       "pending_human_review",
    }
