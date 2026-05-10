"""
agents/auditor/price_check.py
Verifies PO prices match the current catalog prices.
"""
from sqlalchemy import text

from core.db import get_session
from graph.state import POState


def price_check_node(state: POState) -> dict:
    """Check that each line's unit_price matches the catalog."""
    print("\n[auditor.price_check] verifying prices")

    draft_po = state.get("draft_po", {})
    line_items = draft_po.get("line_items", [])
    findings: list[dict] = list(state.get("findings", []))

    if not line_items:
        return {"findings": findings}

    skus = [item["sku"] for item in line_items]
    with get_session() as session:
        rows = session.execute(
            text("SELECT sku, unit_price FROM business_data.products WHERE sku = ANY(:skus)"),
            {"skus": skus},
        ).mappings().all()

    catalog = {r["sku"]: float(r["unit_price"]) for r in rows}
    has_failure = False

    for item in line_items:
        sku = item["sku"]
        po_price = float(item["unit_price"])
        catalog_price = catalog.get(sku)

        if catalog_price is None:
            findings.append({
                "check_name": "price_check",
                "status": "fail",
                "finding": f"SKU {sku} not in catalog",
                "suggested_fix": {"action": "remove_item", "sku": sku},
            })
            has_failure = True
            continue

        if abs(po_price - catalog_price) > 0.01:
            findings.append({
                "check_name": "price_check",
                "status": "fail",
                "finding": (
                    f"Catalog price for {sku} is ₹{catalog_price:,.2f} but PO has "
                    f"₹{po_price:,.2f}"
                ),
                "suggested_fix": {
                    "action": "update_price",
                    "sku": sku,
                    "old_price": po_price,
                    "new_price": catalog_price,
                },
            })
            has_failure = True

    if not has_failure:
        findings.append({
            "check_name": "price_check",
            "status": "pass",
            "finding": "All prices match catalog",
            "suggested_fix": None,
        })

    print(f"  → {'FAIL' if has_failure else 'PASS'}")
    return {"findings": findings}
