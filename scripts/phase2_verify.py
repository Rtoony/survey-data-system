#!/usr/bin/env python3
"""
Phase 2 - Verification Script

This script verifies that Phase 2 (Auto-Integration) was completed successfully by:
- Checking embedding queue infrastructure
- Testing auto-queue triggers
- Verifying hybrid search functionality
- Checking background worker compatibility
- Testing queue statistics functions

Usage:
    python scripts/phase2_verify.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()


class Phase2Verifier:
    """Verify Phase 2 implementation."""

    def __init__(self):
        # Connect to database
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST') or os.getenv('DB_HOST'),
            port=int(os.getenv('PGPORT') or os.getenv('DB_PORT', 5432)),
            database=os.getenv('PGDATABASE') or os.getenv('DB_NAME'),
            user=os.getenv('PGUSER') or os.getenv('DB_USER'),
            password=os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
            sslmode='require'
        )

    def check_queue_table(self):
        """Check if embedding_generation_queue table exists with correct schema."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'embedding_generation_queue'
            ) as exists
        """)

        exists = cursor.fetchone()['exists']
        if not exists:
            cursor.close()
            return {'exists': False}

        # Check columns
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'embedding_generation_queue'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()

        # Check indexes
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'embedding_generation_queue'
        """)

        indexes = cursor.fetchall()

        # Check constraints
        cursor.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'embedding_generation_queue'
        """)

        constraints = cursor.fetchall()

        cursor.close()

        return {
            'exists': True,
            'columns': columns,
            'indexes': indexes,
            'constraints': constraints
        }

    def check_triggers(self):
        """Check if auto-embedding triggers are installed."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                trigger_name,
                event_object_table as table_name,
                action_timing,
                event_manipulation
            FROM information_schema.triggers
            WHERE trigger_name LIKE '%embedding_queue%'
               OR trigger_name LIKE '%trigger_queue_embedding%'
            ORDER BY event_object_table
        """)

        triggers = cursor.fetchall()

        # Check if trigger function exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname = 'trigger_queue_embedding'
                  AND n.nspname = 'public'
            ) as exists
        """)

        function_exists = cursor.fetchone()['exists']

        cursor.close()

        return {
            'triggers': triggers,
            'function_exists': function_exists
        }

    def test_auto_queue_trigger(self):
        """Test that triggers actually queue embeddings when entities are created."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Create a test layer
            cursor.execute("""
                INSERT INTO layer_standards (name, description, category)
                VALUES ('TEST-PHASE2-VERIFY', 'Test automatic queue trigger', 'test')
                RETURNING layer_id, entity_id
            """)

            result = cursor.fetchone()
            test_layer_id = result['layer_id']
            test_entity_id = result['entity_id']

            # Check if it was queued
            cursor.execute("""
                SELECT *
                FROM embedding_generation_queue
                WHERE entity_id = %s
            """, (test_entity_id,))

            queued = cursor.fetchone()

            # Cleanup
            cursor.execute("""
                DELETE FROM embedding_generation_queue WHERE entity_id = %s
            """, (test_entity_id,))

            cursor.execute("""
                DELETE FROM layer_standards WHERE layer_id = %s
            """, (test_layer_id,))

            self.conn.commit()
            cursor.close()

            return {
                'success': queued is not None,
                'queued_item': queued
            }

        except Exception as e:
            self.conn.rollback()
            cursor.close()
            return {
                'success': False,
                'error': str(e)
            }

    def check_queue_stats(self):
        """Check queue statistics and current state."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # Check if get_queue_stats function exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname = 'get_queue_stats'
                  AND n.nspname = 'public'
            ) as exists
        """)

        function_exists = cursor.fetchone()['exists']

        if not function_exists:
            cursor.close()
            return {'function_exists': False}

        # Get queue stats
        cursor.execute("SELECT * FROM get_queue_stats()")
        stats = cursor.fetchall()

        # Get total counts
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'processing') as processing,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE priority = 'high') as high_priority
            FROM embedding_generation_queue
        """)

        totals = cursor.fetchone()

        cursor.close()

        return {
            'function_exists': True,
            'stats': stats,
            'totals': totals
        }

    def test_hybrid_search(self):
        """Test hybrid search function."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # Check if hybrid_search function exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname = 'hybrid_search'
                  AND n.nspname = 'public'
            ) as exists
        """)

        function_exists = cursor.fetchone()['exists']

        if not function_exists:
            cursor.close()
            return {'function_exists': False}

        # Test the function
        try:
            cursor.execute("""
                SELECT *
                FROM hybrid_search('storm', 5)
                LIMIT 5
            """)

            results = cursor.fetchall()
            cursor.close()

            return {
                'function_exists': True,
                'success': True,
                'result_count': len(results),
                'sample_results': results[:3] if results else []
            }

        except Exception as e:
            cursor.close()
            return {
                'function_exists': True,
                'success': False,
                'error': str(e)
            }

    def check_quality_score_triggers(self):
        """Check if quality score auto-update triggers exist."""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                trigger_name,
                event_object_table as table_name
            FROM information_schema.triggers
            WHERE trigger_name LIKE '%quality_score%'
               OR trigger_name LIKE '%update_quality%'
            ORDER BY event_object_table
        """)

        triggers = cursor.fetchall()

        # Check if update function exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE p.proname LIKE '%quality%'
                  AND n.nspname = 'public'
            ) as exists
        """)

        function_exists = cursor.fetchone()['exists']

        cursor.close()

        return {
            'triggers': triggers,
            'function_exists': function_exists
        }

    def check_worker_prerequisites(self):
        """Check if environment is ready for background worker."""
        checks = {
            'openai_key': bool(os.getenv('OPENAI_API_KEY')),
            'database_url': bool(os.getenv('DATABASE_URL') or os.getenv('PGHOST')),
            'worker_script_exists': os.path.exists('workers/embedding_worker.py'),
            'python_packages': True  # Will check imports
        }

        # Try importing required packages
        try:
            import openai
            checks['openai_installed'] = True
        except ImportError:
            checks['openai_installed'] = False
            checks['python_packages'] = False

        try:
            import psycopg2
            checks['psycopg2_installed'] = True
        except ImportError:
            checks['psycopg2_installed'] = False
            checks['python_packages'] = False

        return checks

    def run(self):
        """Run all verification checks."""
        print('=' * 70)
        print('PHASE 2 VERIFICATION')
        print('=' * 70)
        print()

        success = True

        # Check 1: Queue Table
        print('1. Checking Embedding Queue Table...')
        print('-' * 70)
        queue = self.check_queue_table()

        if not queue['exists']:
            print('  ✗ QUEUE TABLE NOT FOUND!')
            print('  Run: psql "$DATABASE_URL" < database/migrations/phase2_01_embedding_queue.sql')
            success = False
        else:
            print(f'  ✓ Table exists with {len(queue["columns"])} columns')
            print(f'  ✓ {len(queue["indexes"])} indexes')
            print(f'  ✓ {len(queue["constraints"])} constraints')

        print()

        # Check 2: Triggers
        print('2. Checking Auto-Queue Triggers...')
        print('-' * 70)
        triggers = self.check_triggers()

        if not triggers['function_exists']:
            print('  ✗ TRIGGER FUNCTION NOT FOUND!')
            success = False
        else:
            print('  ✓ trigger_queue_embedding() function exists')

        if len(triggers['triggers']) == 0:
            print('  ⚠️  NO TRIGGERS FOUND')
            print('  Expected triggers on: layer_standards, block_definitions, detail_standards')
            success = False
        else:
            print(f'  ✓ Found {len(triggers["triggers"])} triggers:')
            for trigger in triggers['triggers']:
                print(f'    - {trigger["table_name"]}: {trigger["trigger_name"]}')

        print()

        # Check 3: Test Auto-Queue
        print('3. Testing Auto-Queue Trigger...')
        print('-' * 70)
        test_result = self.test_auto_queue_trigger()

        if test_result['success']:
            print('  ✓ Trigger successfully queued test entity')
            print(f'    Priority: {test_result["queued_item"]["priority"]}')
            print(f'    Status: {test_result["queued_item"]["status"]}')
        else:
            print(f'  ✗ TRIGGER TEST FAILED: {test_result.get("error", "Unknown error")}')
            success = False

        print()

        # Check 4: Queue Statistics
        print('4. Checking Queue Statistics...')
        print('-' * 70)
        stats = self.check_queue_stats()

        if not stats['function_exists']:
            print('  ✗ get_queue_stats() function not found')
            success = False
        else:
            print('  ✓ get_queue_stats() function exists')
            print()
            print('  Current queue state:')
            totals = stats['totals']
            print(f'    Total items: {totals["total"]:,}')
            print(f'    Pending: {totals["pending"]:,}')
            print(f'    Processing: {totals["processing"]:,}')
            print(f'    Completed: {totals["completed"]:,}')
            print(f'    Failed: {totals["failed"]:,}')
            print(f'    High priority: {totals["high_priority"]:,}')

        print()

        # Check 5: Hybrid Search
        print('5. Testing Hybrid Search...')
        print('-' * 70)
        hybrid = self.test_hybrid_search()

        if not hybrid['function_exists']:
            print('  ✗ HYBRID_SEARCH FUNCTION NOT FOUND!')
            print('  This should have been created in Phase 1')
            success = False
        elif not hybrid['success']:
            print(f'  ✗ Hybrid search failed: {hybrid.get("error", "Unknown error")}')
            success = False
        else:
            print(f'  ✓ Hybrid search working')
            print(f'  ✓ Found {hybrid["result_count"]} results for test query')
            if hybrid['sample_results']:
                print('  Sample results:')
                for r in hybrid['sample_results']:
                    print(f'    - {r["canonical_name"]} (score: {r["combined_score"]:.2%})')

        print()

        # Check 6: Quality Score Triggers
        print('6. Checking Quality Score Auto-Update...')
        print('-' * 70)
        quality = self.check_quality_score_triggers()

        if quality['function_exists']:
            print('  ✓ Quality score function exists')
        else:
            print('  ⚠️  Quality score function not found (optional)')

        if len(quality['triggers']) > 0:
            print(f'  ✓ Found {len(quality["triggers"])} quality score triggers')
        else:
            print('  ⚠️  No quality score triggers (optional)')

        print()

        # Check 7: Worker Prerequisites
        print('7. Checking Background Worker Prerequisites...')
        print('-' * 70)
        worker = self.check_worker_prerequisites()

        if worker['openai_key']:
            print('  ✓ OPENAI_API_KEY is set')
        else:
            print('  ✗ OPENAI_API_KEY not found in environment')
            print('  Set in .env file: OPENAI_API_KEY=sk-...')
            success = False

        if worker['database_url']:
            print('  ✓ Database credentials found')
        else:
            print('  ✗ Database credentials not found')
            success = False

        if worker['worker_script_exists']:
            print('  ✓ workers/embedding_worker.py exists')
        else:
            print('  ✗ workers/embedding_worker.py not found')
            success = False

        if worker['openai_installed']:
            print('  ✓ openai package installed')
        else:
            print('  ✗ openai package not installed')
            print('  Install: pip install openai')
            success = False

        if worker['psycopg2_installed']:
            print('  ✓ psycopg2 package installed')
        else:
            print('  ✗ psycopg2 package not installed')
            print('  Install: pip install psycopg2-binary')
            success = False

        print()
        print('=' * 70)
        print('PHASE 2 VERIFICATION COMPLETE')
        print('=' * 70)
        print()

        # Success criteria
        print('Success Criteria:')

        if queue['exists']:
            print('  ✓ Embedding queue infrastructure created')
        else:
            print('  ✗ Embedding queue infrastructure missing')

        if triggers['function_exists'] and len(triggers['triggers']) > 0:
            print('  ✓ Auto-queue triggers functional')
        else:
            print('  ✗ Auto-queue triggers not working')

        if hybrid.get('function_exists') and hybrid.get('success'):
            print('  ✓ Hybrid search functional')
        else:
            print('  ✗ Hybrid search not working')

        if worker['python_packages'] and worker['worker_script_exists']:
            print('  ✓ Worker prerequisites met')
        else:
            print('  ✗ Worker prerequisites missing')

        print()

        if success:
            print('🎉 PHASE 2 SUCCESSFUL!')
            print()
            print('You now have:')
            print('  - ✓ Automatic embedding generation queue')
            print('  - ✓ Auto-queue triggers on entity creation')
            print('  - ✓ Hybrid search combining text + AI + quality')
            print('  - ✓ Background worker ready to run')
            print()
            print('Next steps:')
            print('  1. Start background worker:')
            print('     python workers/embedding_worker.py --batch-size 50')
            print()
            print('  2. Integrate with UI (see PHASE2_INTEGRATION_GUIDE.md)')
            print()
            print('  3. Test DXF import auto-queueing')
            print()
            print('  4. Proceed to Phase 3 (user-facing features)')
        else:
            print('⚠️  Phase 2 incomplete. Please address issues above.')

        return success


def main():
    try:
        verifier = Phase2Verifier()
        success = verifier.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
