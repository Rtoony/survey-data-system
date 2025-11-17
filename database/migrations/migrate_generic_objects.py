"""
Migrate existing generic_objects to standards_entities.
Run once to transition from old system to new classification-based system.

This script:
1. Checks if generic_objects table exists
2. Migrates any data to standards_entities with appropriate classification metadata
3. Marks the generic_objects table as deprecated (but doesn't delete it yet)
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()


def migrate_generic_objects():
    """Move generic_objects data to standards_entities"""
    conn = psycopg2.connect(
        host=os.getenv('PGHOST'),
        port=os.getenv('PGPORT'),
        database=os.getenv('PGDATABASE'),
        user=os.getenv('PGUSER'),
        password=os.getenv('PGPASSWORD')
    )

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Check if generic_objects exists and has data
        cur.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_name = 'generic_objects'
        """)
        table_exists = cur.fetchone()['count'] > 0

        if not table_exists:
            print("✓ generic_objects table doesn't exist - nothing to migrate")
            return

        cur.execute("SELECT COUNT(*) FROM generic_objects")
        count = cur.fetchone()['count']
        print(f"Found {count} records in generic_objects to migrate")

        if count == 0:
            print("✓ No records to migrate")
            return

        # Migrate each record
        cur.execute("""
            SELECT * FROM generic_objects
            WHERE review_status IN ('pending', 'approved', 'ignored')
        """)

        migrated = 0
        skipped = 0

        for obj in cur.fetchall():
            try:
                # Determine classification state from old review_status
                if obj['review_status'] == 'pending':
                    classification_state = 'needs_review'
                elif obj['review_status'] == 'approved':
                    classification_state = 'user_classified'
                else:  # ignored
                    classification_state = 'auto_classified'

                # Build classification metadata
                metadata = {
                    'suggested_type': obj.get('suggested_object_type'),
                    'original_layer': obj.get('original_layer_name'),
                    'migrated_from_generic_objects': True,
                    'migration_date': datetime.utcnow().isoformat(),
                    'old_review_status': obj['review_status']
                }

                # Create standards_entity record
                cur.execute("""
                    INSERT INTO standards_entities (
                        entity_id, entity_type, canonical_name, source_table, source_id,
                        project_id, classification_state, classification_confidence,
                        classification_metadata, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_table, source_id) DO UPDATE SET
                        classification_state = EXCLUDED.classification_state,
                        classification_confidence = EXCLUDED.classification_confidence,
                        classification_metadata = EXCLUDED.classification_metadata
                """, (
                    obj['object_id'],
                    obj.get('suggested_object_type', 'generic_object'),
                    f"Generic Object {obj['object_id'][:8]}",
                    'generic_objects',
                    obj['object_id'],
                    obj.get('project_id'),
                    classification_state,
                    obj.get('classification_confidence', 0.5),
                    json.dumps(metadata),
                    obj.get('created_at', datetime.utcnow())
                ))

                migrated += 1

            except Exception as e:
                print(f"Warning: Failed to migrate {obj['object_id']}: {e}")
                skipped += 1
                continue

        conn.commit()
        print(f"✓ Successfully migrated {migrated} records to standards_entities")
        if skipped > 0:
            print(f"⚠ Skipped {skipped} records due to errors")

        # Add deprecation comment to table
        cur.execute("""
            COMMENT ON TABLE generic_objects IS
            'DEPRECATED: Use standards_entities with classification_state instead.
            This table is kept for historical reference only.
            All new objects should be created directly in their target tables
            with classification metadata in standards_entities.'
        """)
        conn.commit()

        print("✓ Marked generic_objects table as DEPRECATED")

    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Generic Objects Migration Script")
    print("=" * 60)
    migrate_generic_objects()
    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)
