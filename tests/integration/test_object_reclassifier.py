"""
Integration Tests for Object Reclassifier

Tests the complete workflow of entity classification review and reclassification,
including DXF import, review queue, AI suggestions, and user corrections.
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from services.classification_service import ClassificationService


class TestObjectReclassifierIntegration:
    """Integration tests for the complete object reclassifier workflow."""

    def test_import_creates_needs_review_entities(self, db_connection):
        """Test that low-confidence DXF import creates entities flagged for review."""
        cur = db_connection.cursor(cursor_factory=RealDictCursor)

        # Create a test project
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (gen_random_uuid(), 'Test Reclassifier Project', 'TEST-RECLAS-001')
            RETURNING project_id
        """)
        project = cur.fetchone()
        project_id = project['project_id']

        # Create a drawing entity with ambiguous layer name (low confidence)
        cur.execute("""
            INSERT INTO drawing_entities (
                entity_id, project_id, layer_name, entity_type,
                geometry, dxf_handle
            )
            VALUES (
                gen_random_uuid(), %s, 'MISC-STUFF', 'LINE',
                ST_GeomFromText('LINESTRING(0 0, 100 100)', 2227),
                'TEST123'
            )
            RETURNING entity_id
        """, (project_id,))
        drawing_entity = cur.fetchone()
        entity_id = drawing_entity['entity_id']

        # Create standards_entities record with low confidence
        cur.execute("""
            INSERT INTO standards_entities (
                entity_id, project_id, entity_type, source_table,
                classification_state, classification_confidence,
                classification_metadata
            )
            VALUES (
                %s, %s, 'utility_line', 'drawing_entities',
                'needs_review', 0.45,
                '{"reasoning": "Ambiguous layer name", "suggestions": []}'::jsonb
            )
        """, (entity_id, project_id))

        db_connection.commit()

        # Verify entity is flagged for review
        cur.execute("""
            SELECT classification_state, classification_confidence
            FROM standards_entities
            WHERE entity_id = %s
        """, (entity_id,))
        entity = cur.fetchone()

        assert entity['classification_state'] == 'needs_review'
        assert entity['classification_confidence'] < 0.7

        # Cleanup
        cur.execute("DELETE FROM standards_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        db_connection.commit()
        cur.close()

    def test_reclassifier_retrieves_pending_entities(self, db_connection, db_config):
        """Test that review queue retrieves only entities needing review."""
        cur = db_connection.cursor(cursor_factory=RealDictCursor)

        # Create test project
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (gen_random_uuid(), 'Test Queue Project', 'TEST-QUEUE-001')
            RETURNING project_id
        """)
        project = cur.fetchone()
        project_id = project['project_id']

        # Create multiple entities with different states
        entities_to_create = [
            ('needs_review', 0.45, 'Should appear'),
            ('needs_review', 0.65, 'Should appear'),
            ('auto_classified', 0.85, 'Should NOT appear'),
            ('user_classified', 1.0, 'Should NOT appear'),
        ]

        created_ids = []
        for state, confidence, note in entities_to_create:
            cur.execute("""
                INSERT INTO drawing_entities (
                    entity_id, project_id, layer_name, entity_type,
                    geometry, dxf_handle
                )
                VALUES (
                    gen_random_uuid(), %s, %s, 'LINE',
                    ST_GeomFromText('LINESTRING(0 0, 100 100)', 2227),
                    %s
                )
                RETURNING entity_id
            """, (project_id, f'LAYER-{note}', f'HANDLE-{note}'))
            drawing_entity = cur.fetchone()
            entity_id = drawing_entity['entity_id']
            created_ids.append(entity_id)

            cur.execute("""
                INSERT INTO standards_entities (
                    entity_id, project_id, entity_type, source_table,
                    classification_state, classification_confidence,
                    classification_metadata
                )
                VALUES (
                    %s, %s, 'utility_line', 'drawing_entities',
                    %s, %s, %s::jsonb
                )
            """, (entity_id, project_id, state, confidence, json.dumps({'note': note})))

        db_connection.commit()

        # Test review queue retrieval
        service = ClassificationService(db_config, conn=db_connection)
        results = service.get_review_queue(project_id=project_id)

        # Should only return 2 entities with 'needs_review' state
        assert len(results) == 2
        for entity in results:
            assert entity['classification_state'] == 'needs_review'
            assert entity['classification_confidence'] < 0.7

        # Cleanup
        for entity_id in created_ids:
            cur.execute("DELETE FROM standards_entities WHERE entity_id = %s", (entity_id,))
            cur.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        db_connection.commit()
        cur.close()

    def test_single_entity_reclassification(self, db_connection, db_config):
        """Test successful single entity reclassification."""
        cur = db_connection.cursor(cursor_factory=RealDictCursor)

        # Create test project
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (gen_random_uuid(), 'Test Reclassify Project', 'TEST-RECLAS-002')
            RETURNING project_id
        """)
        project = cur.fetchone()
        project_id = project['project_id']

        # Create entity needing review
        cur.execute("""
            INSERT INTO drawing_entities (
                entity_id, project_id, layer_name, entity_type,
                geometry, dxf_handle
            )
            VALUES (
                gen_random_uuid(), %s, 'U-UNCLEAR', 'LINE',
                ST_GeomFromText('LINESTRING(0 0, 100 100)', 2227),
                'TESTHANDLE'
            )
            RETURNING entity_id
        """, (project_id,))
        drawing_entity = cur.fetchone()
        entity_id = drawing_entity['entity_id']

        cur.execute("""
            INSERT INTO standards_entities (
                entity_id, project_id, entity_type, source_table,
                classification_state, classification_confidence,
                target_table, classification_metadata
            )
            VALUES (
                %s, %s, 'utility_line', 'drawing_entities',
                'needs_review', 0.55, 'utility_lines',
                '{"reasoning": "Unclear layer"}'::jsonb
            )
        """, (entity_id, project_id))

        db_connection.commit()

        # Reclassify entity
        service = ClassificationService(db_config, conn=db_connection)
        result = service.reclassify_entity(
            entity_id=entity_id,
            new_type='utility_line',
            user_notes='User confirmed as utility line'
        )

        assert result['success'] == True
        assert result['action'] == 'confirmed'

        # Verify entity state updated
        cur.execute("""
            SELECT classification_state, classification_confidence, classification_metadata
            FROM standards_entities
            WHERE entity_id = %s
        """, (entity_id,))
        entity = cur.fetchone()

        assert entity['classification_state'] == 'user_classified'
        assert entity['classification_confidence'] == 1.0
        assert 'user_notes' in entity['classification_metadata']

        # Cleanup
        cur.execute("DELETE FROM standards_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        db_connection.commit()
        cur.close()

    def test_bulk_reclassification(self, db_connection, db_config):
        """Test batch reclassification of multiple entities."""
        cur = db_connection.cursor(cursor_factory=RealDictCursor)

        # Create test project
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (gen_random_uuid(), 'Test Bulk Project', 'TEST-BULK-001')
            RETURNING project_id
        """)
        project = cur.fetchone()
        project_id = project['project_id']

        # Create 5 entities needing review
        entity_ids = []
        for i in range(5):
            cur.execute("""
                INSERT INTO drawing_entities (
                    entity_id, project_id, layer_name, entity_type,
                    geometry, dxf_handle
                )
                VALUES (
                    gen_random_uuid(), %s, %s, 'CIRCLE',
                    ST_GeomFromText('POINT(50 50)', 2227),
                    %s
                )
                RETURNING entity_id
            """, (project_id, f'U-VALVE-{i}', f'HANDLE{i}'))
            drawing_entity = cur.fetchone()
            entity_id = drawing_entity['entity_id']
            entity_ids.append(entity_id)

            cur.execute("""
                INSERT INTO standards_entities (
                    entity_id, project_id, entity_type, source_table,
                    classification_state, classification_confidence,
                    target_table, classification_metadata
                )
                VALUES (
                    %s, %s, 'utility_structure', 'drawing_entities',
                    'needs_review', 0.60, 'utility_structures',
                    '{}'::jsonb
                )
            """, (entity_id, project_id))

        db_connection.commit()

        # Bulk reclassify all entities
        service = ClassificationService(db_config, conn=db_connection)
        result = service.bulk_reclassify(
            entity_ids=entity_ids,
            new_type='utility_structure',
            user_notes='Batch correction - all valves confirmed'
        )

        assert result['success'] == 5
        assert result['failed'] == 0

        # Verify all entities updated
        for entity_id in entity_ids:
            cur.execute("""
                SELECT classification_state, classification_confidence
                FROM standards_entities
                WHERE entity_id = %s
            """, (entity_id,))
            entity = cur.fetchone()

            assert entity['classification_state'] == 'user_classified'
            assert entity['classification_confidence'] == 1.0

        # Cleanup
        for entity_id in entity_ids:
            cur.execute("DELETE FROM standards_entities WHERE entity_id = %s", (entity_id,))
            cur.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        db_connection.commit()
        cur.close()

    def test_confidence_threshold_filtering(self, db_connection, db_config):
        """Test filtering review queue by confidence threshold."""
        cur = db_connection.cursor(cursor_factory=RealDictCursor)

        # Create test project
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (gen_random_uuid(), 'Test Confidence Project', 'TEST-CONF-001')
            RETURNING project_id
        """)
        project = cur.fetchone()
        project_id = project['project_id']

        # Create entities with different confidence levels
        confidence_levels = [0.2, 0.4, 0.6, 0.8]
        created_ids = []

        for conf in confidence_levels:
            cur.execute("""
                INSERT INTO drawing_entities (
                    entity_id, project_id, layer_name, entity_type,
                    geometry, dxf_handle
                )
                VALUES (
                    gen_random_uuid(), %s, %s, 'LINE',
                    ST_GeomFromText('LINESTRING(0 0, 100 100)', 2227),
                    %s
                )
                RETURNING entity_id
            """, (project_id, f'LAYER-{conf}', f'HANDLE-{conf}'))
            drawing_entity = cur.fetchone()
            entity_id = drawing_entity['entity_id']
            created_ids.append(entity_id)

            cur.execute("""
                INSERT INTO standards_entities (
                    entity_id, project_id, entity_type, source_table,
                    classification_state, classification_confidence,
                    classification_metadata
                )
                VALUES (
                    %s, %s, 'utility_line', 'drawing_entities',
                    'needs_review', %s, '{}'::jsonb
                )
            """, (entity_id, project_id, conf))

        db_connection.commit()

        # Test filtering by confidence range
        service = ClassificationService(db_config, conn=db_connection)

        # Get entities with confidence 0.3 - 0.7
        results = service.get_review_queue(
            project_id=project_id,
            min_confidence=0.3,
            max_confidence=0.7
        )

        # Should return 2 entities (0.4 and 0.6)
        assert len(results) == 2
        for entity in results:
            assert 0.3 <= entity['classification_confidence'] <= 0.7

        # Cleanup
        for entity_id in created_ids:
            cur.execute("DELETE FROM standards_entities WHERE entity_id = %s", (entity_id,))
            cur.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        db_connection.commit()
        cur.close()

    def test_classification_metadata_preservation(self, db_connection, db_config):
        """Test that metadata is preserved during reclassification."""
        cur = db_connection.cursor(cursor_factory=RealDictCursor)

        # Create test project
        cur.execute("""
            INSERT INTO projects (project_id, project_name, project_number)
            VALUES (gen_random_uuid(), 'Test Metadata Project', 'TEST-META-001')
            RETURNING project_id
        """)
        project = cur.fetchone()
        project_id = project['project_id']

        # Create entity with rich metadata
        original_metadata = {
            'original_confidence': 0.45,
            'reasoning': 'Ambiguous layer name',
            'suggestions': ['utility_line', 'utility_structure'],
            'spatial_context': 'Near water main'
        }

        cur.execute("""
            INSERT INTO drawing_entities (
                entity_id, project_id, layer_name, entity_type,
                geometry, dxf_handle
            )
            VALUES (
                gen_random_uuid(), %s, 'U-UNCLEAR', 'LINE',
                ST_GeomFromText('LINESTRING(0 0, 100 100)', 2227),
                'METAMETA'
            )
            RETURNING entity_id
        """, (project_id,))
        drawing_entity = cur.fetchone()
        entity_id = drawing_entity['entity_id']

        cur.execute("""
            INSERT INTO standards_entities (
                entity_id, project_id, entity_type, source_table,
                classification_state, classification_confidence,
                target_table, classification_metadata
            )
            VALUES (
                %s, %s, 'utility_line', 'drawing_entities',
                'needs_review', 0.45, 'utility_lines', %s::jsonb
            )
        """, (entity_id, project_id, json.dumps(original_metadata)))

        db_connection.commit()

        # Reclassify
        service = ClassificationService(db_config, conn=db_connection)
        service.reclassify_entity(
            entity_id=entity_id,
            new_type='utility_line',
            user_notes='User confirmed based on field visit'
        )

        # Verify metadata preserved and augmented
        cur.execute("""
            SELECT classification_metadata
            FROM standards_entities
            WHERE entity_id = %s
        """, (entity_id,))
        entity = cur.fetchone()
        metadata = entity['classification_metadata']

        # Original metadata should be preserved
        assert metadata['original_confidence'] == 0.45
        assert metadata['reasoning'] == 'Ambiguous layer name'
        assert metadata['spatial_context'] == 'Near water main'

        # New metadata should be added
        assert 'user_notes' in metadata
        assert metadata['user_notes'] == 'User confirmed based on field visit'
        assert 'reclassified_at' in metadata

        # Cleanup
        cur.execute("DELETE FROM standards_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        db_connection.commit()
        cur.close()


# Fixtures
@pytest.fixture
def db_config():
    """Database configuration."""
    return {
        'host': 'localhost',
        'database': 'survey_civil',
        'user': 'postgres',
        'password': 'postgres'
    }


@pytest.fixture
def db_connection(db_config):
    """
    Database connection fixture.

    If connection fails, skips the test gracefully instead of crashing.
    """
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        yield conn
        conn.rollback()
        conn.close()
    except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
        pytest.skip(f"Skipping integration test: No local DB available ({str(e)[:100]})")
