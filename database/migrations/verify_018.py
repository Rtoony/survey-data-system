#!/usr/bin/env python3
"""
Verification script for migration 018: Add project_id columns to drawing tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.db_utils import execute_query

def verify_migration():
    """Verify that project_id columns were added to drawing tables."""
    print("Verifying migration 018: Add project_id columns to drawing tables...")
    print("-" * 70)

    # Query to check if project_id column exists in the three tables
    query = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name IN ('drawing_text', 'drawing_dimensions', 'drawing_hatches')
          AND column_name = 'project_id'
        ORDER BY table_name;
    """

    try:
        results = execute_query(query)

        if not results or len(results) == 0:
            print("❌ FAILED: No project_id columns found in any of the tables!")
            print("\nExpected to find project_id in:")
            print("  - drawing_text")
            print("  - drawing_dimensions")
            print("  - drawing_hatches")
            return False

        # Check that we have all three tables
        tables_found = {row['table_name'] for row in results}
        expected_tables = {'drawing_text', 'drawing_dimensions', 'drawing_hatches'}

        if tables_found != expected_tables:
            print(f"❌ FAILED: Not all tables have project_id column")
            print(f"\nTables with project_id: {tables_found}")
            print(f"Expected tables: {expected_tables}")
            print(f"Missing: {expected_tables - tables_found}")
            return False

        # Display results
        print("✅ SUCCESS: All three tables have project_id column\n")
        print(f"{'Table Name':<25} {'Column':<15} {'Data Type':<15} {'Nullable':<10}")
        print("-" * 70)
        for row in results:
            print(f"{row['table_name']:<25} {row['column_name']:<15} {row['data_type']:<15} {row['is_nullable']:<10}")

        print("\n" + "=" * 70)
        print("Migration 018 verification PASSED!")
        print("DXF imports should now work correctly.")
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
