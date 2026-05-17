"""
api/routes_data.py
Reference data endpoints — forms, clients, audit log.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text as sql_text

from core.db import get_session

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/forms")
def list_forms():
    """List all active forms (for IPM to choose)."""
    with get_session() as session:
        rows = session.execute(
            sql_text("""
                SELECT form_id, form_name, version
                FROM business_data.forms
                WHERE is_active = true
                ORDER BY form_id
            """)
        ).fetchall()
    return [
        {"form_id": r.form_id, "form_name": r.form_name, "version": r.version}
        for r in rows
    ]


@router.get("/forms/{form_id}")
def get_form(form_id: int):
    """Get a form's full config (sections, sub-sections, questions)."""
    with get_session() as session:
        row = session.execute(
            sql_text("""
                SELECT form_id, form_name, version, config
                FROM business_data.forms
                WHERE form_id = :fid
            """),
            {"fid": form_id},
        ).first()

    if not row:
        raise HTTPException(404, f"Form {form_id} not found")

    return {
        "form_id":   row.form_id,
        "form_name": row.form_name,
        "version":   row.version,
        "config":    row.config,
    }


@router.get("/clients")
def list_clients():
    """List enterprise clients for IPM to select."""
    with get_session() as session:
        rows = session.execute(
            sql_text("""
                SELECT client_id, name, industry, plan_year_start, is_high_risk
                FROM business_data.clients
                ORDER BY name
            """)
        ).fetchall()
    return [
        {
            "client_id":       r.client_id,
            "name":            r.name,
            "industry":        r.industry,
            "plan_year_start": r.plan_year_start.isoformat() if r.plan_year_start else None,
            "is_high_risk":    r.is_high_risk,
        }
        for r in rows
    ]


@router.get("/audit-log/{submission_id}")
def get_audit_log(submission_id: str):
    """Get audit log entries for a submission."""
    with get_session() as session:
        rows = session.execute(
            sql_text("""
                SELECT event_type, actor, event_data, created_at
                FROM business_data.audit_log
                WHERE submission_id = :sub
                ORDER BY created_at
            """),
            {"sub": submission_id},
        ).fetchall()

    return [
        {
            "event_type": r.event_type,
            "actor":      r.actor,
            "event_data": r.event_data,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
