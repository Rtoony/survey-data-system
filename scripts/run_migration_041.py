#!/usr/bin/env python3
"""
Run Migration 041: Create GraphRAG Supporting Tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
import psycopg2

def run_migration():
    """Run migration 041 to create GraphRAG tables"""
    migration_file = 'database/migrations/041_create_graphrag_tables.sql'

    print("=" * 80)
    print("Running Migration 041: Create GraphRAG Supporting Tables")
    print("=" * 80)

    # Read the migration SQL
    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    try:
        with get_db() as conn:
            # Disable autocommit for migration
            conn.autocommit = False

            with conn.cursor() as cur:
                print("\n✓ Connected to database")
                print("✓ Executing migration SQL...")

                # Execute the migration
                cur.execute(migration_sql)

                # Commit the transaction
                conn.commit()
                print("✓ Migration committed successfully")

                # Verify tables were created
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name IN (
                          'embedding_jobs',
                          'ai_query_cache',
                          'quality_history',
                          'ai_query_history',
                          'graph_analytics_cache',
                          'semantic_similarity_cache'
                      )
                    ORDER BY table_name
                """)

                tables = [row[0] for row in cur.fetchall()]

                print(f"\n✓ Created {len(tables)}/6 tables:")
                for table in tables:
                    print(f"  • {table}")

                if len(tables) == 6:
                    print("\n" + "=" * 80)
                    print("SUCCESS: Migration 041 completed successfully!")
                    print("=" * 80)
                    return True
                else:
                    print(f"\n⚠ WARNING: Expected 6 tables but found {len(tables)}")
                    return False

    except psycopg2.Error as e:
        print(f"\n✗ ERROR: Migration failed!")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: Unexpected error!")
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
