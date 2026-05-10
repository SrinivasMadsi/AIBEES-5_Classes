"""
scripts/test_db.py
Verifies the Neon database connection and reports row counts.
Run:  python scripts/test_db.py
"""
import sys
from pathlib import Path

# Add backend/ to path so config and core resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from core.db import engine, healthcheck


def main():
    print("Testing Neon connection…")
    if not healthcheck():
        print("❌ Could not connect. Check BUSINESS_DB_URL in .env.")
        sys.exit(1)
    print("✅ Connection OK\n")

    tables = [
        "vendors", "products", "inventory", "budget_codes",
        "tax_rules", "business_rules", "purchase_orders", "audit_log",
    ]
    print(f"{'Table':<22}{'Rows':>10}")
    print("-" * 32)
    with engine.connect() as conn:
        for tbl in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM business_data.{tbl}")).scalar()
            print(f"{tbl:<22}{count:>10}")

    print("\n✅ All tables reachable.")


if __name__ == "__main__":
    main()
