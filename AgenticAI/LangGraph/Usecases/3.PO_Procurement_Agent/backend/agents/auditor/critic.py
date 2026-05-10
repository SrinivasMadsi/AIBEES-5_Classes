"""
agents/auditor/critic.py
The reasoning step. Reads all four check findings, synthesizes a verdict,
and produces structured patches when self-correction is possible.
"""
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import CRITIC_PROMPT
from core.llm import get_llm
from graph.state import POState

logger = logging.getLogger(__name__)


def critic_node(state: POState) -> dict:
    """Synthesize findings into a verdict + patches."""
    print("\n[auditor.critic] reasoning over findings")

    findings = state.get("findings", [])
    draft_po = state.get("draft_po", {})

    has_fail = any(f["status"] == "fail" for f in findings)
    has_warning = any(f["status"] == "warning" for f in findings)
    has_fixable = any(
        f["status"] == "fail" and f.get("suggested_fix", {}).get("action")
        in {"update_price", "reduce_quantity"}
        for f in findings
    )
    has_unfixable = any(
        f["status"] == "fail" and f.get("suggested_fix", {}).get("action")
        in {"manual_approval_required", "split_po", "manual_review"}
        for f in findings
    )

    # Fast path: rule-based verdict (so we don't waste LLM calls when the answer is obvious)
    if has_unfixable:
        verdict = "FAIL_REJECT"
    elif has_fixable:
        verdict = "FAIL_FIXABLE"
    elif has_warning and not has_fail:
        verdict = "PASS_WITH_WARNINGS"
    elif not has_fail:
        verdict = "PASS"
    else:
        verdict = "FAIL_REJECT"

    # Use the LLM only to produce a human-readable summary
    user = (
        f"Verdict (already determined): {verdict}\n\n"
        f"Findings:\n{json.dumps(findings, indent=2, default=str)}\n\n"
        f"PO summary: total ₹{draft_po.get('total_amount', 0):,.2f}, "
        f"{len(draft_po.get('line_items', []))} line items"
    )
    response = get_llm().invoke([
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=user),
    ])
    raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
        summary = parsed.get("summary", "")
        # Trust LLM patches only if our fast-path agrees
        patches = parsed.get("patches", []) if verdict == "FAIL_FIXABLE" else []
    except json.JSONDecodeError as e:
        logger.warning("Critic JSON parse failed: %s", e)
        summary = raw[:500]
        patches = []

    # Always include the deterministic patches as a safety net
    if verdict == "FAIL_FIXABLE":
        for f in findings:
            fix = f.get("suggested_fix")
            if not fix:
                continue
            if fix.get("action") in {"update_price", "reduce_quantity"} and fix not in patches:
                patches.append(fix)

    print(f"  → verdict={verdict}  patches={len(patches)}")
    return {
        "verdict": verdict,
        "critic_summary": summary,
        "patches": patches,
    }
