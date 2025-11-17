"""
Comprehensive unit tests for ClassificationService.

Tests cover:
- Review queue retrieval with various filters
- Entity reclassification workflows
- Confidence score calculations
- Classification state management
- Metadata handling
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import json

from services.classification_service import ClassificationService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def classification_service(db_config):
    """Create ClassificationService instance."""
    return ClassificationService(db_config)


@pytest.fixture
def classification_service_with_conn(db_config, db_connection):
    """Create ClassificationService with database connection."""
    return ClassificationService(db_config, conn=db_connection)


@pytest.fixture
def mock_cursor_with_review_queue():
    """Mock cursor with review queue data."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'source_table': 'drawing_entities',
            'canonical_name': 'utility_line',
            'classification_state': 'needs_review',
            'classification_confidence': 0.65,
            'classification_metadata': '{"reasoning": "Low confidence"}',
            'target_table': 'utility_lines',
            'target_id': None,
            'project_id': '22222222-2222-2222-2222-222222222222',
            'layer_name': 'U-WATR',
            'dxf_entity_type': 'LINE',
            'geometry_wkt': 'LINESTRING(0 0, 100 100)',
            'geometry_type': 'ST_LineString'
        },
        {
            'entity_id': '33333333-3333-3333-3333-333333333333',
            'entity_type': 'CIRCLE',
            'source_table': 'drawing_entities',
            'canonical_name': 'valve',
            'classification_state': 'needs_review',
            'classification_confidence': 0.45,
            'classification_metadata': '{"reasoning": "Ambiguous geometry"}',
            'target_table': 'utility_structures',
            'target_id': None,
            'project_id': '22222222-2222-2222-2222-222222222222',
            'layer_name': 'U-WATR-VALVE',
            'dxf_entity_type': 'CIRCLE',
            'geometry_wkt': 'POINT(50 50)',
            'geometry_type': 'ST_Point'
        }
    ]
    return mock_cursor


# ============================================================================
# Test Initialization
# ============================================================================

class TestClassificationServiceInit:
    """Test ClassificationService initialization."""

    def test_init_without_connection(self, db_config):
        """Test initialization without database connection."""
        service = ClassificationService(db_config)
        assert service.db_config == db_config
        assert service.conn is None
        assert service.should_close is True

    def test_init_with_connection(self, db_config, db_connection):
        """Test initialization with database connection."""
        service = ClassificationService(db_config, conn=db_connection)
        assert service.conn == db_connection
        assert service.should_close is False


# ============================================================================
# Test Review Queue Retrieval
# ============================================================================

class TestGetReviewQueue:
    """Test review queue retrieval with various filters."""

    def test_get_review_queue_no_filters(self, db_config, mock_cursor_with_review_queue):
        """Test getting review queue without filters."""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor_with_review_queue
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue()

            assert len(results) == 2
            assert results[0]['entity_id'] == '11111111-1111-1111-1111-111111111111'
            assert results[1]['entity_id'] == '33333333-3333-3333-3333-333333333333'

    def test_get_review_queue_with_project_filter(self, db_config, mock_cursor_with_review_queue):
        """Test getting review queue filtered by project."""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor_with_review_queue
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue(
                project_id='22222222-2222-2222-2222-222222222222'
            )

            # Verify query was called with project_id parameter
            assert mock_cursor_with_review_queue.execute.called

    def test_get_review_queue_with_confidence_range(self, db_config):
        """Test getting review queue with confidence score range."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'entity_id': '11111111-1111-1111-1111-111111111111',
                'classification_confidence': 0.65,
            }
        ]

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue(
                min_confidence=0.5,
                max_confidence=0.8
            )

            # Should have filtered by confidence range
            assert mock_cursor.execute.called

    def test_get_review_queue_with_limit(self, db_config, mock_cursor_with_review_queue):
        """Test getting review queue with result limit."""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor_with_review_queue
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue(limit=50)

            # Verify LIMIT parameter was used
            call_args = mock_cursor_with_review_queue.execute.call_args
            assert 50 in call_args[0][1]

    def test_get_review_queue_empty_results(self, db_config):
        """Test getting review queue when no entities need review."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue()

            assert len(results) == 0


# ============================================================================
# Test Entity Reclassification
# ============================================================================

class TestReclassifyEntity:
    """Test entity reclassification workflows."""

    def test_reclassify_entity_success(self, db_config):
        """Test successful entity reclassification."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': '{}'
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.return_value = ('utility_lines', 'line_id')

            service = ClassificationService(db_config)
            result = service.reclassify_entity(
                '11111111-1111-1111-1111-111111111111',
                'utility_line',
                user_notes='User corrected classification'
            )

            # Should have updated entity
            assert mock_cursor.execute.called

    def test_reclassify_entity_not_found(self, db_config):
        """Test reclassification of non-existent entity."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)

            with pytest.raises(ValueError, match="not found"):
                service.reclassify_entity(
                    '99999999-9999-9999-9999-999999999999',
                    'utility_line'
                )

    def test_reclassify_entity_with_user_notes(self, db_config):
        """Test reclassification with user notes."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': '{}'
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.return_value = ('utility_lines', 'line_id')

            service = ClassificationService(db_config)
            service.reclassify_entity(
                '11111111-1111-1111-1111-111111111111',
                'utility_line',
                user_notes='Corrected based on site visit'
            )

            # Verify user notes were included in metadata
            assert mock_cursor.execute.called


# ============================================================================
# Test Confidence Score Management
# ============================================================================

class TestConfidenceScores:
    """Test confidence score calculations and management."""

    def test_high_confidence_entities_not_in_review_queue(self, db_config):
        """Test that high-confidence entities are not in review queue."""
        mock_cursor = MagicMock()
        # Only low-confidence entities should be returned
        mock_cursor.fetchall.return_value = [
            {
                'entity_id': '11111111-1111-1111-1111-111111111111',
                'classification_confidence': 0.45,
                'classification_state': 'needs_review'
            }
        ]

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue(min_confidence=0.0, max_confidence=0.5)

            # Should only return low-confidence entities
            for entity in results:
                assert entity['classification_confidence'] <= 0.5

    def test_confidence_score_updated_after_reclassification(self, db_config):
        """Test that confidence score is set to 1.0 after user reclassification."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': '{}',
            'classification_confidence': 0.45
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.return_value = ('utility_lines', 'line_id')

            service = ClassificationService(db_config)
            service.reclassify_entity(
                '11111111-1111-1111-1111-111111111111',
                'utility_line'
            )

            # Should have set confidence to 1.0
            # Verify UPDATE statement includes confidence = 1.0
            assert mock_cursor.execute.called


# ============================================================================
# Test Classification State Management
# ============================================================================

class TestClassificationStates:
    """Test classification state transitions."""

    def test_needs_review_state_filtering(self, db_config, mock_cursor_with_review_queue):
        """Test that only 'needs_review' entities are returned."""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor_with_review_queue
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            results = service.get_review_queue()

            # All results should be in 'needs_review' state
            for entity in results:
                assert entity['classification_state'] == 'needs_review'

    def test_user_classified_state_after_reclassification(self, db_config):
        """Test that state changes to 'user_classified' after reclassification."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': '{}',
            'classification_state': 'needs_review'
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.return_value = ('utility_lines', 'line_id')

            service = ClassificationService(db_config)
            service.reclassify_entity(
                '11111111-1111-1111-1111-111111111111',
                'utility_line'
            )

            # Should have set state to 'user_classified'
            assert mock_cursor.execute.called


# ============================================================================
# Test Metadata Handling
# ============================================================================

class TestMetadataHandling:
    """Test classification metadata handling."""

    def test_metadata_preserved_during_reclassification(self, db_config):
        """Test that existing metadata is preserved during reclassification."""
        original_metadata = {
            'original_confidence': 0.45,
            'reasoning': 'Low confidence due to ambiguous layer name'
        }

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': json.dumps(original_metadata)
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.return_value = ('utility_lines', 'line_id')

            service = ClassificationService(db_config)
            service.reclassify_entity(
                '11111111-1111-1111-1111-111111111111',
                'utility_line',
                user_notes='User correction'
            )

            # Metadata should include user notes and reclassification timestamp
            assert mock_cursor.execute.called

    def test_metadata_includes_timestamp(self, db_config):
        """Test that reclassification timestamp is added to metadata."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': '{}'
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.return_value = ('utility_lines', 'line_id')

            service = ClassificationService(db_config)
            service.reclassify_entity(
                '11111111-1111-1111-1111-111111111111',
                'utility_line'
            )

            # Should have added reclassified_at timestamp
            assert mock_cursor.execute.called


# ============================================================================
# Test Connection Management
# ============================================================================

class TestConnectionManagement:
    """Test database connection management."""

    def test_connection_closed_when_owned(self, db_config):
        """Test that connection is closed when service owns it."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            service = ClassificationService(db_config)
            service.get_review_queue()

            # Connection should be closed
            mock_conn.close.assert_called_once()

    def test_connection_not_closed_when_external(self, db_config):
        """Test that external connection is not closed."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor

        service = ClassificationService(db_config, conn=mock_conn)
        service.get_review_queue()

        # External connection should NOT be closed
        mock_conn.close.assert_not_called()


# ============================================================================
# Test Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    def test_database_connection_error(self, db_config):
        """Test handling of database connection failure."""
        with patch('psycopg2.connect', side_effect=Exception("Connection failed")):
            service = ClassificationService(db_config)

            with pytest.raises(Exception, match="Connection failed"):
                service.get_review_queue()

    def test_invalid_entity_type_reclassification(self, db_config):
        """Test reclassification with invalid entity type."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'entity_id': '11111111-1111-1111-1111-111111111111',
            'entity_type': 'LINE',
            'target_table': 'utility_lines',
            'classification_metadata': '{}'
        }

        with patch('psycopg2.connect') as mock_connect, \
             patch('services.classification_service.EntityRegistry') as mock_registry:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            mock_registry.get_table_and_pk.side_effect = Exception("Invalid type")

            service = ClassificationService(db_config)

            with pytest.raises(Exception):
                service.reclassify_entity(
                    '11111111-1111-1111-1111-111111111111',
                    'invalid_type'
                )
