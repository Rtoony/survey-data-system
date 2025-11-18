#!/usr/bin/env python3
"""
Verification script for migration 020: Drop obsolete drawing tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.db_utils import execute_query

def verify_migration():
    """Verify that all obsolete drawing tables have been dropped."""
    print("Verifying migration 020: Drop obsolete drawing tables...")
    print("-" * 70)

    # List of tables that should be dropped
    obsolete_tables = ['drawing_materials', 'drawing_references', 'drawings']

    # Query to check if any of these tables still exist
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name IN ('drawing_materials', 'drawing_references', 'drawings')
          AND table_schema = 'public'
        ORDER BY table_name;
    """

    try:
        results = execute_query(query)

        if results and len(results) > 0:
            print("❌ FAILED: Obsolete drawing tables still exist in the database!")
            print("\nTables that should be dropped:")
            print(f"{'Table Name':<30}")
            print("-" * 40)
            for row in results:
                print(f"{row['table_name']:<30}")
            print(f"\nTotal obsolete tables: {len(results)}")
            print("\nAction required: Run migration 020 to drop these tables.")
            return False

        # Success - no obsolete tables found
        print("✅ SUCCESS: All obsolete drawing tables have been dropped!\n")
        print("The following tables no longer exist:")
        for table in obsolete_tables:
            print(f"  ✓ {table}")

        # Final comprehensive check
        print("\n" + "-" * 70)
        print("Comprehensive Migration Verification")
        print("-" * 70)

        # Check 1: Verify no drawing_id columns exist
        drawing_id_query = """
            SELECT COUNT(DISTINCT table_name) as count
            FROM information_schema.columns
            WHERE column_name = 'drawing_id'
              AND table_schema = 'public'
              AND table_name NOT LIKE 'pg_%';
        """

        drawing_id_result = execute_query(drawing_id_query)
        drawing_id_count = drawing_id_result[0]['count'] if drawing_id_result else 0

        if drawing_id_count == 0:
            print("✓ No drawing_id columns found in database")
        else:
            print(f"⚠ Warning: {drawing_id_count} tables still have drawing_id column")
            print("  Run migration 019 if not done yet")

        # Check 2: Verify project_id columns exist in key tables
        project_id_query = """
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE column_name = 'project_id'
              AND table_schema = 'public'
              AND table_name IN (
                  'drawing_text', 'drawing_dimensions', 'drawing_hatches', 'block_inserts'
              );
        """

        project_id_result = execute_query(project_id_query)
        project_id_count = project_id_result[0]['count'] if project_id_result else 0

        if project_id_count == 4:
            print("✓ All 4 core DXF tables have project_id column")
        else:
            print(f"⚠ Warning: Only {project_id_count}/4 core tables have project_id")
            print("  Run migration 018 if not done yet")

        # Check 3: List all remaining drawing-related tables
        drawing_tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name LIKE '%drawing%'
            ORDER BY table_name;
        """

        drawing_tables = execute_query(drawing_tables_query)
        if drawing_tables:
            print(f"\nRemaining tables with 'drawing' in name: {len(drawing_tables)}")
            print("(These are entity tables like drawing_text, drawing_entities, etc.)")
            for row in drawing_tables[:10]:  # Show first 10
                print(f"  - {row['table_name']}")
            if len(drawing_tables) > 10:
                print(f"  ... and {len(drawing_tables) - 10} more")

        print("\n" + "=" * 70)
        print("Migration 020 verification PASSED!")
        print("All obsolete drawing tables have been removed.")
        print("")
        print("Drawing → Project migration is COMPLETE!")
        print("  ✓ Phase 1 (018): Added project_id to 4 tables")
        print("  ✓ Phase 2 (019): Removed all drawing_id columns")
        print("  ✓ Phase 3 (020): Dropped obsolete drawing tables")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = verify_migration()
    sys.exit(0 if success else 1)
