"""
core/models.py
SQLAlchemy ORM models matching the business_data schema.
Used by the Auditor's checks and the API's data endpoints.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """All ORM models live in the business_data schema by default."""
    __table_args__ = {"schema": "business_data"}


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    approved_categories: Mapped[str] = mapped_column(Text, nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="vendor")


class Product(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(Text, default="INR")
    approved_vendor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("business_data.vendors.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vendor: Mapped[Vendor | None] = relationship(back_populates="products")
    inventory: Mapped["Inventory | None"] = relationship(back_populates="product", uselist=False)


class Inventory(Base):
    __tablename__ = "inventory"

    sku: Mapped[str] = mapped_column(
        Text, ForeignKey("business_data.products.sku"), primary_key=True
    )
    warehouse: Mapped[str] = mapped_column(Text, nullable=False)
    units_in_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=10)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("units_in_stock >= 0", name="non_negative_stock"),
        {"schema": "business_data"},
    )

    product: Mapped[Product] = relationship(back_populates="inventory")


class BudgetCode(Base):
    __tablename__ = "budget_codes"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    department: Mapped[str | None] = mapped_column(Text)
    approved_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    spent_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    fiscal_quarter: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TaxRule(Base):
    __tablename__ = "tax_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    __table_args__ = (
        UniqueConstraint("region", "category", name="uq_region_category"),
        {"schema": "business_data"},
    )


class BusinessRule(Base):
    __tablename__ = "business_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(Text, nullable=False)
    rule_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(Text, primary_key=True)
    requester: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="draft")
    total_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    budget_code: Mapped[str | None] = mapped_column(
        Text, ForeignKey("business_data.budget_codes.code")
    )
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    audit_entries: Mapped[list["AuditLog"]] = relationship(back_populates="po")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_number: Mapped[str | None] = mapped_column(
        Text, ForeignKey("business_data.purchase_orders.po_number")
    )
    check_name: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    finding: Mapped[str | None] = mapped_column(Text)
    suggested_fix: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    po: Mapped[PurchaseOrder | None] = relationship(back_populates="audit_entries")
