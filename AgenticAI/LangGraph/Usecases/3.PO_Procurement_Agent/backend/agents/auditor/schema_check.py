"""
agents/auditor/schema_check.py
Validates that the PO has all mandatory fields and well-formed values.
"""
from graph.state import POState


REQUIRED_FIELDS = {
    "po_number": str,
    "requester": str,
    "delivery_address": str,
    "line_items": list,
    "subtotal": (int, float),
    "gst_amount": (int, float),
    "total_amount": (int, float),
    "currency": str,
}

REQUIRED_LINE_FIELDS = {"sku", "name", "quantity", "unit_price", "line_total"}


def schema_check_node(state: POState) -> dict:
    """Validate the draft PO's structure."""
    print("\n[auditor.schema_check] validating schema")

    draft_po = state.get("draft_po", {})
    findings: list[dict] = list(state.get("findings", []))
    errors: list[str] = []

    # Top-level fields
    for field, expected_type in REQUIRED_FIELDS.items():
        value = draft_po.get(field)
        if value is None or value == "":
            errors.append(f"missing field: {field}")
        elif not isinstance(value, expected_type):
            errors.append(f"wrong type for {field}: expected {expected_type}")

    # Line item structure
    line_items = draft_po.get("line_items") or []
    for i, line in enumerate(line_items):
        missing = REQUIRED_LINE_FIELDS - set(line.keys())
        if missing:
            errors.append(f"line {i}: missing {missing}")

    if not line_items:
        errors.append("line_items is empty")

    if errors:
        findings.append({
            "check_name": "schema_check",
            "status": "fail",
            "finding": "; ".join(errors),
            "suggested_fix": {"action": "manual_review", "errors": errors},
        })
        print(f"  → FAIL: {len(errors)} error(s)")
    else:
        findings.append({
            "check_name": "schema_check",
            "status": "pass",
            "finding": "PO payload conforms to ERP schema",
            "suggested_fix": None,
        })
        print("  → PASS")

    return {"findings": findings}
