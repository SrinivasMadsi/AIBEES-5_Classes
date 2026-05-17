"""
agents/intake/nodes/parse_submission.py
Node: parse_submission

Reads the raw submission JSON (with qid/value structure) and normalizes
it into:
  - parsed_answers: structured tree with full lineage
  - answer_lookup:  flat {question_id: resolved_value} dict for easy access
"""
from typing import Any

from graph.state import MainState


def parse_submission_node(state: MainState) -> dict:
    """Parse the raw submission into a working format."""
    submission = state.get("submission", {})
    form_config = state.get("form_config", {})

    # Build flat lookup: question_id -> resolved_value
    answer_lookup: dict[str, Any] = {}
    parsed_sections = []

    raw_answers = submission.get("answers", {})

    # Walk the form config to know what each question's response_type is
    for section in form_config.get("sections", []):
        section_id = section["section_id"]
        section_name = section["section_name"]
        parsed_subs = []

        for sub_section in section.get("sub_sections", []):
            sub_id = sub_section["sub_section_id"]
            sub_name = sub_section["sub_section_name"]
            parsed_questions = []

            for question in sub_section.get("questions", []):
                qid = str(question["question_id"])
                raw_value = raw_answers.get(qid)

                # Resolve based on response type
                resolved = _resolve_answer(raw_value, question)

                answer_lookup[qid] = resolved

                parsed_questions.append({
                    "question_id": qid,
                    "question_text": question["question_text"],
                    "response_type": question.get("response_type"),
                    "raw_value": raw_value,
                    "resolved_value": resolved,
                })

            parsed_subs.append({
                "sub_section_id": sub_id,
                "sub_section_name": sub_name,
                "answers": parsed_questions,
            })

        parsed_sections.append({
            "section_id": section_id,
            "section_name": section_name,
            "sub_sections": parsed_subs,
        })

    parsed_answers = {
        "form_id": form_config.get("form_id"),
        "form_name": form_config.get("form_name"),
        "sections": parsed_sections,
    }

    print(f"[intake.parse_submission] parsed {len(answer_lookup)} answers")

    return {
        "parsed_answers": parsed_answers,
        "answer_lookup": answer_lookup,
    }


def _resolve_answer(raw_value: Any, question: dict) -> Any:
    """Resolve qid-based radio/select answers to their string value."""
    if raw_value is None:
        return None

    response_type = question.get("response_type", "text")

    # For radio/select with qid mapping, resolve qid to value
    if response_type in ("radio", "select") and "values" in question:
        for opt in question["values"]:
            if opt.get("qid") == raw_value or str(opt.get("qid")) == str(raw_value):
                return opt.get("value")
        # If raw_value is already a string matching a value, accept it
        for opt in question["values"]:
            if opt.get("value") == raw_value:
                return raw_value

    return raw_value
