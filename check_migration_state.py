#!/usr/bin/env python3
"""
Check the current state of the database for project_id and drawing_id columns.
This helps us understand what migrations have been run and what still needs to be done.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.db_utils import execute_query

def check_migration_state():
    """Check which tables have project_id and drawing_id columns."""

    print("=" * 80)
    print("DATABASE MIGRATION STATE CHECK")
    print("=" * 80)

    # Check for project_id columns
    print("\n1. Tables with project_id column:")
    print("-" * 80)
    project_id_query = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE column_name = 'project_id'
          AND table_schema = 'public'
          AND table_name NOT LIKE 'pg_%'
        ORDER BY table_name;
    """

    try:
        project_id_results = execute_query(project_id_query)
        if project_id_results:
            print(f"{'Table Name':<30} {'Column':<15} {'Type':<10} {'Nullable':<10}")
            print("-" * 80)
            for row in project_id_results:
                print(f"{row['table_name']:<30} {row['column_name']:<15} {row['data_type']:<10} {row['is_nullable']:<10}")
            print(f"\nTotal tables with project_id: {len(project_id_results)}")
        else:
            print("No tables with project_id found!")
    except Exception as e:
        print(f"Error querying project_id: {e}")

    # Check for drawing_id columns
    print("\n2. Tables with drawing_id column:")
    print("-" * 80)
    drawing_id_query = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE column_name = 'drawing_id'
          AND table_schema = 'public'
          AND table_name NOT LIKE 'pg_%'
        ORDER BY table_name;
    """

    try:
        drawing_id_results = execute_query(drawing_id_query)
        if drawing_id_results:
            print(f"{'Table Name':<30} {'Column':<15} {'Type':<10} {'Nullable':<10}")
            print("-" * 80)
            for row in drawing_id_results:
                print(f"{row['table_name']:<30} {row['column_name']:<15} {row['data_type']:<10} {row['is_nullable']:<10}")
            print(f"\nTotal tables with drawing_id: {len(drawing_id_results)}")
        else:
            print("✓ No tables with drawing_id found (migration complete!)")
    except Exception as e:
        print(f"Error querying drawing_id: {e}")

    # Check specific Phase 1 tables
    print("\n3. Phase 1 Target Tables Status (should have project_id):")
    print("-" * 80)
    phase1_tables = ['drawing_text', 'drawing_dimensions', 'drawing_hatches', 'block_inserts']

    for table in phase1_tables:
        has_project_id_query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}' AND column_name = 'project_id';
        """
        has_drawing_id_query = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table}' AND column_name = 'drawing_id';
        """

        try:
            has_project_id = execute_query(has_project_id_query)
            has_drawing_id = execute_query(has_drawing_id_query)

            project_id_status = "✓ YES" if has_project_id else "✗ NO"
            drawing_id_status = "✓ YES" if has_drawing_id else "✗ NO"

            print(f"{table:<30} project_id: {project_id_status:<10} drawing_id: {drawing_id_status:<10}")
        except Exception as e:
            print(f"{table:<30} Error: {e}")

    # Check if obsolete drawing tables still exist
    print("\n4. Obsolete Drawing Tables (should be dropped in Phase 3):")
    print("-" * 80)
    obsolete_tables = ['drawing_materials', 'drawing_references', 'drawings']

    for table in obsolete_tables:
        check_table_query = f"""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name = '{table}' AND table_schema = 'public';
        """

        try:
            exists = execute_query(check_table_query)
            status = "EXISTS (needs deletion)" if exists else "✓ DROPPED"
            print(f"{table:<30} {status}")
        except Exception as e:
            print(f"{table:<30} Error: {e}")

    print("\n" + "=" * 80)
    print("END OF MIGRATION STATE CHECK")
    print("=" * 80)

if __name__ == '__main__':
    try:
        check_migration_state()
    except Exception as e:
        print(f"\n✗ Error checking migration state: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
