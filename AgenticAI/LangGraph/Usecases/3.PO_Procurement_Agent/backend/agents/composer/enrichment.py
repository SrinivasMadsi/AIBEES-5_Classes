"""
agents/composer/enrichment.py
For each parsed item, queries the catalog and uses the LLM to pick the
best-matching SKU. Output rows are ready for the rest of the Composer pipeline.
"""
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import text

from config.prompts import ENRICHMENT_PROMPT
from core.db import get_session
from core.llm import get_llm
from graph.state import POState

logger = logging.getLogger(__name__)


def _candidates_for(description: str) -> list[dict]:
    """Pull a small set of catalog rows likely to match the description."""
    # Naive keyword filter; in production you'd use full-text search or embeddings.
    keywords = [w for w in description.lower().split() if len(w) > 2][:4]
    if not keywords:
        return []

    pattern = "|".join(keywords)
    sql = text("""
        SELECT sku, name, category, unit_price, approved_vendor_id
        FROM business_data.products
        WHERE LOWER(name) ~ :pattern OR LOWER(category) ~ :pattern
        ORDER BY name
        LIMIT 10
    """)
    with get_session() as session:
        rows = session.execute(sql, {"pattern": pattern}).mappings().all()
    return [dict(r) for r in rows]


def _match_with_llm(description: str, candidates: list[dict]) -> dict:
    """Ask the LLM to pick the best SKU from the candidates."""
    if not candidates:
        return {"sku": None, "confidence": "low", "reason": "no candidates found"}

    user = (
        f"Item description: {description}\n\n"
        f"Candidates:\n{json.dumps(candidates, indent=2, default=str)}"
    )
    response = get_llm().invoke([
        SystemMessage(content=ENRICHMENT_PROMPT),
        HumanMessage(content=user),
    ])

    raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"sku": None, "confidence": "low", "reason": "parse failed"}


def enrichment_node(state: POState) -> dict:
    """Resolve each item to a catalog row."""
    print("\n[composer.enrichment] resolving SKUs")

    items = state.get("parsed_intake", {}).get("items", [])
    enriched: list[dict] = []

    for item in items:
        description = item.get("description", "")
        quantity = item.get("quantity", 0)

        candidates = _candidates_for(description)
        match = _match_with_llm(description, candidates)
        sku = match.get("sku")

        if not sku:
            print(f"  ✗ '{description}' — {match.get('reason')}")
            enriched.append({
                "description": description,
                "sku": None,
                "quantity": quantity,
                "match_confidence": match.get("confidence", "low"),
                "match_reason": match.get("reason", ""),
            })
            continue

        # Look up the chosen SKU's full details
        with get_session() as session:
            row = session.execute(
                text("""
                    SELECT sku, name, category, unit_price, approved_vendor_id
                    FROM business_data.products WHERE sku = :sku
                """),
                {"sku": sku},
            ).mappings().one_or_none()

        if row:
            r = dict(row)
            enriched.append({
                "description": description,
                "sku": r["sku"],
                "name": r["name"],
                "category": r["category"],
                "unit_price": float(r["unit_price"]),
                "approved_vendor_id": r["approved_vendor_id"],
                "quantity": quantity,
                "match_confidence": match.get("confidence", "high"),
            })
            print(f"  ✓ '{description}' → {r['sku']} ({match.get('confidence')})")

    return {"enriched_items": enriched}
