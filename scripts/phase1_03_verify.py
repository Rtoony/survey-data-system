#!/usr/bin/env python3
"""
Phase 1 - Task 3: Verify Implementation

This script verifies that Phase 1 was completed successfully by:
- Checking embedding counts
- Testing similarity search
- Verifying relationships
- Testing database functions

Usage:
    python scripts/phase1_03_verify.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()


class Phase1Verifier:
    """Verify Phase 1 implementation."""

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

    def check_embeddings(self):
        """Check embedding counts."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT entity_id) as unique_entities,
                COUNT(*) FILTER (WHERE is_current = TRUE) as current,
                AVG(array_length(embedding::real[], 1)) as avg_dimensions
            FROM entity_embeddings
        """)

        total, unique, current, avg_dim = cursor.fetchone()

        cursor.execute("""
            SELECT
                em.model_name,
                COUNT(*) as count
            FROM entity_embeddings ee
            JOIN embedding_models em ON ee.model_id = em.model_id
            WHERE ee.is_current = TRUE
            GROUP BY em.model_name
        """)

        by_model = cursor.fetchall()

        cursor.close()

        return {
            'total': total,
            'unique_entities': unique,
            'current': current,
            'avg_dimensions': avg_dim,
            'by_model': by_model
        }

    def check_relationships(self):
        """Check relationship counts."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                relationship_type,
                predicate,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence
            FROM entity_relationships
            GROUP BY relationship_type, predicate
            ORDER BY count DESC
        """)

        by_type = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(DISTINCT subject_entity_id) as entities_with_outbound
            FROM entity_relationships
        """)

        entities_with_out = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT object_entity_id) as entities_with_inbound
            FROM entity_relationships
        """)

        entities_with_in = cursor.fetchone()[0]

        cursor.close()

        return {
            'by_type': by_type,
            'entities_with_outbound': entities_with_out,
            'entities_with_inbound': entities_with_in
        }

    def test_similarity_search(self):
        """Test the find_similar_entities() function."""
        cursor = self.conn.cursor()

        # Get a random entity with an embedding
        cursor.execute("""
            SELECT
                se.entity_id,
                se.canonical_name
            FROM standards_entities se
            WHERE EXISTS (
                SELECT 1 FROM entity_embeddings ee
                WHERE ee.entity_id = se.entity_id
                  AND ee.is_current = TRUE
            )
            LIMIT 1
        """)

        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None

        test_entity_id, test_entity_name = result

        # Test similarity search
        cursor.execute("""
            SELECT
                entity_id,
                canonical_name,
                entity_type,
                similarity_score
            FROM find_similar_entities(%s::uuid, 0.70, 5)
        """, (test_entity_id,))

        similar = cursor.fetchall()
        cursor.close()

        return {
            'test_entity_id': test_entity_id,
            'test_entity_name': test_entity_name,
            'similar_count': len(similar),
            'similar_entities': similar
        }

    def test_graph_traversal(self):
        """Test the find_related_entities() function."""
        cursor = self.conn.cursor()

        # Get an entity with relationships
        cursor.execute("""
            SELECT
                se.entity_id,
                se.canonical_name
            FROM standards_entities se
            WHERE EXISTS (
                SELECT 1 FROM entity_relationships er
                WHERE er.subject_entity_id = se.entity_id
                   OR er.object_entity_id = se.entity_id
            )
            LIMIT 1
        """)

        result = cursor.fetchone()
        if not result:
            cursor.close()
            return None

        test_entity_id, test_entity_name = result

        # Test graph traversal
        cursor.execute("""
            SELECT
                entity_id,
                canonical_name,
                entity_type,
                hop_distance,
                relationship_path
            FROM find_related_entities(%s::uuid, 2, NULL)
        """, (test_entity_id,))

        related = cursor.fetchall()
        cursor.close()

        return {
            'test_entity_id': test_entity_id,
            'test_entity_name': test_entity_name,
            'related_count': len(related),
            'related_entities': related
        }

    def check_quality_scores(self):
        """Check quality score distribution."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                CASE
                    WHEN quality_score < 0.25 THEN '0-25%'
                    WHEN quality_score < 0.50 THEN '25-50%'
                    WHEN quality_score < 0.75 THEN '50-75%'
                    ELSE '75-100%'
                END as range,
                COUNT(*) as count,
                AVG(quality_score) as avg_score
            FROM standards_entities
            WHERE quality_score IS NOT NULL
            GROUP BY range
            ORDER BY range
        """)

        distribution = cursor.fetchall()

        cursor.execute("""
            SELECT AVG(quality_score) as overall_avg
            FROM standards_entities
            WHERE quality_score IS NOT NULL
        """)

        overall_avg = cursor.fetchone()[0]

        cursor.close()

        return {
            'distribution': distribution,
            'overall_avg': overall_avg
        }

    def run(self):
        """Run all verification checks."""
        print('=' * 70)
        print('PHASE 1 VERIFICATION')
        print('=' * 70)
        print()

        # Check embeddings
        print('1. Checking Embeddings...')
        print('-' * 70)
        emb = self.check_embeddings()
        print(f'  Total embeddings: {emb["total"]:,}')
        print(f'  Unique entities: {emb["unique_entities"]:,}')
        print(f'  Current embeddings: {emb["current"]:,}')
        print(f'  Avg dimensions: {emb["avg_dimensions"]:.0f}')
        print()
        print('  By model:')
        for model_name, count in emb['by_model']:
            print(f'    {model_name}: {count:,}')

        if emb['current'] == 0:
            print()
            print('  ✗ NO EMBEDDINGS FOUND!')
            print('  Run: python scripts/phase1_01_generate_embeddings.py')
            return False

        print()

        # Check relationships
        print('2. Checking Relationships...')
        print('-' * 70)
        rel = self.check_relationships()
        total_rel = sum(count for _, _, count, _ in rel['by_type'])
        print(f'  Total relationships: {total_rel:,}')
        print(f'  Entities with outbound: {rel["entities_with_outbound"]:,}')
        print(f'  Entities with inbound: {rel["entities_with_inbound"]:,}')
        print()
        print('  By type:')
        for rel_type, predicate, count, avg_conf in rel['by_type']:
            print(f'    {rel_type} ({predicate}): {count:,} (avg confidence: {avg_conf:.2%})')

        if total_rel == 0:
            print()
            print('  ⚠️  NO RELATIONSHIPS FOUND')
            print('  Run: python scripts/phase1_02_build_relationships.py')

        print()

        # Test similarity search
        print('3. Testing Similarity Search...')
        print('-' * 70)
        sim = self.test_similarity_search()
        if sim:
            print(f'  Test entity: {sim["test_entity_name"]}')
            print(f'  Similar entities found: {sim["similar_count"]}')
            print()
            if sim['similar_count'] > 0:
                print('  Top 3 similar:')
                for entity_id, name, entity_type, score in sim['similar_entities'][:3]:
                    print(f'    {name[:40]:40} ({score:.2%})')
                print()
                print('  ✓ Similarity search working!')
            else:
                print('  ⚠️  No similar entities found (threshold may be too high)')
        else:
            print('  ✗ No entities with embeddings found')

        print()

        # Test graph traversal
        print('4. Testing Graph Traversal (GraphRAG)...')
        print('-' * 70)
        graph = self.test_graph_traversal()
        if graph:
            print(f'  Test entity: {graph["test_entity_name"]}')
            print(f'  Related entities (2-hops): {graph["related_count"]}')
            print()
            if graph['related_count'] > 0:
                print('  Sample path:')
                for entity_id, name, entity_type, hops, path in graph['related_entities'][:3]:
                    print(f'    {name[:35]:35} ({hops} hops) via: {path}')
                print()
                print('  ✓ GraphRAG traversal working!')
            else:
                print('  ⚠️  No related entities found (need more relationships)')
        else:
            print('  ✗ No entities with relationships found')

        print()

        # Check quality scores
        print('5. Quality Score Distribution...')
        print('-' * 70)
        qual = self.check_quality_scores()
        print(f'  Overall average: {qual["overall_avg"]:.2%}')
        print()
        print('  Distribution:')
        for range_name, count, avg in qual['distribution']:
            bar = '█' * int(count / 10)
            print(f'    {range_name:10} {count:5,} {bar}')

        print()
        print('=' * 70)
        print('PHASE 1 VERIFICATION COMPLETE')
        print('=' * 70)
        print()

        # Success criteria
        success = True
        print('Success Criteria:')

        if emb['current'] >= 50:
            print('  ✓ At least 50 embeddings generated')
        else:
            print(f'  ✗ Only {emb["current"]} embeddings (target: 50+)')
            success = False

        if total_rel >= 100:
            print('  ✓ At least 100 relationships created')
        else:
            print(f'  ⚠️  Only {total_rel} relationships (target: 100+)')

        if sim and sim['similar_count'] > 0:
            print('  ✓ Similarity search functional')
        else:
            print('  ✗ Similarity search not working')
            success = False

        print()

        if success:
            print('🎉 PHASE 1 SUCCESSFUL!')
            print()
            print('You now have:')
            print(f'  - {emb["current"]:,} vector embeddings')
            print(f'  - {total_rel:,} semantic relationships')
            print('  - Working similarity search')
            print('  - GraphRAG multi-hop traversal')
            print()
            print('Next steps:')
            print('  - Add "Find Similar" UI (see game plan)')
            print('  - Proceed to Phase 2 (auto-integration)')
        else:
            print('⚠️  Phase 1 incomplete. Please address issues above.')

        return success


def main():
    try:
        verifier = Phase1Verifier()
        success = verifier.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f'\n✗ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
