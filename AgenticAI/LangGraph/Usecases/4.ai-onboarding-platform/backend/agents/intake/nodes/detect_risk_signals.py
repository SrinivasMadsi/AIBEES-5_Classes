"""
agents/intake/nodes/detect_risk_signals.py
Node: detect_risk_signals

Pre-validation scan for anti-patterns that need attention from the
validator. Does NOT validate against SOPs — that's the validator's job.
"""
import json
import re

from config.prompts import DETECT_RISK_SIGNALS_PROMPT
from core.llm import get_llm
from graph.state import MainState


def detect_risk_signals_node(state: MainState) -> dict:
    """LLM scans answers for anti-patterns."""
    parsed_answers = state.get("parsed_answers", {})
    plan_type = state.get("plan_type", "")

    # Build summary for LLM
    summary_lines = [f"Plan type: {plan_type}", "", "Submitted answers:"]
    for section in parsed_answers.get("sections", []):
        for sub in section.get("sub_sections", []):
            for ans in sub.get("answers", []):
                val = ans.get("resolved_value")
                if val is not None and val != "":
                    summary_lines.append(
                        f"  Q{ans['question_id']} ({ans['question_text']}): {val}"
                    )
    summary = "\n".join(summary_lines)

    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": DETECT_RISK_SIGNALS_PROMPT},
        {"role": "user", "content": summary},
    ])

    try:
        result = _parse_json(response.content)
        signals = result.get("signals", [])
    except Exception as e:
        print(f"[intake.detect_risk_signals] ⚠️ parse error: {e}")
        signals = []

    print(f"[intake.detect_risk_signals] → {len(signals)} signal(s) detected")
    for sig in signals:
        print(f"    • [{sig.get('priority', '?')}] {sig.get('description', '')}")

    return {"risk_signals": signals}


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
