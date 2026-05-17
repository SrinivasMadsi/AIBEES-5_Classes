"""
api/routes_review.py
HITL — BOM analyst review queue + decision endpoints.
"""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text as sql_text

from core.db import get_session

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


class ReviewDecisionRequest(BaseModel):
    reviewed_by: str
    decision: str       # 'approve' | 'reject' | 'override'
    comment: str = ""


@router.get("")
def list_pending_reviews():
    """Get all reviews in the BOM analyst queue."""
    with get_session() as session:
        rows = session.execute(
            sql_text("""
                SELECT hr.id, hr.submission_id, hr.rule_id, hr.affected_field,
                       hr.issue_description, hr.agent_recommendation, hr.status,
                       hr.created_at,
                       s.client_name, s.form_id, s.submitted_by
                FROM business_data.human_reviews hr
                JOIN business_data.submissions s ON s.submission_id = hr.submission_id
                WHERE hr.status = 'pending'
                ORDER BY hr.created_at DESC
            """)
        ).fetchall()

    return [
        {
            "review_id":           r.id,
            "submission_id":       r.submission_id,
            "client_name":         r.client_name,
            "form_id":             r.form_id,
            "submitted_by":        r.submitted_by,
            "rule_id":             r.rule_id,
            "affected_field":      r.affected_field,
            "issue_description":   r.issue_description,
            "agent_recommendation": r.agent_recommendation,
            "status":              r.status,
            "created_at":          r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/{review_id}")
def get_review(review_id: int):
    """Get a single review with full context (the submission's answers and findings)."""
    with get_session() as session:
        review = session.execute(
            sql_text("""
                SELECT hr.id, hr.submission_id, hr.rule_id, hr.affected_field,
                       hr.issue_description, hr.agent_recommendation, hr.status,
                       hr.created_at,
                       s.client_name, s.form_id, s.submitted_by, s.answers, s.plan_type
                FROM business_data.human_reviews hr
                JOIN business_data.submissions s ON s.submission_id = hr.submission_id
                WHERE hr.id = :rid
            """),
            {"rid": review_id},
        ).first()

        if not review:
            raise HTTPException(404, f"Review {review_id} not found")

        # Also fetch the failed finding for full context
        finding = session.execute(
            sql_text("""
                SELECT rule_id, rule_name, domain, affected_field, status, severity,
                       current_value, expected_value, message, suggested_fix
                FROM business_data.findings
                WHERE submission_id = :sub AND rule_id = :rule
                LIMIT 1
            """),
            {"sub": review.submission_id, "rule": review.rule_id},
        ).first()

    return {
        "review_id":          review.id,
        "submission_id":      review.submission_id,
        "client_name":        review.client_name,
        "form_id":            review.form_id,
        "submitted_by":       review.submitted_by,
        "plan_type":          review.plan_type,
        "rule_id":            review.rule_id,
        "affected_field":     review.affected_field,
        "issue_description":  review.issue_description,
        "agent_recommendation": review.agent_recommendation,
        "status":             review.status,
        "answers":            review.answers,
        "finding": {
            "rule_id":        finding.rule_id if finding else None,
            "rule_name":      finding.rule_name if finding else None,
            "domain":         finding.domain if finding else None,
            "current_value":  finding.current_value if finding else None,
            "expected_value": finding.expected_value if finding else None,
            "message":        finding.message if finding else None,
            "suggested_fix":  finding.suggested_fix if finding else None,
        } if finding else None,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    }


@router.post("/{review_id}/decision")
def submit_decision(review_id: int, req: ReviewDecisionRequest):
    """
    BOM analyst submits a decision on a flagged finding.
    Resolves the review and, if it's the last pending review for a submission,
    updates the submission status to 'approved' or 'rejected'.
    """
    if req.decision not in ("approve", "reject", "override"):
        raise HTTPException(400, "Invalid decision; must be approve/reject/override")

    new_review_status = {
        "approve":  "approved",
        "reject":   "rejected",
        "override": "overridden",
    }[req.decision]

    with get_session() as session:
        # Update the review row
        review = session.execute(
            sql_text("""
                UPDATE business_data.human_reviews
                SET status = :st, reviewed_by = :by, decision_comment = :cmt,
                    decided_at = now()
                WHERE id = :rid
                RETURNING submission_id
            """),
            {
                "st":  new_review_status,
                "by":  req.reviewed_by,
                "cmt": req.comment,
                "rid": review_id,
            },
        ).first()

        if not review:
            raise HTTPException(404, f"Review {review_id} not found")

        submission_id = review.submission_id

        # Audit log
        session.execute(
            sql_text("""
                INSERT INTO business_data.audit_log
                    (submission_id, event_type, actor, event_data)
                VALUES (:sub, 'human_decision', :actor, CAST(:data AS jsonb))
            """),
            {
                "sub":   submission_id,
                "actor": req.reviewed_by,
                "data":  json.dumps({
                    "review_id":  review_id,
                    "decision":   req.decision,
                    "comment":    req.comment,
                }),
            },
        )

        # If no more pending reviews for this submission, set final status
        pending_left = session.execute(
            sql_text("""
                SELECT COUNT(*) FROM business_data.human_reviews
                WHERE submission_id = :sub AND status = 'pending'
            """),
            {"sub": submission_id},
        ).scalar()

        if pending_left == 0:
            # If any rejected → reject the submission; else approve
            had_reject = session.execute(
                sql_text("""
                    SELECT COUNT(*) FROM business_data.human_reviews
                    WHERE submission_id = :sub AND status = 'rejected'
                """),
                {"sub": submission_id},
            ).scalar()

            new_sub_status = "rejected" if had_reject > 0 else "approved"

            session.execute(
                sql_text("""
                    UPDATE business_data.submissions
                    SET status = :st, updated_at = now()
                    WHERE submission_id = :sub
                """),
                {"st": new_sub_status, "sub": submission_id},
            )

    return {
        "review_id":     review_id,
        "review_status": new_review_status,
        "submission_id": submission_id,
        "pending_left":  pending_left,
    }
