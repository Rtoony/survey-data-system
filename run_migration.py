#!/usr/bin/env python3
"""
Run database migration script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.db_utils import get_cursor

def run_migration(migration_file):
    """Run a migration SQL file."""
    print(f"Running migration: {migration_file}")

    # Read the migration file
    with open(migration_file, 'r') as f:
        sql_content = f.read()

    # Execute the migration
    try:
        with get_cursor(dict_cursor=False) as cursor:
            cursor.execute(sql_content)
        print(f"✓ Migration completed successfully: {migration_file}")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    migration_file = 'database/migrations/008_spec_management_system.sql'

    if not os.path.exists(migration_file):
        print(f"Error: Migration file not found: {migration_file}")
        sys.exit(1)

    success = run_migration(migration_file)
    sys.exit(0 if success else 1)
