"""
agents/composer/intake.py
Parses the user's natural-language procurement request into structured items.
"""
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from config.prompts import INTAKE_PROMPT
from core.llm import get_llm
from graph.state import POState

logger = logging.getLogger(__name__)


def intake_node(state: POState) -> dict:
    """Extract structured intake from the user request."""
    print("\n[composer.intake] parsing user request")

    request = state.get("user_request", "")
    if not request:
        return {"parsed_intake": {}, "messages": []}

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=INTAKE_PROMPT),
        HumanMessage(content=request),
    ])

    raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Intake parse failed: %s | raw=%s", e, raw[:200])
        parsed = {"requester": None, "delivery_location": None,
                  "budget_code": None, "items": []}

    print(f"  → {len(parsed.get('items', []))} item(s) parsed")
    return {"parsed_intake": parsed}
