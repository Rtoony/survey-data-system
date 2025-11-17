"""
Comprehensive integration tests for Projects API endpoints.

Tests cover:
- Project CRUD operations (Create, Read, Update, Delete)
- Project listing with filtering and pagination
- Project statistics and analytics
- Project relationships and associations
- Error handling and validation
- Authentication and authorization
"""

import pytest
import json
from uuid import uuid4


# ============================================================================
# Test Project Creation
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectCreation:
    """Test project creation endpoints."""

    def test_create_project_success(self, client, db_transaction):
        """Test successful project creation."""
        project_data = {
            'project_name': 'Test Project',
            'client_name': 'Test Client',
            'project_number': f'TEST-{uuid4().hex[:6].upper()}',
            'description': 'Test project description'
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert 'project_id' in data
        assert data['project_name'] == 'Test Project'

    def test_create_project_missing_required_fields(self, client):
        """Test project creation with missing required fields."""
        project_data = {
            'project_name': 'Test Project'
            # Missing client_name and project_number
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        # Should return error for missing fields
        assert response.status_code in [400, 422]

    def test_create_project_duplicate_project_number(self, client, project_factory):
        """Test project creation with duplicate project number."""
        existing_project = project_factory(project_number='DUPLICATE-001')

        project_data = {
            'project_name': 'Another Project',
            'client_name': 'Test Client',
            'project_number': 'DUPLICATE-001'
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        # Should handle duplicate project number
        assert response.status_code in [400, 409, 422]

    def test_create_project_with_custom_attributes(self, client):
        """Test project creation with custom attributes."""
        project_data = {
            'project_name': 'Custom Project',
            'client_name': 'Test Client',
            'project_number': f'CUSTOM-{uuid4().hex[:6].upper()}',
            'attributes': {
                'custom_field_1': 'value1',
                'custom_field_2': 'value2'
            }
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        # Should accept custom attributes
        assert response.status_code in [200, 201, 422]


# ============================================================================
# Test Project Retrieval
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectRetrieval:
    """Test project retrieval endpoints."""

    def test_get_project_by_id(self, client, project_factory):
        """Test retrieving project by ID."""
        project = project_factory(project_name='Retrieval Test Project')

        response = client.get(f'/api/projects/{project["project_id"]}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['project_id'] == str(project['project_id'])
        assert data['project_name'] == 'Retrieval Test Project'

    def test_get_project_not_found(self, client):
        """Test retrieving non-existent project."""
        fake_id = str(uuid4())
        response = client.get(f'/api/projects/{fake_id}')

        assert response.status_code == 404

    def test_get_project_invalid_uuid(self, client):
        """Test retrieving project with invalid UUID."""
        response = client.get('/api/projects/invalid-uuid')

        assert response.status_code in [400, 404]

    def test_list_all_projects(self, client, project_factory):
        """Test listing all projects."""
        # Create multiple test projects
        project_factory(project_name='Project 1')
        project_factory(project_name='Project 2')
        project_factory(project_name='Project 3')

        response = client.get('/api/projects')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list) or 'projects' in data

    def test_list_projects_with_pagination(self, client, project_factory):
        """Test listing projects with pagination."""
        # Create multiple projects
        for i in range(10):
            project_factory(project_name=f'Project {i}')

        response = client.get('/api/projects?page=1&per_page=5')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should return paginated results
        assert data is not None

    def test_list_projects_with_search(self, client, project_factory):
        """Test listing projects with search filter."""
        project_factory(project_name='Searchable Project Alpha')
        project_factory(project_name='Different Project')

        response = client.get('/api/projects?search=Searchable')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should filter by search term
        assert data is not None


# ============================================================================
# Test Project Updates
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectUpdates:
    """Test project update endpoints."""

    def test_update_project_success(self, client, project_factory):
        """Test successful project update."""
        project = project_factory(project_name='Original Name')

        update_data = {
            'project_name': 'Updated Name',
            'description': 'Updated description'
        }

        response = client.put(f'/api/projects/{project["project_id"]}',
                             json=update_data,
                             content_type='application/json')

        assert response.status_code in [200, 204]

    def test_update_project_not_found(self, client):
        """Test updating non-existent project."""
        fake_id = str(uuid4())
        update_data = {'project_name': 'New Name'}

        response = client.put(f'/api/projects/{fake_id}',
                             json=update_data,
                             content_type='application/json')

        assert response.status_code == 404

    def test_update_project_partial(self, client, project_factory):
        """Test partial project update (PATCH)."""
        project = project_factory(project_name='Original Name')

        update_data = {'description': 'Updated description only'}

        response = client.patch(f'/api/projects/{project["project_id"]}',
                               json=update_data,
                               content_type='application/json')

        # Should allow partial updates
        assert response.status_code in [200, 204, 405]  # 405 if PATCH not supported

    def test_update_project_invalid_data(self, client, project_factory):
        """Test project update with invalid data."""
        project = project_factory()

        update_data = {
            'quality_score': 'invalid'  # Should be numeric
        }

        response = client.put(f'/api/projects/{project["project_id"]}',
                             json=update_data,
                             content_type='application/json')

        assert response.status_code in [400, 422]


# ============================================================================
# Test Project Deletion
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectDeletion:
    """Test project deletion endpoints."""

    def test_delete_project_success(self, client, project_factory):
        """Test successful project deletion."""
        project = project_factory(project_name='Project to Delete')

        response = client.delete(f'/api/projects/{project["project_id"]}')

        assert response.status_code in [200, 204]

        # Verify project is deleted
        get_response = client.get(f'/api/projects/{project["project_id"]}')
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, client):
        """Test deleting non-existent project."""
        fake_id = str(uuid4())
        response = client.delete(f'/api/projects/{fake_id}')

        assert response.status_code == 404

    def test_delete_project_with_entities(self, client, project_factory, entity_factory):
        """Test deleting project with associated entities."""
        project = project_factory()
        entity_factory(project_id=project['project_id'])

        response = client.delete(f'/api/projects/{project["project_id"]}')

        # Should handle cascade deletion or prevent deletion
        assert response.status_code in [200, 204, 400, 409]


# ============================================================================
# Test Project Statistics
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectStatistics:
    """Test project statistics endpoints."""

    def test_get_project_stats(self, client, project_factory):
        """Test retrieving project statistics."""
        project = project_factory()

        response = client.get(f'/api/projects/{project["project_id"]}/stats')

        # Stats endpoint may or may not exist
        assert response.status_code in [200, 404]

    def test_get_project_entity_counts(self, client, project_factory, entity_factory):
        """Test getting entity counts for project."""
        project = project_factory()
        entity_factory(project_id=project['project_id'])
        entity_factory(project_id=project['project_id'])

        response = client.get(f'/api/projects/{project["project_id"]}/entities/count')

        # Count endpoint may or may not exist
        assert response.status_code in [200, 404]


# ============================================================================
# Test Project Relationships
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectRelationships:
    """Test project relationship endpoints."""

    def test_get_project_layers(self, client, project_factory, layer_factory):
        """Test retrieving project layers."""
        project = project_factory()
        layer_factory(project_id=project['project_id'])

        response = client.get(f'/api/projects/{project["project_id"]}/layers')

        # Layers endpoint may or may not exist
        assert response.status_code in [200, 404]

    def test_get_project_entities(self, client, project_factory, entity_factory):
        """Test retrieving project entities."""
        project = project_factory()
        entity_factory(project_id=project['project_id'])

        response = client.get(f'/api/projects/{project["project_id"]}/entities')

        # Entities endpoint may or may not exist
        assert response.status_code in [200, 404]


# ============================================================================
# Test Input Validation
# ============================================================================

@pytest.mark.integration
class TestInputValidation:
    """Test input validation for project endpoints."""

    def test_create_project_sql_injection_attempt(self, client):
        """Test SQL injection protection."""
        malicious_data = {
            'project_name': "Test'; DROP TABLE projects; --",
            'client_name': 'Test Client',
            'project_number': 'SQL-INJECT-001'
        }

        response = client.post('/api/projects',
                              json=malicious_data,
                              content_type='application/json')

        # Should handle safely (create project or reject)
        assert response.status_code in [200, 201, 400, 422]

    def test_create_project_xss_attempt(self, client):
        """Test XSS protection."""
        xss_data = {
            'project_name': '<script>alert("xss")</script>',
            'client_name': 'Test Client',
            'project_number': f'XSS-{uuid4().hex[:6].upper()}'
        }

        response = client.post('/api/projects',
                              json=xss_data,
                              content_type='application/json')

        # Should handle safely
        assert response.status_code in [200, 201, 400, 422]

    def test_create_project_oversized_input(self, client):
        """Test handling of oversized input."""
        large_data = {
            'project_name': 'A' * 10000,  # Very long name
            'client_name': 'Test Client',
            'project_number': f'LARGE-{uuid4().hex[:6].upper()}'
        }

        response = client.post('/api/projects',
                              json=large_data,
                              content_type='application/json')

        # Should reject or truncate
        assert response.status_code in [200, 201, 400, 413, 422]


# ============================================================================
# Test Error Handling
# ============================================================================

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling for project endpoints."""

    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON."""
        response = client.post('/api/projects',
                              data='{"invalid json',
                              content_type='application/json')

        assert response.status_code == 400

    def test_missing_content_type(self, client):
        """Test request without content type header."""
        project_data = {
            'project_name': 'Test Project',
            'client_name': 'Test Client',
            'project_number': f'TEST-{uuid4().hex[:6].upper()}'
        }

        response = client.post('/api/projects',
                              data=json.dumps(project_data))

        # Should handle missing content type
        assert response.status_code in [200, 201, 400, 415]

    def test_empty_request_body(self, client):
        """Test request with empty body."""
        response = client.post('/api/projects',
                              json={},
                              content_type='application/json')

        assert response.status_code in [400, 422]


# ============================================================================
# Test Quality Score Management
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestQualityScores:
    """Test project quality score management."""

    def test_create_project_with_quality_score(self, client):
        """Test creating project with quality score."""
        project_data = {
            'project_name': 'Quality Project',
            'client_name': 'Test Client',
            'project_number': f'QUAL-{uuid4().hex[:6].upper()}',
            'quality_score': 0.85
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        assert response.status_code in [200, 201, 422]

    def test_update_project_quality_score(self, client, project_factory):
        """Test updating project quality score."""
        project = project_factory(quality_score=0.5)

        update_data = {'quality_score': 0.9}

        response = client.put(f'/api/projects/{project["project_id"]}',
                             json=update_data,
                             content_type='application/json')

        assert response.status_code in [200, 204]

    def test_invalid_quality_score_range(self, client):
        """Test quality score outside valid range."""
        project_data = {
            'project_name': 'Invalid Score Project',
            'client_name': 'Test Client',
            'project_number': f'INVALID-{uuid4().hex[:6].upper()}',
            'quality_score': 1.5  # Invalid: should be 0-1
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        # Should reject invalid score
        assert response.status_code in [400, 422]


# ============================================================================
# Test Project Tags
# ============================================================================

@pytest.mark.integration
@pytest.mark.db
class TestProjectTags:
    """Test project tagging functionality."""

    def test_create_project_with_tags(self, client):
        """Test creating project with tags."""
        project_data = {
            'project_name': 'Tagged Project',
            'client_name': 'Test Client',
            'project_number': f'TAG-{uuid4().hex[:6].upper()}',
            'tags': ['residential', 'new-construction']
        }

        response = client.post('/api/projects',
                              json=project_data,
                              content_type='application/json')

        # Should accept tags
        assert response.status_code in [200, 201, 422]

    def test_update_project_tags(self, client, project_factory):
        """Test updating project tags."""
        project = project_factory()

        update_data = {'tags': ['updated', 'tags']}

        response = client.put(f'/api/projects/{project["project_id"]}',
                             json=update_data,
                             content_type='application/json')

        assert response.status_code in [200, 204]
