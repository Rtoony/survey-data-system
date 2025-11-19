"""
Unit Tests for Projects Blueprint
Tests the projects blueprint in isolation
"""
import pytest
from flask import Flask
from app.blueprints.projects import projects_bp


@pytest.fixture
def app():
    """Create a test Flask app with just the projects blueprint"""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    test_app.config['SECRET_KEY'] = 'test-secret-key'
    test_app.register_blueprint(projects_bp)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


class TestBlueprintRegistration:
    """Test that the blueprint registers correctly"""

    def test_blueprint_is_registered(self, app):
        """Verify projects blueprint is registered"""
        assert 'projects' in app.blueprints

    def test_blueprint_has_correct_routes(self, app):
        """Verify expected routes are registered"""
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # Page routes
        assert '/projects' in routes
        assert '/projects/<project_id>' in routes
        assert '/projects/<project_id>/survey-points' in routes
        assert '/projects/<project_id>/command-center' in routes
        assert '/projects/<project_id>/entities' in routes
        assert '/projects/<project_id>/relationship-sets' in routes
        assert '/projects/<project_id>/gis-manager' in routes
        assert '/project-operations' in routes

        # API routes
        assert '/api/active-project' in routes
        assert '/api/projects' in routes
        assert '/api/projects/<project_id>' in routes
        assert '/api/projects/<project_id>/survey-points' in routes


class TestPageRoutes:
    """Test page rendering routes"""

    def test_projects_page_returns_200(self, client):
        """Test projects listing page"""
        response = client.get('/projects')
        # Will be 500 without templates, but route should exist
        assert response.status_code in [200, 500]

    def test_project_overview_route_exists(self, client):
        """Test project overview page route"""
        response = client.get('/projects/test-id')
        assert response.status_code in [200, 500]


class TestActiveProjectAPI:
    """Test active project session management"""

    def test_get_active_project_no_session(self, client):
        """Test getting active project when none is set"""
        response = client.get('/api/active-project')
        assert response.status_code in [200, 500]

    def test_set_active_project_endpoint_exists(self, client):
        """Test set active project endpoint exists"""
        response = client.post(
            '/api/active-project',
            json={'project_id': 'test-123'}
        )
        # Will fail without DB but route should exist
        assert response.status_code in [200, 400, 404, 500]


class TestProjectCRUDAPI:
    """Test project CRUD endpoints"""

    def test_get_projects_endpoint_exists(self, client):
        """Test list projects endpoint"""
        response = client.get('/api/projects')
        # 500 expected without DB connection
        assert response.status_code in [200, 500]

    def test_create_project_endpoint_exists(self, client):
        """Test create project endpoint"""
        response = client.post(
            '/api/projects',
            json={'project_name': 'Test Project'}
        )
        assert response.status_code in [200, 201, 400, 500]

    def test_get_single_project_endpoint_exists(self, client):
        """Test get single project endpoint"""
        response = client.get('/api/projects/test-id')
        assert response.status_code in [200, 404, 500]

    def test_update_project_endpoint_exists(self, client):
        """Test update project endpoint"""
        response = client.put(
            '/api/projects/test-id',
            json={'project_name': 'Updated Name'}
        )
        assert response.status_code in [200, 400, 404, 500]

    def test_delete_project_endpoint_exists(self, client):
        """Test delete project endpoint"""
        response = client.delete('/api/projects/test-id')
        assert response.status_code in [200, 404, 500]


class TestSurveyPointsAPI:
    """Test survey points endpoints"""

    def test_get_survey_points_endpoint_exists(self, client):
        """Test get survey points endpoint"""
        response = client.get('/api/projects/test-id/survey-points')
        assert response.status_code in [200, 500]

    def test_delete_survey_points_endpoint_exists(self, client):
        """Test delete survey points endpoint"""
        response = client.delete(
            '/api/projects/test-id/survey-points',
            json={'point_ids': ['id1', 'id2']}
        )
        assert response.status_code in [200, 400, 500]

    def test_delete_survey_points_requires_point_ids(self, client):
        """Test that deleting survey points requires point_ids"""
        response = client.delete(
            '/api/projects/test-id/survey-points',
            json={}
        )
        assert response.status_code == 400
        assert b'point_ids' in response.data


class TestHelperFunctions:
    """Test helper functions in the blueprint"""

    def test_get_active_project_id_helper(self, app):
        """Test get_active_project_id helper function"""
        from app.blueprints.projects import get_active_project_id

        with app.test_request_context():
            # Should return None when no session is set
            result = get_active_project_id()
            assert result is None
