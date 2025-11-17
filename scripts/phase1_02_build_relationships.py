#!/usr/bin/env python3
"""
Phase 1 - Task 2: Build Semantic Relationships

This script builds semantic relationships between entities using vector similarity.
It creates edges in the knowledge graph for GraphRAG queries.

Usage:
    python scripts/phase1_02_build_relationships.py [--threshold 0.75] [--limit 5]

Options:
    --threshold   Similarity threshold (0.0-1.0, default: 0.75)
    --limit       Max relationships per entity (default: 5)
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()


class RelationshipBuilder:
    """Build semantic relationships from embeddings."""

    def __init__(self, similarity_threshold=0.75, limit_per_entity=5):
        self.similarity_threshold = similarity_threshold
        self.limit_per_entity = limit_per_entity

        # Connect to database
        self.conn = psycopg2.connect(
            host=os.getenv('PGHOST') or os.getenv('DB_HOST'),
            port=int(os.getenv('PGPORT') or os.getenv('DB_PORT', 5432)),
            database=os.getenv('PGDATABASE') or os.getenv('DB_NAME'),
            user=os.getenv('PGUSER') or os.getenv('DB_USER'),
            password=os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
            sslmode='require'
        )

    def find_similar_pairs(self):
        """Find pairs of similar entities based on embeddings."""
        cursor = self.conn.cursor()

        print('Finding similar entity pairs...')

        cursor.execute("""
            WITH entity_embeddings_current AS (
                SELECT entity_id, embedding
                FROM entity_embeddings
                WHERE is_current = TRUE
            ),
            similarity_pairs AS (
                SELECT
                    e1.entity_id as subject_id,
                    e2.entity_id as object_id,
                    1 - (e1.embedding <=> e2.embedding) as similarity
                FROM entity_embeddings_current e1
                CROSS JOIN entity_embeddings_current e2
                WHERE e1.entity_id < e2.entity_id  -- Avoid duplicates and self-pairs
                  AND 1 - (e1.embedding <=> e2.embedding) >= %s
            ),
            ranked_pairs AS (
                SELECT
                    subject_id,
                    object_id,
                    similarity,
                    ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY similarity DESC) as rank1,
                    ROW_NUMBER() OVER (PARTITION BY object_id ORDER BY similarity DESC) as rank2
                FROM similarity_pairs
            )
            SELECT subject_id, object_id, similarity
            FROM ranked_pairs
            WHERE rank1 <= %s OR rank2 <= %s
            ORDER BY similarity DESC
        """, (self.similarity_threshold, self.limit_per_entity, self.limit_per_entity))

        pairs = cursor.fetchall()
        cursor.close()

        return pairs

    def create_relationship(self, subject_id, object_id, similarity):
        """Create a bidirectional semantic relationship."""
        cursor = self.conn.cursor()

        # Create relationship: subject → object
        cursor.execute("""
            INSERT INTO entity_relationships (
                subject_entity_id,
                predicate,
                object_entity_id,
                relationship_type,
                confidence_score,
                semantic_relationship,
                ai_generated,
                attributes
            ) VALUES (
                %s, 'similar_to', %s, 'semantic', %s, TRUE, TRUE,
                jsonb_build_object('similarity_score', %s, 'created_by', 'phase1_script')
            )
            ON CONFLICT (subject_entity_id, predicate, object_entity_id)
            DO UPDATE SET
                confidence_score = EXCLUDED.confidence_score,
                attributes = EXCLUDED.attributes
        """, (subject_id, object_id, similarity, similarity))

        # Create reverse relationship: object → subject
        cursor.execute("""
            INSERT INTO entity_relationships (
                subject_entity_id,
                predicate,
                object_entity_id,
                relationship_type,
                confidence_score,
                semantic_relationship,
                ai_generated,
                attributes
            ) VALUES (
                %s, 'similar_to', %s, 'semantic', %s, TRUE, TRUE,
                jsonb_build_object('similarity_score', %s, 'created_by', 'phase1_script')
            )
            ON CONFLICT (subject_entity_id, predicate, object_entity_id)
            DO UPDATE SET
                confidence_score = EXCLUDED.confidence_score,
                attributes = EXCLUDED.attributes
        """, (object_id, subject_id, similarity, similarity))

        self.conn.commit()
        cursor.close()

    def run(self):
        """Build semantic relationships."""
        print('=' * 70)
        print('PHASE 1 - TASK 2: BUILD SEMANTIC RELATIONSHIPS')
        print('=' * 70)
        print()

        print('Configuration:')
        print(f'  Similarity threshold: {self.similarity_threshold:.2f} ({self.similarity_threshold * 100:.0f}%)')
        print(f'  Max relationships per entity: {self.limit_per_entity}')
        print()

        # Find similar pairs
        pairs = self.find_similar_pairs()
        print(f'✓ Found {len(pairs)} similar entity pairs')
        print()

        if len(pairs) == 0:
            print('No similar pairs found. Try lowering the threshold.')
            print('Current threshold: {:.2f}'.format(self.similarity_threshold))
            print('Suggested: --threshold 0.70')
            return

        # Show sample pairs
        print('Sample similarity pairs:')
        print('-' * 70)
        cursor = self.conn.cursor()
        for subject_id, object_id, similarity in pairs[:5]:
            cursor.execute("""
                SELECT
                    (SELECT canonical_name FROM standards_entities WHERE entity_id = %s) as subject,
                    (SELECT canonical_name FROM standards_entities WHERE entity_id = %s) as object
            """, (subject_id, object_id))
            subject, obj = cursor.fetchone()
            print(f'  {subject[:30]:30} ↔ {obj[:30]:30} ({similarity:.2%})')
        cursor.close()
        print()

        # Confirm
        response = input(f'Create {len(pairs)} relationship pairs? (yes/no): ')
        if response.lower() != 'yes':
            print('Cancelled.')
            return

        print()
        print('Creating relationships...')
        print('-' * 70)

        # Create relationships
        created = 0
        failed = 0

        for i, (subject_id, object_id, similarity) in enumerate(pairs, 1):
            try:
                self.create_relationship(subject_id, object_id, similarity)
                created += 1

                if i % 20 == 0:
                    print(f'  [{i}/{len(pairs)}] Created {created} relationship pairs...')

            except Exception as e:
                print(f'  ✗ Failed to create relationship: {e}')
                failed += 1

        print()
        print('=' * 70)
        print('RESULTS:')
        print('=' * 70)
        print(f'  ✓ Created: {created} relationship pairs')
        print(f'  ✗ Failed: {failed}')
        print(f'  Total edges: {created * 2} (bidirectional)')
        print()
        print('✓ Phase 1 - Task 2 Complete!')
        print()
        print('Next steps:')
        print('  - Verify: python scripts/phase1_03_verify.py')
        print('  - Test similarity search in database')


def main():
    parser = argparse.ArgumentParser(description='Build semantic relationships')
    parser.add_argument('--threshold', type=float, default=0.75,
                        help='Similarity threshold (0.0-1.0)')
    parser.add_argument('--limit', type=int, default=5,
                        help='Max relationships per entity')

    args = parser.parse_args()

    if not (0.0 <= args.threshold <= 1.0):
        print('Error: --threshold must be between 0.0 and 1.0')
        sys.exit(1)

    try:
        builder = RelationshipBuilder(
            similarity_threshold=args.threshold,
            limit_per_entity=args.limit
        )
        builder.run()
    except KeyboardInterrupt:
        print('\n\nCancelled by user.')
        sys.exit(1)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
