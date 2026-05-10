"""
agents/composer/assembler.py
Assembles the final draft PO JSON from enriched items, vendors, and tax.
"""
import uuid
from datetime import datetime, timezone

from graph.state import POState


def assembler_node(state: POState) -> dict:
    """Build the final PO payload."""
    print("\n[composer.assembler] assembling draft PO")

    intake = state.get("parsed_intake", {})
    items = state.get("enriched_items", [])
    tax = state.get("tax_breakdown", {})

    line_items = []
    subtotal = 0.0
    for item in items:
        sku = item.get("sku")
        qty = item.get("quantity", 0) or 0
        price = item.get("unit_price", 0) or 0
        if not (sku and qty and price):
            continue
        line_total = qty * price
        subtotal += line_total
        line_items.append({
            "sku": sku,
            "name": item.get("name"),
            "quantity": qty,
            "unit_price": price,
            "line_total": line_total,
        })

    gst_amount = tax.get("total_gst", 0.0)
    total_amount = round(subtotal + gst_amount, 2)

    po_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    draft_po = {
        "po_number": po_number,
        "requester": intake.get("requester") or "anonymous@aibees.com",
        "delivery_address": intake.get("delivery_location") or "AIBees HQ, Hyderabad",
        "delivery_date": None,
        "budget_code": intake.get("budget_code"),
        "line_items": line_items,
        "subtotal": round(subtotal, 2),
        "gst_amount": gst_amount,
        "total_amount": total_amount,
        "currency": "INR",
        "region": tax.get("region"),
        "status": "draft",
    }

    print(f"  → PO {po_number}: ₹{total_amount:,.2f}, {len(line_items)} line item(s)")
    return {"draft_po": draft_po}
