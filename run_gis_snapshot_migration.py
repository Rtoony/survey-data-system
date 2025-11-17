#!/usr/bin/env python3
"""
Run GIS Snapshot Integrator database migration
Creates tables and adds snapshot_metadata columns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.db_utils import get_cursor

def run_migration():
    """Execute the GIS snapshot schema migration"""
    print("=" * 60)
    print("GIS Snapshot Integrator - Database Migration")
    print("=" * 60)

    # Read the migration SQL file
    migration_file = 'migrations/create_gis_snapshot_schema.sql'

    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        print(f"\n✓ Loaded migration file: {migration_file}")

        # Execute migration
        print("\n→ Executing migration SQL...")
        with get_cursor(dict_cursor=False) as cursor:
            cursor.execute(migration_sql)

        print("✓ Migration executed successfully")

        # Verify tables exist
        print("\n→ Verifying tables were created...")
        with get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name IN ('gis_data_layers', 'project_gis_snapshots')
                ORDER BY table_name
            """)
            tables = cursor.fetchall()

            print("\nCreated tables:")
            for table in tables:
                print(f"  ✓ {table['table_name']}")

        # Verify snapshot_metadata columns
        print("\n→ Verifying snapshot_metadata columns...")
        with get_cursor(dict_cursor=True) as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.columns
                WHERE column_name = 'snapshot_metadata'
                    AND table_schema = 'public'
                ORDER BY table_name
            """)
            columns = cursor.fetchall()

            print("\nAdded snapshot_metadata to:")
            for table in columns:
                print(f"  ✓ {table['table_name']}")

        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Review the migration results above")
        print("  2. Test by inserting a sample GIS layer")
        print("  3. Proceed to Phase 2 (Backend API implementation)")
        print("=" * 60)

        return True

    except FileNotFoundError:
        print(f"\n✗ Error: Migration file not found: {migration_file}")
        print("  Make sure you're running this from the project root directory.")
        return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    exit(0 if success else 1)
