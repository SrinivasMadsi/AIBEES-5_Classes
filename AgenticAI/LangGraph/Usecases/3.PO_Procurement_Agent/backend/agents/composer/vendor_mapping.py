"""
agents/composer/vendor_mapping.py
For each enriched item, fetch the approved vendor's details.
"""
from sqlalchemy import text

from core.db import get_session
from graph.state import POState


def vendor_mapping_node(state: POState) -> dict:
    """Look up vendor info for each item's approved_vendor_id."""
    print("\n[composer.vendor_mapping] mapping vendors")

    items = state.get("enriched_items", [])
    vendors: dict[str, dict] = {}

    vendor_ids = {item.get("approved_vendor_id") for item in items if item.get("approved_vendor_id")}

    if not vendor_ids:
        return {"selected_vendors": {}}

    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT id, name, approved_categories, payment_terms_days, is_active
                FROM business_data.vendors
                WHERE id = ANY(:ids)
            """),
            {"ids": list(vendor_ids)},
        ).mappings().all()

    by_id = {row["id"]: dict(row) for row in rows}

    for item in items:
        sku = item.get("sku")
        vid = item.get("approved_vendor_id")
        if sku and vid in by_id:
            vendors[sku] = by_id[vid]

    print(f"  → {len(vendors)} vendor mapping(s) resolved")
    return {"selected_vendors": vendors}
