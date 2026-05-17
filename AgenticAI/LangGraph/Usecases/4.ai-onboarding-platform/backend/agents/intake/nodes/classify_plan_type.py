"""
agents/intake/nodes/classify_plan_type.py
Node: classify_plan_type

Uses the LLM to infer whether the submitted plan is HMO/PPO/HDHP/EPO
based on patterns in the answers. This classification determines which
SOP variant the Validation Agent loads (since different plan types
have different rules).
"""
import json
import re

from config.prompts import CLASSIFY_PLAN_TYPE_PROMPT
from core.llm import get_llm
from graph.state import MainState


def classify_plan_type_node(state: MainState) -> dict:
    """Have the LLM classify the plan type based on submitted answers."""
    answer_lookup = state.get("answer_lookup", {})
    parsed_answers = state.get("parsed_answers", {})

    # Build a clean summary of the answers for the LLM
    summary_lines = ["Submitted answers:"]
    for section in parsed_answers.get("sections", []):
        for sub in section.get("sub_sections", []):
            for ans in sub.get("answers", []):
                val = ans.get("resolved_value")
                if val is not None and val != "":
                    summary_lines.append(
                        f"  - {ans['question_text']}: {val}"
                    )
    summary = "\n".join(summary_lines)

    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": CLASSIFY_PLAN_TYPE_PROMPT},
        {"role": "user", "content": summary},
    ])

    try:
        classification = _parse_json(response.content)
    except Exception as e:
        print(f"[intake.classify_plan_type] ⚠️ parse error: {e}, defaulting to PPO")
        classification = {
            "plan_type": "PPO",
            "confidence": "low",
            "reasoning": ["Fallback default due to parse error"],
        }

    plan_type = classification.get("plan_type", "PPO")
    confidence = classification.get("confidence", "medium")
    print(f"[intake.classify_plan_type] → {plan_type} (confidence: {confidence})")

    return {
        "plan_type": plan_type,
        "plan_classification": classification,
    }


def _parse_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    text = text.strip()
    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
