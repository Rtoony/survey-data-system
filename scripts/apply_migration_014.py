#!/usr/bin/env python3
"""
Apply Migration 014: Add provenance fields to import_mapping_patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db

def apply_migration():
    """Apply migration 014"""

    migration_sql = open('database/migrations/014_add_import_mapping_provenance.sql', 'r').read()

    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                print("Applying migration 014: Add provenance fields to import_mapping_patterns...")
                cur.execute(migration_sql)
                print("✓ Migration 014 applied successfully!")
                return True
            except Exception as e:
                print(f"✗ Error applying migration: {e}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
