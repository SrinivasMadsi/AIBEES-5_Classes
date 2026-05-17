"""
api/routes_submissions.py
Endpoints for IPM to create and read submissions.
"""
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text as sql_text

from core.db import get_session

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


class CreateSubmissionRequest(BaseModel):
    client_id: str
    client_name: str
    form_id: int
    form_version: str = "v1.0"
    submitted_by: str
    answers: dict


@router.post("")
def create_submission(req: CreateSubmissionRequest):
    """Save a new submission (status=draft initially, then submitted)."""
    submission_id = f"sub_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{submission_id}"

    with get_session() as session:
        session.execute(
            sql_text("""
                INSERT INTO business_data.submissions
                    (submission_id, client_id, client_name, form_id, form_version,
                     submitted_by, answers, status, thread_id)
                VALUES (:sub, :cid, :cname, :fid, :fver, :sb,
                        CAST(:answers AS jsonb), 'submitted', :thread)
            """),
            {
                "sub":     submission_id,
                "cid":     req.client_id,
                "cname":   req.client_name,
                "fid":     req.form_id,
                "fver":    req.form_version,
                "sb":      req.submitted_by,
                "answers": json.dumps({"answers": req.answers}),
                "thread":  thread_id,
            },
        )

        # Audit
        session.execute(
            sql_text("""
                INSERT INTO business_data.audit_log
                    (submission_id, event_type, actor, event_data)
                VALUES (:sub, 'form_submitted', :actor, CAST(:data AS jsonb))
            """),
            {
                "sub":   submission_id,
                "actor": req.submitted_by,
                "data":  json.dumps({
                    "form_id":     req.form_id,
                    "client_id":   req.client_id,
                    "answer_count": len(req.answers),
                }),
            },
        )

    return {
        "submission_id": submission_id,
        "thread_id":     thread_id,
        "status":        "submitted",
    }


@router.get("")
def list_submissions():
    """List all submissions (most recent first)."""
    with get_session() as session:
        rows = session.execute(
            sql_text("""
                SELECT submission_id, client_id, client_name, form_id, form_version,
                       submitted_by, status, plan_type, iteration_count,
                       created_at, updated_at
                FROM business_data.submissions
                ORDER BY created_at DESC
                LIMIT 100
            """)
        ).fetchall()

    return [
        {
            "submission_id":   r.submission_id,
            "client_id":       r.client_id,
            "client_name":     r.client_name,
            "form_id":         r.form_id,
            "form_version":    r.form_version,
            "submitted_by":    r.submitted_by,
            "status":          r.status,
            "plan_type":       r.plan_type,
            "iteration_count": r.iteration_count,
            "created_at":      r.created_at.isoformat() if r.created_at else None,
            "updated_at":      r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.get("/{submission_id}")
def get_submission(submission_id: str):
    """Get a single submission with its answers and findings."""
    with get_session() as session:
        sub_row = session.execute(
            sql_text("""
                SELECT submission_id, client_id, client_name, form_id, form_version,
                       submitted_by, answers, status, plan_type, thread_id,
                       iteration_count, created_at, updated_at
                FROM business_data.submissions
                WHERE submission_id = :sub
            """),
            {"sub": submission_id},
        ).first()

        if not sub_row:
            raise HTTPException(404, f"Submission {submission_id} not found")

        findings_rows = session.execute(
            sql_text("""
                SELECT rule_id, rule_name, domain, affected_field, status, severity,
                       current_value, expected_value, message, suggested_fix, auto_applied
                FROM business_data.findings
                WHERE submission_id = :sub
                ORDER BY id
            """),
            {"sub": submission_id},
        ).fetchall()

    return {
        "submission_id":   sub_row.submission_id,
        "client_id":       sub_row.client_id,
        "client_name":     sub_row.client_name,
        "form_id":         sub_row.form_id,
        "form_version":    sub_row.form_version,
        "submitted_by":    sub_row.submitted_by,
        "answers":         sub_row.answers,
        "status":          sub_row.status,
        "plan_type":       sub_row.plan_type,
        "thread_id":       sub_row.thread_id,
        "iteration_count": sub_row.iteration_count,
        "created_at":      sub_row.created_at.isoformat() if sub_row.created_at else None,
        "updated_at":      sub_row.updated_at.isoformat() if sub_row.updated_at else None,
        "findings": [
            {
                "rule_id":        r.rule_id,
                "rule_name":      r.rule_name,
                "domain":         r.domain,
                "affected_field": r.affected_field,
                "status":         r.status,
                "severity":       r.severity,
                "current_value":  r.current_value,
                "expected_value": r.expected_value,
                "message":        r.message,
                "suggested_fix":  r.suggested_fix,
                "auto_applied":   r.auto_applied,
            }
            for r in findings_rows
        ],
    }
