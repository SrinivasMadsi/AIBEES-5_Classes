"""
agents/resolution/nodes/generate_fix_suggestions.py
Node: generate_fix_suggestions

For each fixable finding, generates a concrete fix patch. Uses the LLM
to reason about what value should be applied based on the rule semantics
and current submission values.
"""
import json
import re

from config.prompts import GENERATE_FIXES_PROMPT
from core.llm import get_llm
from graph.state import MainState


def generate_fix_suggestions_node(state: MainState) -> dict:
    """Have the LLM propose structured fix patches for fixable findings."""
    buckets = state.get("finding_categories", {})
    fixable = buckets.get("fixable", [])

    if not fixable:
        print("[resolution.generate_fix_suggestions] no fixable findings — skipping")
        return {"fix_suggestions": []}

    answer_lookup = state.get("answer_lookup", {})

    # Build context for LLM
    context_lines = ["Current answers:"]
    for f in fixable:
        field = f.get("affected_field")
        if field:
            context_lines.append(f"  Q{field} = {answer_lookup.get(str(field), 'N/A')}")
    context_lines.append("")
    context_lines.append("Fixable findings:")
    context_lines.append(json.dumps(fixable, indent=2))

    user_msg = "\n".join(context_lines)

    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": GENERATE_FIXES_PROMPT},
        {"role": "user", "content": user_msg},
    ])

    try:
        result = _parse_json(response.content)
        patches = result.get("patches", [])
    except Exception as e:
        print(f"[resolution.generate_fix_suggestions] ⚠️ parse error: {e}")
        patches = _fallback_patches(fixable, answer_lookup)

    print(f"[resolution.generate_fix_suggestions] generated {len(patches)} patch(es)")

    return {"fix_suggestions": patches}


def _fallback_patches(fixable, answer_lookup):
    """Deterministic fallback when LLM JSON parsing fails."""
    patches = []
    for f in fixable:
        field = f.get("affected_field")
        expected = f.get("expected_value")
        if field and expected is not None:
            patches.append({
                "rule_id": f.get("rule_id"),
                "action": "update_field",
                "field_id": str(field),
                "current_value": f.get("current_value"),
                "new_value": expected,
                "reasoning": f.get("message", "Applying expected value from rule"),
            })
    return patches


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
