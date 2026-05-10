"""
agents/auditor/inventory_check.py
Verifies that requested quantities don't exceed current inventory.
"""
from sqlalchemy import text

from core.db import get_session
from graph.state import POState


def inventory_check_node(state: POState) -> dict:
    """Check stock for every line item."""
    print("\n[auditor.inventory_check] verifying stock")

    draft_po = state.get("draft_po", {})
    line_items = draft_po.get("line_items", [])
    findings: list[dict] = list(state.get("findings", []))

    if not line_items:
        return {"findings": findings}

    skus = [item["sku"] for item in line_items]

    with get_session() as session:
        rows = session.execute(
            text("""
                SELECT sku, units_in_stock, warehouse, reorder_threshold
                FROM business_data.inventory
                WHERE sku = ANY(:skus)
            """),
            {"skus": skus},
        ).mappings().all()

    stock_by_sku = {r["sku"]: dict(r) for r in rows}

    has_failure = False
    for item in line_items:
        sku = item["sku"]
        qty = item["quantity"]
        info = stock_by_sku.get(sku)

        if not info:
            findings.append({
                "check_name": "inventory_check",
                "status": "fail",
                "finding": f"No inventory record found for {sku}",
                "suggested_fix": {"action": "remove_item", "sku": sku},
            })
            has_failure = True
            continue

        stock = info["units_in_stock"]
        if stock < qty:
            findings.append({
                "check_name": "inventory_check",
                "status": "fail",
                "finding": (
                    f"Requested {qty} units of {sku} but only {stock} in stock "
                    f"at {info['warehouse']}"
                ),
                "suggested_fix": {
                    "action": "reduce_quantity",
                    "sku": sku,
                    "max_available": stock,
                },
            })
            has_failure = True
        elif stock - qty < info.get("reorder_threshold", 10):
            findings.append({
                "check_name": "inventory_check",
                "status": "warning",
                "finding": (
                    f"After this PO, {sku} stock will be near reorder threshold "
                    f"({stock - qty} remaining)"
                ),
                "suggested_fix": None,
            })

    if not has_failure and not any(
        f["check_name"] == "inventory_check" for f in findings[len(state.get("findings", [])):]
    ):
        findings.append({
            "check_name": "inventory_check",
            "status": "pass",
            "finding": "All items have sufficient stock",
            "suggested_fix": None,
        })

    print(f"  → {sum(1 for f in findings if f['check_name'] == 'inventory_check')} finding(s)")
    return {"findings": findings}
