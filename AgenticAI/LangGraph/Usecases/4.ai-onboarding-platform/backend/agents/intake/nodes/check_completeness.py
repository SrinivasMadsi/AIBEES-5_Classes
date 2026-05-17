"""
agents/intake/nodes/check_completeness.py
Node: check_completeness

Verifies that every required question has been answered. Handles
conditional requirements like "Q122 is required if Q121 = Yes".
"""
from graph.state import MainState


def check_completeness_node(state: MainState) -> dict:
    """Walk the form config, find missing required answers."""
    form_config = state.get("form_config", {})
    answer_lookup = state.get("answer_lookup", {})

    missing = []
    required_count = 0
    answered_count = 0

    for section in form_config.get("sections", []):
        for sub_section in section.get("sub_sections", []):
            for question in sub_section.get("questions", []):
                qid = str(question["question_id"])
                value = answer_lookup.get(qid)
                is_answered = value is not None and value != ""

                is_required = question.get("required", False)
                required_if = question.get("required_if", {})

                # Evaluate conditional requirement
                if required_if and not is_required:
                    for cond_qid, cond_value in required_if.items():
                        if answer_lookup.get(str(cond_qid)) == cond_value:
                            is_required = True
                            break

                if is_required:
                    required_count += 1
                    if not is_answered:
                        because = "always required" if not required_if else _format_condition(required_if)
                        missing.append({
                            "question_id": qid,
                            "question_text": question["question_text"],
                            "section_id": section["section_id"],
                            "section_name": section["section_name"],
                            "sub_section_id": sub_section["sub_section_id"],
                            "sub_section_name": sub_section["sub_section_name"],
                            "required_because": because,
                        })
                    else:
                        answered_count += 1

    completeness_pct = int(answered_count / required_count * 100) if required_count else 100
    is_complete = len(missing) == 0

    status_emoji = "✅" if is_complete else "❌"
    print(f"[intake.check_completeness] {status_emoji} {answered_count}/{required_count} required filled ({completeness_pct}%)")

    return {
        "is_complete": is_complete,
        "completeness_check": {
            "status": "complete" if is_complete else "incomplete",
            "completeness_pct": completeness_pct,
            "answered_count": answered_count,
            "required_count": required_count,
            "missing_required": missing,
        },
    }


def _format_condition(required_if: dict) -> str:
    """Build human-readable explanation of a conditional requirement."""
    parts = [f"Q{qid} answered '{val}'" for qid, val in required_if.items()]
    return " AND ".join(parts)
