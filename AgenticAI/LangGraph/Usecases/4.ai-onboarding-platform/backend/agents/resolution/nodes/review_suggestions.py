"""
agents/resolution/nodes/review_suggestions.py
Node: review_suggestions

The critic. Reviews proposed patches and emits the final verdict.
This is the "reflection" moment of the system — reasoning over the
intermediate outputs to decide the next action.

Verdicts:
  • PASS         — all good, finalize
  • FAIL_FIXABLE — at least one approved patch to apply, then re-validate
  • FAIL_REJECT  — at least one finding needs human review
"""
import json
import re

from config.prompts import REVIEW_FIXES_PROMPT
from core.llm import get_llm
from graph.state import MainState


def review_suggestions_node(state: MainState) -> dict:
    """Critic reviews patches and emits verdict."""
    buckets = state.get("finding_categories", {})
    patches = state.get("fix_suggestions", [])

    has_rejects = len(buckets.get("reject", [])) > 0
    has_fixable = len(patches) > 0

    # Quick deterministic verdict for simple cases
    if has_rejects:
        verdict = "FAIL_REJECT"
        summary = (
            f"{len(buckets['reject'])} finding(s) require human review "
            f"(regulatory/policy issues that cannot be auto-corrected)."
        )
        reviewed = [{"rule_id": p.get("rule_id"), "decision": "APPROVE", "reason": "Auto-approved alongside reject"} for p in patches]
        print(f"[resolution.review_suggestions] verdict=FAIL_REJECT — escalating to BOM")
        return {
            "verdict": verdict,
            "critic_summary": summary,
            "reviewed_patches": reviewed,
        }

    if not has_fixable:
        verdict = "PASS"
        summary = "All checks passed (or warnings only). Submission ready to finalize."
        print(f"[resolution.review_suggestions] verdict=PASS")
        return {
            "verdict": verdict,
            "critic_summary": summary,
            "reviewed_patches": [],
        }

    # LLM review for fixable patches
    context = (
        f"Proposed patches:\n{json.dumps(patches, indent=2)}\n\n"
        f"Findings that triggered them:\n{json.dumps(buckets.get('fixable', []), indent=2)}"
    )

    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": REVIEW_FIXES_PROMPT},
        {"role": "user", "content": context},
    ])

    try:
        result = _parse_json(response.content)
        verdict = result.get("verdict", "FAIL_FIXABLE")
        summary = result.get("overall_summary", "Patches reviewed.")
        reviewed = result.get("reviewed_patches", [])
    except Exception as e:
        print(f"[resolution.review_suggestions] ⚠️ parse error: {e}, defaulting to FAIL_FIXABLE")
        verdict = "FAIL_FIXABLE"
        summary = "Patches generated, will apply and re-validate."
        reviewed = [{"rule_id": p.get("rule_id"), "decision": "APPROVE", "reason": "Auto-approved (LLM parse error)"} for p in patches]

    print(f"[resolution.review_suggestions] verdict={verdict}")
    print(f"    {summary}")

    return {
        "verdict": verdict,
        "critic_summary": summary,
        "reviewed_patches": reviewed,
    }


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
