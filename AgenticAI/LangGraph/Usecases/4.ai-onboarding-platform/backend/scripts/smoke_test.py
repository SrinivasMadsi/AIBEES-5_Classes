"""
scripts/smoke_test.py
End-to-end test — submit a hardcoded submission and run the full agent pipeline.

Run:
  poetry run python scripts/smoke_test.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text as sql_text

from core.db import get_session
from core.tracer import build_config, flush
from graph import get_graph


def main():
    print("=" * 60)
    print("AI_Onboarding_Platform — End-to-End Smoke Test")
    print("=" * 60)
    print()

    # Load form config
    with get_session() as session:
        form = session.execute(
            sql_text("SELECT config FROM business_data.forms WHERE form_id = 1005")
        ).first()

    if not form:
        print("❌ Form 1005 (Benefits & Services) not found.")
        print("   Run sql/02_seed_forms.sql first.")
        return

    # Hardcoded submission with intentional issues:
    # • Q122 = 2026-01-15 → fails ACC-02 (must be 01/01 or 07/01) → FAIL_REJECT
    # • Q152 = 4000 with Q151 = 3000 → fails DED-01 (4000 < 6000) → FAIL_FIXABLE
    answers = {
        "121": 12,   # Yes
        "122": "2026-01-15",
        "123": 15,   # combined
        "141": 7500,
        "142": 15000,
        "143": 17,   # Yes
        "151": 3000,
        "152": 4000, # ← will trigger DED-01 (should be >= 6000)
        "153": 19,   # Yes
        "161": 25,
        "162": 50,
        "163": 200,
    }

    initial_state = {
        "submission_id":   "smoke_test_001",
        "submission":      {"answers": answers},
        "form_config":     form.config,
        "client_id":       "CLIENT-ACME-001",
        "client_name":     "ACME Healthcare",
        "thread_id":       "smoke_test_thread_001",
        "iteration_count": 0,
        "max_iterations":  1,
    }

    # First ensure a submission row exists
    with get_session() as session:
        session.execute(
            sql_text("""
                INSERT INTO business_data.submissions
                    (submission_id, client_id, client_name, form_id, form_version,
                     submitted_by, answers, status, thread_id)
                VALUES (:sub, :cid, :cname, 1005, 'v1.0',
                        'smoke_test@test.com', CAST(:ans AS jsonb),
                        'submitted', :thread)
                ON CONFLICT (submission_id) DO UPDATE
                    SET answers = EXCLUDED.answers,
                        status = 'submitted',
                        updated_at = now()
            """),
            {
                "sub":    "smoke_test_001",
                "cid":    "CLIENT-ACME-001",
                "cname":  "ACME Healthcare",
                "thread": "smoke_test_thread_001",
                "ans":    json.dumps({"answers": answers}),
            },
        )

    print("→ Invoking main graph...\n")
    graph = get_graph()
    config = {
        "configurable": {"thread_id": "smoke_test_thread_001"},
        **build_config(run_name="smoke_test", session_id="smoke_test_thread_001"),
    }

    final_state = graph.invoke(initial_state, config=config)
    flush()

    print()
    print("=" * 60)
    print("Final State Summary")
    print("=" * 60)
    print(f"  Plan type:       {final_state.get('plan_type')}")
    print(f"  Verdict:         {final_state.get('verdict')}")
    print(f"  Final status:    {final_state.get('final_status')}")
    print(f"  Summary:         {final_state.get('critic_summary')}")
    print(f"  Iterations:      {final_state.get('iteration_count', 0)}")
    print(f"  Findings:        {len(final_state.get('findings', []))}")
    print(f"  Risk signals:    {len(final_state.get('risk_signals', []))}")
    print(f"  Human reviews:   {len(final_state.get('human_review_items', []))}")


if __name__ == "__main__":
    main()
