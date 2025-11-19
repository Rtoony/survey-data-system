"""
Pytest configuration and fixtures for the survey data system test suite.

This module provides:
- Database fixtures for testing
- Application fixtures for Flask testing
- Mock data factories
- Common test utilities
"""

# ============================================================================
# EVENTLET SAFETY: Prevent monkey-patching deadlocks during testing
# ============================================================================
# This MUST be at the very top before any other imports
import sys
import os

# Disable eventlet monkey-patching in test environment
os.environ['EVENTLET_NO_GREENDNS'] = 'yes'

# If eventlet is imported, ensure it doesn't monkey-patch
try:
    import eventlet
    # Check if already patched - if so, we can't unpatch safely
    if eventlet.patcher.is_monkey_patched('socket'):
        print("WARNING: eventlet has already monkey-patched socket. Tests may hang.")
    else:
        # Prevent future patching
        eventlet.monkey_patch = lambda *args, **kwargs: None
except ImportError:
    # eventlet not installed, no problem
    pass

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask
from unittest.mock import Mock, MagicMock
from contextlib import contextmanager
from dotenv import load_dotenv
import tempfile
import uuid

# Load environment variables
load_dotenv()

# Safety check: Ensure critical test environment variables are set
# This prevents accidentally connecting to production databases
_required_test_vars = ['TEST_PGDATABASE']
_missing_vars = [var for var in _required_test_vars if not os.getenv(var)]

if _missing_vars:
    raise EnvironmentError(
        f"CRITICAL SAFETY ERROR: Required test environment variables not set: {', '.join(_missing_vars)}. "
        f"This prevents accidentally connecting to production databases. "
        f"Please set these variables in your .env file or environment before running tests."
    )

# Test database configuration
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_PGHOST') or os.getenv('PGHOST', 'localhost'),
    'port': os.getenv('TEST_PGPORT') or os.getenv('PGPORT', '5432'),
    'database': os.getenv('TEST_PGDATABASE'),  # Required, validated above
    'user': os.getenv('TEST_PGUSER') or os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('TEST_PGPASSWORD') or os.getenv('PGPASSWORD', ''),
    'sslmode': os.getenv('TEST_SSLMODE', 'require'),
    'connect_timeout': 10
}


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def db_config():
    """Provide database configuration for tests."""
    return TEST_DB_CONFIG.copy()


@pytest.fixture(scope="session")
def db_connection(db_config):
    """
    Create a database connection for the entire test session.
    This is reused across all tests for better performance.

    If connection fails, skips the test gracefully instead of crashing.
    """
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        yield conn
        conn.close()
    except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
        pytest.skip(f"Skipping integration test: No local DB available ({str(e)[:100]})")


@pytest.fixture
def db_cursor(db_connection):
    """
    Provide a database cursor with transaction rollback.
    Each test gets its own transaction that is rolled back after the test.
    """
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cursor
    db_connection.rollback()  # Rollback any changes made during the test
    cursor.close()


@pytest.fixture
def db_transaction(db_connection):
    """
    Provide a transactional database connection.
    Changes are automatically rolled back after the test.
    """
    db_connection.autocommit = False
    yield db_connection
    db_connection.rollback()


@contextmanager
def get_test_cursor(db_config):
    """
    Context manager for database cursor in tests.

    If connection fails, skips the test gracefully instead of crashing.
    """
    try:
        conn = psycopg2.connect(**db_config)
    except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
        pytest.skip(f"Skipping integration test: No local DB available ({str(e)[:100]})")
        return  # This won't be reached, but makes the control flow clear

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Flask Application Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def app():
    """
    Create Flask application for testing using the factory pattern.

    Note: Legacy routes from app.py are NOT automatically loaded in this fixture.
    The app.py module creates its own app instance and cannot easily be integrated
    into the factory pattern without major refactoring.

    Tests should focus on the new blueprint-based architecture.
    Integration tests that need legacy routes should use the real app.py module.

    EVENTLET SAFETY:
    - This fixture does NOT start any background workers
    - SocketIO is not initialized (use mock_socketio fixture if needed)
    - No async tasks are spawned during app creation
    """
    # Import the factory function
    from app import create_app

    # Create app instance with testing config
    flask_app = create_app(config_name='testing')

    # Additional test-specific config
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SERVER_NAME'] = 'localhost:5000'

    # Ensure no background workers are started
    flask_app.config['TESTING'] = True

    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create Flask application context."""
    with app.app_context():
        yield app


@pytest.fixture
def request_context(app):
    """Create Flask request context."""
    with app.test_request_context():
        yield


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture
def project_factory(db_cursor):
    """Factory for creating test projects."""
    created_projects = []

    def _create_project(
        project_name="Test Project",
        client_name="Test Client",
        project_number=None,
        description="Test project description",
        quality_score=0.5
    ):
        if project_number is None:
            project_number = f"TEST-{uuid.uuid4().hex[:6].upper()}"

        db_cursor.execute("""
            INSERT INTO projects (
                project_name, client_name, project_number,
                description, quality_score, tags, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING project_id, project_name, project_number
        """, (
            project_name, client_name, project_number,
            description, quality_score, '{}', '{}'
        ))

        result = db_cursor.fetchone()
        created_projects.append(result['project_id'])
        return result

    yield _create_project

    # Cleanup after test
    for project_id in created_projects:
        try:
            db_cursor.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        except Exception:
            pass


@pytest.fixture
def layer_factory(db_cursor, project_factory):
    """Factory for creating test layers."""
    created_layers = []

    def _create_layer(
        layer_name="TEST-LAYER",
        color="7",
        linetype="Continuous",
        project_id=None,
        quality_score=0.5
    ):
        if project_id is None:
            project = project_factory()
            project_id = project['project_id']

        db_cursor.execute("""
            INSERT INTO layers (
                layer_name, color, linetype, lineweight,
                quality_score, tags, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING layer_id, layer_name
        """, (
            layer_name, color, linetype, "Default",
            quality_score, '{}', '{}'
        ))

        result = db_cursor.fetchone()
        created_layers.append(result['layer_id'])
        return result

    yield _create_layer

    # Cleanup
    for layer_id in created_layers:
        try:
            db_cursor.execute("DELETE FROM layers WHERE layer_id = %s", (layer_id,))
        except Exception:
            pass


@pytest.fixture
def entity_factory(db_cursor, layer_factory, project_factory):
    """Factory for creating test drawing entities."""
    created_entities = []

    def _create_entity(
        entity_type="LINE",
        layer_id=None,
        project_id=None,
        geometry=None,
        entity_data=None
    ):
        if layer_id is None:
            layer = layer_factory()
            layer_id = layer['layer_id']

        if project_id is None:
            project = project_factory()
            project_id = project['project_id']

        if geometry is None:
            # Default line geometry
            geometry = "LINESTRING(0 0, 100 100)"

        if entity_data is None:
            entity_data = {}

        db_cursor.execute("""
            INSERT INTO drawing_entities (
                entity_type, layer_id, project_id,
                geometry, entity_data
            )
            VALUES (%s, %s, %s, ST_GeomFromText(%s, 0), %s)
            RETURNING entity_id, entity_type
        """, (
            entity_type, layer_id, project_id,
            geometry, psycopg2.extras.Json(entity_data)
        ))

        result = db_cursor.fetchone()
        created_entities.append(result['entity_id'])
        return result

    yield _create_entity

    # Cleanup
    for entity_id in created_entities:
        try:
            db_cursor.execute("DELETE FROM drawing_entities WHERE entity_id = %s", (entity_id,))
        except Exception:
            pass


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing AI features without API calls."""
    mock = Mock()
    mock.embeddings.create.return_value = Mock(
        data=[Mock(embedding=[0.1] * 1536)]
    )
    mock.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Mock AI response"))]
    )
    return mock


@pytest.fixture
def mock_dxf_doc():
    """Mock ezdxf document for testing DXF operations."""
    mock = MagicMock()
    mock.modelspace.return_value = MagicMock()
    mock.layers = MagicMock()
    mock.blocks = MagicMock()
    return mock


@pytest.fixture
def mock_db_cursor():
    """
    Mock database cursor that prevents ANY network calls.
    Returns sample data for testing without database connection.
    """
    mock_cursor = MagicMock()

    # Sample project data
    sample_projects = [
        {
            'project_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
            'project_name': 'Test Project 1',
            'project_number': 'PRJ-001',
            'client_name': 'Test Client',
            'description': 'Sample project for testing',
            'quality_score': 0.85,
            'tags': '{}',
            'attributes': '{}'
        },
        {
            'project_id': 'a1b2c3d4-58cc-4372-a567-0e02b2c3d480',
            'project_name': 'Test Project 2',
            'project_number': 'PRJ-002',
            'client_name': 'Another Client',
            'description': 'Another sample project',
            'quality_score': 0.75,
            'tags': '{}',
            'attributes': '{}'
        }
    ]

    # Configure mock cursor to return sample data
    mock_cursor.fetchall.return_value = sample_projects
    mock_cursor.fetchone.return_value = sample_projects[0] if sample_projects else None
    mock_cursor.rowcount = len(sample_projects)
    mock_cursor.description = [('project_id',), ('project_name',), ('project_number',)]

    # Mock execute method
    mock_cursor.execute.return_value = None

    return mock_cursor


@pytest.fixture
def mock_db_connection(mock_db_cursor):
    """
    Mock database connection that prevents ANY network calls.
    Returns a mock connection with a mock cursor.
    """
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_db_cursor
    mock_conn.autocommit = True
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None
    mock_conn.close.return_value = None

    return mock_conn


@pytest.fixture
def mock_db(monkeypatch, mock_db_connection):
    """
    Mock the entire database module to prevent ANY network calls during tests.
    This patches psycopg2.connect and database.get_db.

    Usage in tests:
        def test_something(mock_db):
            # No actual database calls will be made
            result = some_function_that_uses_db()
            assert result is not None
    """
    # Mock psycopg2.connect
    monkeypatch.setattr('psycopg2.connect', lambda **kwargs: mock_db_connection)

    # Mock database.get_db context manager
    @contextmanager
    def mock_get_db():
        yield mock_db_connection

    monkeypatch.setattr('database.get_db', mock_get_db)

    # Mock database.execute_query
    def mock_execute_query(query, params=None):
        # Return sample data based on query content
        if 'projects' in query.lower():
            return [
                {
                    'project_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
                    'project_name': 'Test Project 1',
                    'project_number': 'PRJ-001'
                }
            ]
        return []

    monkeypatch.setattr('database.execute_query', mock_execute_query)

    return mock_db_connection


@pytest.fixture
def mock_socketio():
    """
    Mock Flask-SocketIO for testing without eventlet dependency.

    IMPORTANT: Uses async_mode='threading' to avoid eventlet deadlocks.
    This fixture prevents any eventlet monkey-patching during tests.
    """
    mock = MagicMock()

    # Configure to use threading mode (not eventlet)
    mock.async_mode = 'threading'

    # Mock common SocketIO methods
    mock.emit.return_value = None
    mock.send.return_value = None
    mock.on.return_value = lambda f: f  # Decorator passthrough

    return mock


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_dxf_file(temp_dir):
    """Create a sample DXF file for testing."""
    import ezdxf

    filepath = os.path.join(temp_dir, "test_drawing.dxf")
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Add some sample entities
    msp.add_line((0, 0, 0), (100, 100, 0), dxfattribs={'layer': 'C-WALL'})
    msp.add_circle((50, 50, 0), radius=25, dxfattribs={'layer': 'C-ANNO'})
    msp.add_text('Test', dxfattribs={'layer': 'C-TEXT', 'height': 5})

    doc.saveas(filepath)
    return filepath


# ============================================================================
# Test Utilities
# ============================================================================

@pytest.fixture
def assert_valid_uuid():
    """Utility to validate UUID strings."""
    def _assert_valid_uuid(value):
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, AttributeError):
            return False
    return _assert_valid_uuid


@pytest.fixture
def assert_geometry_valid():
    """Utility to validate PostGIS geometry."""
    def _assert_geometry_valid(db_cursor, geometry_wkt):
        db_cursor.execute("""
            SELECT ST_IsValid(ST_GeomFromText(%s, 0)) as is_valid
        """, (geometry_wkt,))
        result = db_cursor.fetchone()
        return result['is_valid']
    return _assert_geometry_valid


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require database"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with database"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end workflow tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time"
    )
    config.addinivalue_line(
        "markers", "db: Tests requiring database connection"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on their location.

    Also performs eventlet safety checks during collection.
    """
    # Check for eventlet monkey-patching after collection
    try:
        import eventlet
        if eventlet.patcher.is_monkey_patched('socket'):
            import warnings
            warnings.warn(
                "Eventlet has monkey-patched socket! Tests may deadlock. "
                "Check imports in test files for eventlet.monkey_patch() calls.",
                RuntimeWarning,
                stacklevel=2
            )
    except ImportError:
        pass  # eventlet not installed

    for item in items:
        # Mark tests in unit/ as unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Mark tests in integration/ as integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.db)

        # Mark tests in e2e/ as e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.db)
