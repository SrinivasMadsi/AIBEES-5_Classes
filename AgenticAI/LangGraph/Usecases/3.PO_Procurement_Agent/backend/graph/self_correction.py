"""
graph/self_correction.py
Applies the critic's patches to the draft PO and routes back into the
Composer for re-assembly. The graph's conditional edges decide whether
to loop or finalize based on iteration count + verdict.
"""
from graph.state import POState


def apply_patches(draft_po: dict, enriched_items: list[dict], patches: list[dict]) -> tuple[dict, list[dict]]:
    """Apply each patch to the PO and enriched items in-place; returns updated copies."""
    po = dict(draft_po)
    items = [dict(i) for i in enriched_items]
    line_items = [dict(li) for li in po.get("line_items", [])]

    for patch in patches:
        action = patch.get("action")
        sku = patch.get("sku")

        if action == "update_price":
            new_price = patch.get("new_price")
            for li in line_items:
                if li.get("sku") == sku:
                    li["unit_price"] = new_price
                    li["line_total"] = li["quantity"] * new_price
            for it in items:
                if it.get("sku") == sku:
                    it["unit_price"] = new_price

        elif action == "reduce_quantity":
            new_qty = patch.get("max_available") or patch.get("new_quantity")
            for li in line_items:
                if li.get("sku") == sku:
                    li["quantity"] = new_qty
                    li["line_total"] = new_qty * li["unit_price"]
            for it in items:
                if it.get("sku") == sku:
                    it["quantity"] = new_qty

    # Recompute subtotal — tax recompute happens in tax_calc on the next loop
    po["line_items"] = line_items
    po["subtotal"] = round(sum(li["line_total"] for li in line_items), 2)
    return po, items


def self_correction_node(state: POState) -> dict:
    """Apply patches and bump iteration counter."""
    print("\n[self_correction] applying patches")

    patches = state.get("patches", [])
    if not patches:
        return {"iteration_count": state.get("iteration_count", 0) + 1}

    draft_po = state.get("draft_po", {})
    enriched_items = state.get("enriched_items", [])

    new_po, new_items = apply_patches(draft_po, enriched_items, patches)
    findings = list(state.get("findings", []))
    findings.append({
        "check_name": "self_correction",
        "status": "pass",
        "finding": f"Applied {len(patches)} patch(es): "
                   + ", ".join(f"{p.get('action')}:{p.get('sku')}" for p in patches),
        "suggested_fix": {"applied_fixes": patches,
                          "iteration": state.get("iteration_count", 0) + 1},
    })

    print(f"  → applied {len(patches)} patch(es)")
    return {
        "draft_po": new_po,
        "enriched_items": new_items,
        "findings": findings,
        "iteration_count": state.get("iteration_count", 0) + 1,
        "patches": [],   # clear so we don't re-apply
    }


def finalize_node(state: POState) -> dict:
    """Set the final status and produce the final PO output."""
    print("\n[finalize] producing final output")

    verdict = state.get("verdict", "")
    draft_po = state.get("draft_po", {})

    if verdict in {"PASS", "PASS_WITH_WARNINGS"}:
        status = "submitted"
        print(f"  → submitted: {draft_po.get('po_number')}")
    elif verdict == "FAIL_REJECT":
        status = "rejected"
        print(f"  → rejected: {draft_po.get('po_number')}")
    else:
        status = "needs_human"
        print(f"  → needs human review: {draft_po.get('po_number')}")

    final_po = dict(draft_po)
    final_po["status"] = status

    return {"final_po": final_po, "final_status": status}
