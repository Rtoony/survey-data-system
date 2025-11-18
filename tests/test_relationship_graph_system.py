"""
Test Suite for Relationship Graph System

Tests for:
- RelationshipGraphService (CRUD operations)
- RelationshipQueryService (graph traversal)
- RelationshipValidationService (rule enforcement)
- RelationshipAnalyticsService (metrics)

Usage:
    pytest tests/test_relationship_graph_system.py -v
"""

import pytest
import sys
import os
from uuid import uuid4

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relationship_graph_service import RelationshipGraphService
from services.relationship_query_service import RelationshipQueryService
from services.relationship_validation_service import RelationshipValidationService
from services.relationship_analytics_service import RelationshipAnalyticsService


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def test_project_id():
    """Test project ID"""
    return str(uuid4())


@pytest.fixture
def test_detail_id():
    """Test detail entity ID"""
    return str(uuid4())


@pytest.fixture
def test_material_id():
    """Test material entity ID"""
    return str(uuid4())


@pytest.fixture
def graph_service():
    """RelationshipGraphService instance"""
    return RelationshipGraphService()


@pytest.fixture
def query_service():
    """RelationshipQueryService instance"""
    return RelationshipQueryService()


@pytest.fixture
def validation_service():
    """RelationshipValidationService instance"""
    return RelationshipValidationService()


@pytest.fixture
def analytics_service():
    """RelationshipAnalyticsService instance"""
    return RelationshipAnalyticsService()


# ============================================================================
# RELATIONSHIP GRAPH SERVICE TESTS
# ============================================================================

class TestRelationshipGraphService:
    """Tests for RelationshipGraphService"""

    def test_service_initialization(self, graph_service):
        """Test service can be initialized"""
        assert graph_service is not None
        assert hasattr(graph_service, 'create_edge')
        assert hasattr(graph_service, 'get_edges')

    def test_get_relationship_types(self, graph_service):
        """Test retrieving relationship types"""
        types = graph_service.get_relationship_types()
        assert isinstance(types, list)
        # Should have at least the seeded types
        type_codes = [t['type_code'] for t in types]
        assert 'USES' in type_codes
        assert 'REFERENCES' in type_codes

    def test_get_relationship_type(self, graph_service):
        """Test getting specific relationship type"""
        rel_type = graph_service.get_relationship_type('USES')
        assert rel_type is not None
        assert rel_type['type_code'] == 'USES'
        assert 'description' in rel_type

    def test_validate_edge_data_valid(self, graph_service):
        """Test edge data validation with valid data"""
        is_valid, error = graph_service.validate_edge_data(
            source_entity_type='detail',
            target_entity_type='material',
            relationship_type='USES'
        )
        assert is_valid is True
        assert error is None

    def test_validate_edge_data_invalid_type(self, graph_service):
        """Test edge data validation with invalid relationship type"""
        is_valid, error = graph_service.validate_edge_data(
            source_entity_type='detail',
            target_entity_type='material',
            relationship_type='INVALID_TYPE'
        )
        assert is_valid is False
        assert error is not None
        assert 'Invalid relationship_type' in error


# ============================================================================
# RELATIONSHIP QUERY SERVICE TESTS
# ============================================================================

class TestRelationshipQueryService:
    """Tests for RelationshipQueryService"""

    def test_service_initialization(self, query_service):
        """Test service can be initialized"""
        assert query_service is not None
        assert hasattr(query_service, 'get_related_entities')
        assert hasattr(query_service, 'find_path')

    def test_get_related_entities_no_project(self, query_service, test_detail_id):
        """Test getting related entities without project filter"""
        # Should not raise error even if no relationships exist
        results = query_service.get_related_entities(
            entity_type='detail',
            entity_id=test_detail_id,
            direction='both'
        )
        assert isinstance(results, list)


# ============================================================================
# RELATIONSHIP VALIDATION SERVICE TESTS
# ============================================================================

class TestRelationshipValidationService:
    """Tests for RelationshipValidationService"""

    def test_service_initialization(self, validation_service):
        """Test service can be initialized"""
        assert validation_service is not None
        assert hasattr(validation_service, 'validate_project_relationships')
        assert hasattr(validation_service, 'get_validation_rules')

    def test_get_validation_rules(self, validation_service):
        """Test retrieving validation rules"""
        # Should get global rules at minimum
        rules = validation_service.get_validation_rules(is_active=True)
        assert isinstance(rules, list)


# ============================================================================
# RELATIONSHIP ANALYTICS SERVICE TESTS
# ============================================================================

class TestRelationshipAnalyticsService:
    """Tests for RelationshipAnalyticsService"""

    def test_service_initialization(self, analytics_service):
        """Test service can be initialized"""
        assert analytics_service is not None
        assert hasattr(analytics_service, 'get_relationship_density')
        assert hasattr(analytics_service, 'get_project_health_score')

    def test_get_relationship_density_empty_project(self, analytics_service, test_project_id):
        """Test density calculation for empty project"""
        density = analytics_service.get_relationship_density(test_project_id)
        assert isinstance(density, dict)
        assert 'node_count' in density
        assert 'edge_count' in density
        assert 'density' in density
        # Empty project should have 0 density
        assert density['density'] == 0.0

    def test_interpret_density(self, analytics_service):
        """Test density interpretation"""
        # Test interpretation method
        assert 'Sparse' in analytics_service._interpret_density(0.05)
        assert 'Moderate' in analytics_service._interpret_density(0.2)
        assert 'Dense' in analytics_service._interpret_density(0.5)
        assert 'Very Dense' in analytics_service._interpret_density(0.8)

    def test_get_project_health_score_empty(self, analytics_service, test_project_id):
        """Test health score for empty project"""
        health = analytics_service.get_project_health_score(test_project_id)
        assert isinstance(health, dict)
        assert 'health_score' in health
        assert 'grade' in health
        assert 'status' in health
        assert 'recommendations' in health
        assert isinstance(health['recommendations'], list)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestRelationshipGraphIntegration:
    """Integration tests for the complete relationship system"""

    @pytest.mark.skip(reason="Requires database connection - run manually")
    def test_create_and_query_relationship(self, graph_service, query_service,
                                          test_project_id, test_detail_id, test_material_id):
        """Test creating a relationship and querying it"""
        # Create edge
        edge = graph_service.create_edge(
            project_id=test_project_id,
            source_entity_type='detail',
            source_entity_id=test_detail_id,
            target_entity_type='material',
            target_entity_id=test_material_id,
            relationship_type='USES',
            relationship_strength=0.9,
            created_by='test_user'
        )

        assert edge is not None
        assert edge['relationship_type'] == 'USES'

        # Query related entities
        related = query_service.get_related_entities(
            entity_type='detail',
            entity_id=test_detail_id,
            project_id=test_project_id,
            direction='outgoing'
        )

        assert len(related) >= 1
        assert any(r['related_entity_id'] == test_material_id for r in related)

        # Cleanup
        graph_service.delete_edge(edge['edge_id'], soft_delete=False)

    @pytest.mark.skip(reason="Requires database connection - run manually")
    def test_batch_create_and_subgraph(self, graph_service, query_service,
                                       test_project_id, test_detail_id):
        """Test batch creation and subgraph extraction"""
        material_1 = str(uuid4())
        material_2 = str(uuid4())
        spec_1 = str(uuid4())

        edges = [
            {
                'source_entity_type': 'detail',
                'source_entity_id': test_detail_id,
                'target_entity_type': 'material',
                'target_entity_id': material_1,
                'relationship_type': 'USES'
            },
            {
                'source_entity_type': 'detail',
                'source_entity_id': test_detail_id,
                'target_entity_type': 'material',
                'target_entity_id': material_2,
                'relationship_type': 'USES'
            },
            {
                'source_entity_type': 'detail',
                'source_entity_id': test_detail_id,
                'target_entity_type': 'spec',
                'target_entity_id': spec_1,
                'relationship_type': 'REFERENCES'
            }
        ]

        results = graph_service.create_edges_batch(test_project_id, edges)
        assert len(results) == 3

        # Get subgraph
        subgraph = query_service.get_entity_subgraph(
            entity_type='detail',
            entity_id=test_detail_id,
            project_id=test_project_id,
            depth=1
        )

        assert subgraph['node_count'] >= 4  # Detail + 3 connected entities
        assert subgraph['edge_count'] == 3

        # Cleanup
        for edge in results:
            graph_service.delete_edge(edge['edge_id'], soft_delete=False)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance tests for graph operations"""

    @pytest.mark.skip(reason="Performance test - run manually")
    def test_subgraph_extraction_performance(self, query_service, test_project_id, test_detail_id):
        """Test subgraph extraction performance"""
        import time

        start = time.time()
        subgraph = query_service.get_entity_subgraph(
            entity_type='detail',
            entity_id=test_detail_id,
            project_id=test_project_id,
            depth=2
        )
        duration = time.time() - start

        # Should complete in < 100ms for depth 2
        assert duration < 0.1, f"Subgraph extraction took {duration}s"

    @pytest.mark.skip(reason="Performance test - run manually")
    def test_analytics_performance(self, analytics_service, test_project_id):
        """Test analytics calculation performance"""
        import time

        start = time.time()
        summary = analytics_service.get_comprehensive_summary(test_project_id)
        duration = time.time() - start

        # Should complete in < 500ms
        assert duration < 0.5, f"Analytics calculation took {duration}s"


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
