"""
graph/state.py
The shared state passed between agents.

This is the "Main State" that the top-level graph uses. Each agent subgraph
sees and modifies a subset of these keys.
"""
from typing import Any, TypedDict


class MainState(TypedDict, total=False):
    # ── Input ──────────────────────────────────────────────────────────
    submission_id: str
    submission: dict                    # raw submission JSON from IPM
    form_config: dict                   # loaded from DB
    client_id: str
    client_name: str

    # ── Intake Agent outputs ───────────────────────────────────────────
    parsed_answers: dict                # structured tree
    answer_lookup: dict                 # flat {qid: value}
    is_complete: bool
    completeness_check: dict
    plan_type: str                      # HMO | PPO | HDHP | EPO
    plan_classification: dict
    risk_signals: list[dict]
    domain_groups: dict                 # {domain: [field_ids]}

    # ── Validation Agent outputs ───────────────────────────────────────
    sop_rules_by_domain: dict           # {domain: [rules]}
    findings: list[dict]
    rules_applied: int

    # ── Resolution Agent outputs ───────────────────────────────────────
    finding_categories: dict            # {pass: [...], warning: [...], fixable: [...], reject: [...]}
    fix_suggestions: list[dict]
    reviewed_patches: list[dict]
    verdict: str                        # PASS | FAIL_FIXABLE | FAIL_REJECT
    critic_summary: str
    human_review_items: list[dict]

    # ── Control flow ───────────────────────────────────────────────────
    thread_id: str
    iteration_count: int
    max_iterations: int
    final_status: str                   # validated_pass | validated_with_fixes | pending_human_review | rejected
    error: str
