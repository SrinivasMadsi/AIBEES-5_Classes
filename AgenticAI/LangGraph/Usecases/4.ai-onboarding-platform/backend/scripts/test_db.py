"""
scripts/test_db.py
Quick sanity check — list all tables in business_data with row counts.

Run:
  poetry run python scripts/test_db.py
"""
import sys
from pathlib import Path

# Add backend to sys.path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from core.db import engine, healthcheck


def main():
    print("=" * 60)
    print("AI_Onboarding_Platform — Database Sanity Check")
    print("=" * 60)

    if not healthcheck():
        print("❌ Cannot reach the database. Check BUSINESS_DB_URL in .env")
        return

    print("✅ Database reachable\n")

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'business_data'
                ORDER BY table_name
            """)
        ).fetchall()

        if not result:
            print("⚠️  No tables found in business_data schema.")
            print("    Run sql/01_create_tables.sql first.")
            return

        print(f"Tables in business_data ({len(result)}):")
        print()
        for row in result:
            table = row[0]
            count = conn.execute(text(f"SELECT count(*) FROM business_data.{table}")).scalar()
            print(f"  • {table:<25} {count} rows")

    print("\n✅ Done")


if __name__ == "__main__":
    main()
