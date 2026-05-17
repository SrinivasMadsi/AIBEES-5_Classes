"""
graph/builder.py
The main graph that orchestrates the three agent subgraphs.

Flow:
  START
    → intake_agent (subgraph)
    → [if incomplete] → finalize → END
    → [otherwise] → validation_agent (subgraph)
                    → resolution_agent (subgraph)
                    → [route based on verdict]
                        ├── PASS / validated → finalize → END
                        ├── FAIL_FIXABLE (iter<max) → validation_agent (loop)
                        └── FAIL_REJECT → finalize (paused for HITL) → END

HITL behavior:
  When verdict is FAIL_REJECT, escalate_to_BOM inserts human_reviews rows
  and sets final_status='pending_human_review'. The graph then finalizes
  with that status. The BOM analyst's decision API call resumes the graph
  via a separate code path (or simply updates the submission directly).

Fault tolerance:
  PostgresSaver checkpoints state after EVERY node — including inside
  subgraphs. If the process crashes mid-validation, invoking with the same
  thread_id resumes from the last checkpoint.
"""
from langgraph.graph import END, START, StateGraph

from agents import build_intake_agent, build_resolution_agent, build_validation_agent
from config.settings import settings
from core.checkpointer import get_checkpointer
from core.db import get_session
from graph.state import MainState
from sqlalchemy import text as sql_text


def finalize_node(state: MainState) -> dict:
    """Final node — persist findings + status to business_data tables."""
    submission_id = state.get("submission_id", "")
    findings = state.get("findings", [])
    final_status = state.get("final_status") or _derive_status(state)

    with get_session() as session:
        # Update submission status
        session.execute(
            sql_text("""
                UPDATE business_data.submissions
                SET status = :status,
                    plan_type = :plan_type,
                    thread_id = :thread,
                    iteration_count = :iter,
                    updated_at = now()
                WHERE submission_id = :sub
            """),
            {
                "status":    final_status,
                "plan_type": state.get("plan_type"),
                "thread":    state.get("thread_id"),
                "iter":      state.get("iteration_count", 0),
                "sub":       submission_id,
            },
        )

        # Clear old findings and insert fresh
        session.execute(
            sql_text("DELETE FROM business_data.findings WHERE submission_id = :sub"),
            {"sub": submission_id},
        )
        for f in findings:
            session.execute(
                sql_text("""
                    INSERT INTO business_data.findings
                        (submission_id, rule_id, rule_name, domain, affected_field,
                         status, severity, current_value, expected_value, message,
                         suggested_fix, auto_applied)
                    VALUES (:sub, :rule_id, :rule_name, :domain, :field,
                            :status, :severity,
                            CAST(:current AS jsonb), CAST(:expected AS jsonb),
                            :message, CAST(:fix AS jsonb), :applied)
                """),
                {
                    "sub":       submission_id,
                    "rule_id":   f.get("rule_id"),
                    "rule_name": f.get("rule_name"),
                    "domain":    f.get("domain"),
                    "field":     str(f.get("affected_field")),
                    "status":    f.get("status"),
                    "severity":  f.get("severity"),
                    "current":   _json(f.get("current_value")),
                    "expected":  _json(f.get("expected_value")),
                    "message":   f.get("message"),
                    "fix":       _json(f.get("suggested_fix")),
                    "applied":   bool(f.get("auto_applied", False)),
                },
            )

        # Audit log
        session.execute(
            sql_text("""
                INSERT INTO business_data.audit_log
                    (submission_id, event_type, actor, event_data)
                VALUES (:sub, 'validation_completed', 'system',
                        CAST(:data AS jsonb))
            """),
            {
                "sub":  submission_id,
                "data": _json({
                    "final_status": final_status,
                    "verdict":      state.get("verdict"),
                    "summary":      state.get("critic_summary"),
                    "iterations":   state.get("iteration_count", 0),
                }),
            },
        )

    print(f"[finalize] persisted submission={submission_id} status={final_status}")
    return {"final_status": final_status}


def _json(value):
    """Serialize a value to JSON string for SQL CAST."""
    import json as _json_mod
    if value is None:
        return None
    return _json_mod.dumps(value, default=str)


def _derive_status(state: MainState) -> str:
    """Derive final_status from verdict if not already set."""
    verdict = state.get("verdict", "")
    if verdict == "PASS":
        return "validated_pass"
    if verdict == "FAIL_REJECT":
        return "pending_human_review"
    if verdict == "FAIL_FIXABLE":
        return "validated_with_fixes"
    if verdict == "INCOMPLETE":
        return "rejected"
    return "validated_pass"


def _route_after_intake(state: MainState) -> str:
    """If intake found the submission incomplete, skip to finalize."""
    if state.get("final_status") == "rejected" or state.get("error") == "incomplete_submission":
        return "finalize"
    return "validation_agent"


def _route_after_resolution(state: MainState) -> str:
    """
    Main graph routing after the Resolution Agent runs:
      • FAIL_FIXABLE + iter < max → loop back to validation_agent
      • All other verdicts → finalize
    """
    verdict = state.get("verdict", "")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", settings.max_self_correction_iterations)

    if verdict == "FAIL_FIXABLE" and iteration < max_iter:
        print(f"[main_router] FAIL_FIXABLE iter={iteration}<{max_iter} — looping back to validation")
        return "validation_agent"

    return "finalize"


def build_main_graph():
    """Build, compile, and return the orchestration graph with checkpointer."""
    intake_agent = build_intake_agent()
    validation_agent = build_validation_agent()
    resolution_agent = build_resolution_agent()

    g = StateGraph(MainState)
    g.add_node("intake_agent",     intake_agent)
    g.add_node("validation_agent", validation_agent)
    g.add_node("resolution_agent", resolution_agent)
    g.add_node("finalize",         finalize_node)

    g.add_edge(START, "intake_agent")

    g.add_conditional_edges(
        "intake_agent",
        _route_after_intake,
        {
            "validation_agent": "validation_agent",
            "finalize":         "finalize",
        },
    )

    g.add_edge("validation_agent", "resolution_agent")

    g.add_conditional_edges(
        "resolution_agent",
        _route_after_resolution,
        {
            "validation_agent": "validation_agent",  # self-correction loop
            "finalize":         "finalize",
        },
    )

    g.add_edge("finalize", END)

    checkpointer = get_checkpointer()
    return g.compile(checkpointer=checkpointer)


# ── Singleton ───────────────────────────────────────────────────────────────
_compiled_graph = None


def get_graph():
    """Return the singleton compiled main graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_main_graph()
        _save_graph_visualization(_compiled_graph)
    return _compiled_graph


def _save_graph_visualization(graph):
    """Save Mermaid + PNG of the compiled graph to backend/graph/."""
    from pathlib import Path
    out_dir = Path(__file__).resolve().parent
    try:
        mmd = graph.get_graph().draw_mermaid()
        (out_dir / "main_graph.mmd").write_text(mmd, encoding="utf-8")
        try:
            png = graph.get_graph().draw_mermaid_png()
            (out_dir / "main_graph.png").write_bytes(png)
            print(f"[graph] saved visualization to {out_dir}/main_graph.png")
        except Exception:
            pass  # PNG requires network; skip silently
    except Exception as e:
        print(f"[graph] visualization skipped: {e}")
