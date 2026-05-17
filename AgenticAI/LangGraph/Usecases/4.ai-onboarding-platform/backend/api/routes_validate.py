"""
api/routes_validate.py
The Validate button trigger — kicks off the LangGraph agent pipeline.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text as sql_text

from core.db import get_session
from core.tracer import build_config, flush
from graph import get_graph

router = APIRouter(prefix="/api/submissions", tags=["validate"])


@router.post("/{submission_id}/validate")
def validate_submission(submission_id: str):
    """Run the agent pipeline on a submission."""
    # Load submission + form config from DB
    with get_session() as session:
        sub = session.execute(
            sql_text("""
                SELECT submission_id, client_id, client_name, form_id, form_version,
                       submitted_by, answers, thread_id, iteration_count
                FROM business_data.submissions
                WHERE submission_id = :sub
            """),
            {"sub": submission_id},
        ).first()

        if not sub:
            raise HTTPException(404, f"Submission {submission_id} not found")

        form = session.execute(
            sql_text("""
                SELECT config FROM business_data.forms WHERE form_id = :fid
            """),
            {"fid": sub.form_id},
        ).first()

        if not form:
            raise HTTPException(404, f"Form {sub.form_id} not found")

        # Mark as validating
        session.execute(
            sql_text("""
                UPDATE business_data.submissions
                SET status = 'validating', updated_at = now()
                WHERE submission_id = :sub
            """),
            {"sub": submission_id},
        )

    # Build initial state
    answers = sub.answers.get("answers", {}) if isinstance(sub.answers, dict) else sub.answers

    initial_state = {
        "submission_id":   sub.submission_id,
        "submission":      {"answers": answers},
        "form_config":     form.config,
        "client_id":       sub.client_id,
        "client_name":     sub.client_name,
        "thread_id":       sub.thread_id,
        "iteration_count": sub.iteration_count or 0,
        "max_iterations":  1,
    }

    # Invoke graph
    graph = get_graph()
    config = {
        "configurable": {"thread_id": sub.thread_id},
        **build_config(
            run_name="ai_onboarding_validate",
            session_id=sub.thread_id,
            user_id=sub.submitted_by,
            tags=["validate", f"form-{sub.form_id}"],
        ),
    }

    final_state = graph.invoke(initial_state, config=config)
    flush()

    return {
        "submission_id":   submission_id,
        "verdict":         final_state.get("verdict"),
        "final_status":    final_state.get("final_status"),
        "summary":         final_state.get("critic_summary"),
        "plan_type":       final_state.get("plan_type"),
        "iteration_count": final_state.get("iteration_count", 0),
        "findings_count":  len(final_state.get("findings", [])),
        "human_review_items": final_state.get("human_review_items", []),
    }
