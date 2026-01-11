#!/usr/bin/env python3
"""
Refresh materialized views script.

Refreshes all materialized views used for analytics queries.
Uses CONCURRENTLY to avoid blocking read queries.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from src.database import engine
from src.config import settings


MATERIALIZED_VIEWS = [
    "mv_daily_compliance",
    "mv_step_statistics",
    "mv_device_status"
]


def refresh_materialized_views():
    """
    Refresh all materialized views concurrently.
    
    CONCURRENTLY allows other sessions to read from the view while it's being refreshed.
    Note: First refresh cannot use CONCURRENTLY (requires initial data).
    """
    print("=" * 80)
    print("Refreshing Materialized Views")
    print("=" * 80)
    print()
    
    with engine.connect() as conn:
        for view_name in MATERIALIZED_VIEWS:
            try:
                print(f"Refreshing {view_name}...")
                
                # Try concurrent refresh first (works after initial data exists)
                try:
                    conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
                    conn.commit()
                    print(f"✅ {view_name} refreshed (CONCURRENTLY)")
                except Exception as concurrent_error:
                    # If concurrent refresh fails (e.g., no unique index or first run),
                    # fall back to non-concurrent refresh
                    if "does not have a unique index" in str(concurrent_error) or "no data" in str(concurrent_error):
                        print(f"  ⚠️  CONCURRENT refresh not available, using standard refresh...")
                        conn.rollback()
                        conn.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                        conn.commit()
                        print(f"✅ {view_name} refreshed (standard)")
                    else:
                        raise concurrent_error
                    
            except Exception as e:
                print(f"❌ Failed to refresh {view_name}: {e}")
                conn.rollback()
                # Continue with other views
    
    print()
    print("✅ Materialized view refresh completed")


def main():
    """Main entry point."""
    try:
        refresh_materialized_views()
    except Exception as e:
        print(f"\n❌ Error during materialized view refresh: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
