"""
api/routes_data.py
Read-only endpoints powering the UI's reference data and history panels.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from core.db import get_session

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/products")
def list_products():
    """All products with vendor name and current stock."""
    sql = text("""
        SELECT
            p.sku,
            p.name,
            p.category,
            p.unit_price,
            p.currency,
            v.name           AS vendor_name,
            i.units_in_stock,
            i.warehouse,
            i.reorder_threshold
        FROM business_data.products p
        LEFT JOIN business_data.vendors   v ON p.approved_vendor_id = v.id
        LEFT JOIN business_data.inventory i ON p.sku = i.sku
        ORDER BY p.category, p.name
    """)
    with get_session() as session:
        rows = session.execute(sql).mappings().all()
    return [dict(r) | {"unit_price": float(r["unit_price"])} for r in rows]


@router.get("/vendors")
def list_vendors():
    sql = text("""
        SELECT id, name, approved_categories, payment_terms_days, is_active
        FROM business_data.vendors
        ORDER BY name
    """)
    with get_session() as session:
        rows = session.execute(sql).mappings().all()
    return [dict(r) for r in rows]


@router.get("/inventory")
def list_inventory():
    sql = text("""
        SELECT
            i.sku, p.name, i.warehouse, i.units_in_stock,
            i.reorder_threshold, i.last_updated
        FROM business_data.inventory i
        JOIN business_data.products p ON i.sku = p.sku
        ORDER BY i.warehouse, p.name
    """)
    with get_session() as session:
        rows = session.execute(sql).mappings().all()
    return [dict(r) for r in rows]


@router.get("/budgets")
def list_budgets():
    sql = text("""
        SELECT
            code, department, fiscal_quarter,
            approved_amount, spent_amount,
            (approved_amount - spent_amount) AS available
        FROM business_data.budget_codes
        ORDER BY department
    """)
    with get_session() as session:
        rows = session.execute(sql).mappings().all()
    return [
        dict(r) | {
            "approved_amount": float(r["approved_amount"]),
            "spent_amount":    float(r["spent_amount"]),
            "available":       float(r["available"]),
        }
        for r in rows
    ]


@router.get("/orders")
def list_orders(limit: int = 50):
    sql = text("""
        SELECT
            po.po_number, po.requester, po.status,
            po.total_amount, po.budget_code,
            bc.department,
            po.created_at,
            (SELECT COUNT(*) FROM business_data.audit_log al
                WHERE al.po_number = po.po_number) AS finding_count
        FROM business_data.purchase_orders po
        LEFT JOIN business_data.budget_codes bc ON po.budget_code = bc.code
        ORDER BY po.created_at DESC
        LIMIT :limit
    """)
    with get_session() as session:
        rows = session.execute(sql, {"limit": limit}).mappings().all()
    return [
        dict(r) | {"total_amount": float(r["total_amount"]) if r["total_amount"] else None}
        for r in rows
    ]


@router.get("/orders/{po_number}")
def get_order(po_number: str):
    sql = text("""
        SELECT po_number, requester, status, total_amount, budget_code, payload, created_at
        FROM business_data.purchase_orders
        WHERE po_number = :po
    """)
    with get_session() as session:
        row = session.execute(sql, {"po": po_number}).mappings().one_or_none()
    if not row:
        raise HTTPException(404, f"PO {po_number} not found")
    return dict(row) | {"total_amount": float(row["total_amount"]) if row["total_amount"] else None}


@router.get("/orders/{po_number}/audit")
def get_order_audit(po_number: str):
    sql = text("""
        SELECT id, check_name, status, finding, suggested_fix, created_at
        FROM business_data.audit_log
        WHERE po_number = :po
        ORDER BY created_at, id
    """)
    with get_session() as session:
        rows = session.execute(sql, {"po": po_number}).mappings().all()
    return [dict(r) for r in rows]
