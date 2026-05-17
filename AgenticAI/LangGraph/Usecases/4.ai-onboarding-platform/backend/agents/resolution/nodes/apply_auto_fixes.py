"""
agents/resolution/nodes/apply_auto_fixes.py
Node: apply_auto_fixes

Applies approved patches to the answer_lookup. After this runs, the
graph will loop back through the Validation Agent to re-check with the
corrected answers.
"""
from graph.state import MainState


def apply_auto_fixes_node(state: MainState) -> dict:
    """Apply approved patches to answer_lookup; bump iteration counter."""
    patches = state.get("fix_suggestions", [])
    reviewed = state.get("reviewed_patches", [])
    answer_lookup = dict(state.get("answer_lookup", {}))
    iteration_count = state.get("iteration_count", 0)

    # Only apply patches whose review decision was APPROVE
    approved_rule_ids = {r.get("rule_id") for r in reviewed if r.get("decision") == "APPROVE"}

    applied_count = 0
    for patch in patches:
        if patch.get("rule_id") not in approved_rule_ids and reviewed:
            # If we have explicit reviews, only apply approved ones
            continue
        field_id = str(patch.get("field_id"))
        new_value = patch.get("new_value")
        if field_id and new_value is not None:
            answer_lookup[field_id] = new_value
            applied_count += 1
            print(f"    🔧 patched Q{field_id}: → {new_value} (rule {patch.get('rule_id')})")

    print(f"[resolution.apply_auto_fixes] applied {applied_count} patch(es), iteration → {iteration_count + 1}")

    return {
        "answer_lookup": answer_lookup,
        "iteration_count": iteration_count + 1,
    }
