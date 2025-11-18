#!/usr/bin/env python3
"""
Verification script for migration 019: Remove all drawing_id columns
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.db_utils import execute_query

def verify_migration():
    """Verify that all drawing_id columns have been removed."""
    print("Verifying migration 019: Remove all drawing_id columns...")
    print("-" * 70)

    # Query to check if any drawing_id columns still exist
    query = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE column_name = 'drawing_id'
          AND table_schema = 'public'
          AND table_name NOT LIKE 'pg_%'
        ORDER BY table_name;
    """

    try:
        results = execute_query(query)

        if results and len(results) > 0:
            print("❌ FAILED: drawing_id columns still exist in the database!")
            print("\nTables with drawing_id column:")
            print(f"{'Table Name':<30} {'Column':<15} {'Type':<10} {'Nullable':<10}")
            print("-" * 70)
            for row in results:
                print(f"{row['table_name']:<30} {row['column_name']:<15} {row['data_type']:<10} {row['is_nullable']:<10}")
            print(f"\nTotal tables with drawing_id: {len(results)}")
            print("\nAction required: These tables still have drawing_id columns.")
            print("Run migration 019 to remove them.")
            return False

        # Success - no drawing_id columns found
        print("✅ SUCCESS: No drawing_id columns found in database!\n")
        print("All tables have been successfully migrated to use project_id exclusively.")

        # Also verify that project_id columns exist where expected
        print("\n" + "-" * 70)
        print("Additional check: Verifying project_id columns exist...")
        print("-" * 70)

        project_id_query = """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE column_name = 'project_id'
              AND table_schema = 'public'
              AND table_name IN (
                  'drawing_text', 'drawing_dimensions', 'drawing_hatches', 'block_inserts',
                  'drawing_entities', 'layers', 'dxf_entity_links'
              )
            ORDER BY table_name;
        """

        project_id_results = execute_query(project_id_query)

        if project_id_results:
            print(f"\nTables with project_id column (core DXF tables):")
            print(f"{'Table Name':<30} {'Column':<15}")
            print("-" * 50)
            for row in project_id_results:
                print(f"{row['table_name']:<30} {row['column_name']:<15}")
            print(f"\n✓ Found project_id in {len(project_id_results)} core tables")
        else:
            print("\n⚠ Warning: No project_id columns found in core DXF tables!")
            print("You may need to run migration 018 first.")

        print("\n" + "=" * 70)
        print("Migration 019 verification PASSED!")
        print("All drawing_id columns have been removed.")
        print("Database now uses project_id exclusively.")
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
