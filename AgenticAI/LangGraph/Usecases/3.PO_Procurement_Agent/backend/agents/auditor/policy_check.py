"""
agents/auditor/policy_check.py
Checks PO against business policies: budget remaining, qty limits, vendor approval.
"""
from sqlalchemy import text

from core.db import get_session
from graph.state import POState


def policy_check_node(state: POState) -> dict:
    """Run all policy checks against the PO."""
    print("\n[auditor.policy_check] verifying policies")

    draft_po = state.get("draft_po", {})
    findings: list[dict] = list(state.get("findings", []))

    total_amount = float(draft_po.get("total_amount", 0))
    budget_code = draft_po.get("budget_code")
    line_items = draft_po.get("line_items", [])

    has_failure = False

    # ── 1. Budget check ──────────────────────────────────────────────────────
    if budget_code:
        with get_session() as session:
            row = session.execute(
                text("""
                    SELECT code, approved_amount, spent_amount, is_active
                    FROM business_data.budget_codes WHERE code = :code
                """),
                {"code": budget_code},
            ).mappings().one_or_none()

        if not row:
            findings.append({
                "check_name": "policy_check",
                "status": "fail",
                "finding": f"Budget code {budget_code} not found",
                "suggested_fix": {"action": "manual_approval_required",
                                  "reason": "invalid_budget_code"},
            })
            has_failure = True
        else:
            available = float(row["approved_amount"]) - float(row["spent_amount"])
            if total_amount > available:
                findings.append({
                    "check_name": "policy_check",
                    "status": "fail",
                    "finding": (
                        f"PO total ₹{total_amount:,.2f} exceeds remaining budget on "
                        f"{budget_code} (₹{available:,.2f} available)"
                    ),
                    "suggested_fix": {
                        "action": "split_po",
                        "remaining_budget": available,
                        "po_amount": total_amount,
                    },
                })
                has_failure = True

    # ── 2. Quantity limits per category ──────────────────────────────────────
    with get_session() as session:
        rule_row = session.execute(
            text("""
                SELECT rule_value FROM business_data.business_rules
                WHERE rule_name = 'max_qty_per_line'
            """)
        ).mappings().one_or_none()

    qty_limits = rule_row["rule_value"] if rule_row else {}

    # Need category for each SKU
    skus = [item["sku"] for item in line_items]
    if skus:
        with get_session() as session:
            cat_rows = session.execute(
                text("SELECT sku, category FROM business_data.products WHERE sku = ANY(:skus)"),
                {"skus": skus},
            ).mappings().all()
        category_by_sku = {r["sku"]: r["category"] for r in cat_rows}

        for item in line_items:
            cat = category_by_sku.get(item["sku"])
            qty = item["quantity"]
            limit = qty_limits.get(cat) if cat else None
            if limit is not None and qty >= limit:
                findings.append({
                    "check_name": "policy_check",
                    "status": "fail",
                    "finding": (
                        f"Quantity {qty} hits max_qty_per_line for {cat} "
                        f"(limit: {limit}, requested: {qty})"
                    ),
                    "suggested_fix": {
                        "action": "manual_approval_required",
                        "category": cat,
                        "limit": limit,
                    },
                })
                has_failure = True

    if not has_failure:
        findings.append({
            "check_name": "policy_check",
            "status": "pass",
            "finding": "All policy checks passed",
            "suggested_fix": None,
        })

    print(f"  → {'FAIL' if has_failure else 'PASS'}")
    return {"findings": findings}
