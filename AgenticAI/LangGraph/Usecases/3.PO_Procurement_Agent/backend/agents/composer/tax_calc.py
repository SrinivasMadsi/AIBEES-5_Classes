"""
agents/composer/tax_calc.py
Computes GST per line item using the tax_rules table.
"""
from sqlalchemy import text

from config.settings import settings
from core.db import get_session
from graph.state import POState


def _region_from_location(location: str | None) -> str:
    """Map a delivery location string to a region (state) for tax rules."""
    if not location:
        return settings.default_region
    location_lower = location.lower()
    if "hyderabad" in location_lower or "telangana" in location_lower:
        return "Telangana"
    if "bangalore" in location_lower or "bengaluru" in location_lower or "karnataka" in location_lower:
        return "Karnataka"
    if "mumbai" in location_lower or "maharashtra" in location_lower:
        return "Maharashtra"
    return settings.default_region


def tax_calc_node(state: POState) -> dict:
    """Compute GST line by line."""
    print("\n[composer.tax_calc] computing GST")

    items = state.get("enriched_items", [])
    delivery_location = state.get("parsed_intake", {}).get("delivery_location")
    region = _region_from_location(delivery_location)

    breakdown: list[dict] = []
    total_gst = 0.0

    with get_session() as session:
        for item in items:
            sku = item.get("sku")
            category = item.get("category")
            qty = item.get("quantity", 0) or 0
            price = item.get("unit_price", 0) or 0

            if not (sku and category and qty and price):
                continue

            row = session.execute(
                text("""
                    SELECT gst_rate FROM business_data.tax_rules
                    WHERE region = :region AND category = :category
                """),
                {"region": region, "category": category},
            ).mappings().one_or_none()

            rate = float(row["gst_rate"]) if row else 18.0
            line_subtotal = qty * price
            line_gst = round(line_subtotal * rate / 100, 2)
            total_gst += line_gst

            breakdown.append({
                "sku": sku,
                "subtotal": line_subtotal,
                "gst_rate": rate,
                "gst_amount": line_gst,
            })

    print(f"  → region={region}  total GST={total_gst:.2f}")
    return {
        "tax_breakdown": {
            "region": region,
            "total_gst": round(total_gst, 2),
            "breakdown": breakdown,
        }
    }
