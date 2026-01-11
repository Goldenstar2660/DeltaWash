#!/usr/bin/env python3
"""
Database initialization script.

Runs Alembic migrations and verifies database schema.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from sqlalchemy import inspect, text

from src.database import engine
from src.config import settings


def run_migrations():
    """Run Alembic migrations to create/update database schema."""
    print("Running database migrations...")
    
    # Configure Alembic
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    try:
        # Run migrations to head
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def verify_schema():
    """Verify that all expected tables and views exist."""
    print("\nVerifying database schema...")
    
    inspector = inspect(engine)
    
    # Expected tables
    expected_tables = [
        "units",
        "devices",
        "sessions",
        "steps",
        "heartbeats",
        "users",
    ]
    
    # Check tables
    existing_tables = inspector.get_table_names()
    print(f"\nFound {len(existing_tables)} tables:")
    for table in expected_tables:
        if table in existing_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} (missing)")
    
    # Check materialized views
    print("\nChecking materialized views:")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT matviewname FROM pg_matviews
            WHERE schemaname = 'public'
        """))
        matviews = [row[0] for row in result]
    
    expected_views = [
        "mv_daily_compliance",
        "mv_step_statistics",
        "mv_device_status",
    ]
    
    for view in expected_views:
        if view in matviews:
            print(f"  ✅ {view}")
        else:
            print(f"  ❌ {view} (missing)")
    
    # Verify all expected components exist
    all_tables_exist = all(table in existing_tables for table in expected_tables)
    all_views_exist = all(view in matviews for view in expected_views)
    
    if all_tables_exist and all_views_exist:
        print("\n✅ Database schema verification passed")
        return True
    else:
        print("\n❌ Database schema verification failed")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("Hospital Dashboard - Database Initialization")
    print("=" * 60)
    print(f"\nDatabase URL: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    # Verify schema
    if not verify_schema():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Database initialization completed successfully")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Create a user: python src/scripts/create_user.py")
    print("  2. Start the API: uvicorn src.main:app --reload")
    print()


if __name__ == "__main__":
    main()
