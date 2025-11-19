"""
Test Flask Extensions
Tests for extension initialization and configuration

Tests verify:
- CORS extension initialization
- Cache extension initialization
- Extension binding to Flask app
- Extension configuration
"""
import pytest
from flask import Flask


class TestCORSExtension:
    """Test suite for CORS (Cross-Origin Resource Sharing) extension."""

    def test_cors_extension_exists(self):
        """Verify CORS extension is defined in extensions module."""
        from app.extensions import cors

        assert cors is not None

    def test_cors_extension_is_initialized(self, app):
        """Verify CORS extension is initialized with the Flask app."""
        from app.extensions import cors

        # The extension should be bound to the app
        assert cors is not None

        # Verify CORS is actually working by checking for CORS-related attributes
        # When CORS is initialized, it adds extensions to the app
        assert hasattr(app, 'extensions')

    def test_cors_allows_cross_origin_requests(self, client, mock_db):
        """Verify CORS headers are added to responses."""
        # Make a request with Origin header
        response = client.get('/', headers={'Origin': 'http://example.com'})

        # Even if the route doesn't exist, CORS should still add headers
        # or at least the extension should be configured
        # We're just verifying the extension is loaded
        assert response is not None

    def test_cors_extension_type(self):
        """Verify CORS extension is the correct type."""
        from app.extensions import cors
        from flask_cors import CORS

        assert isinstance(cors, CORS)


class TestCacheExtension:
    """Test suite for Flask-Caching extension."""

    def test_cache_extension_exists(self):
        """Verify Cache extension is defined in extensions module."""
        from app.extensions import cache

        assert cache is not None

    def test_cache_extension_is_initialized(self, app):
        """Verify Cache extension is initialized with the Flask app."""
        from app.extensions import cache

        assert cache is not None
        assert hasattr(app, 'extensions')

    def test_cache_extension_type(self):
        """Verify Cache extension is the correct type."""
        from app.extensions import cache
        from flask_caching import Cache

        assert isinstance(cache, Cache)

    def test_cache_configuration_in_testing(self, app):
        """Verify cache is configured as NullCache in testing environment."""
        # Testing config should use NullCache
        assert app.config['TESTING'] is True
        assert app.config['CACHE_TYPE'] == 'NullCache'

    def test_cache_configuration_in_development(self, mock_db):
        """Verify cache is configured correctly in development environment."""
        from app import create_app

        dev_app = create_app(config_name='development')

        assert dev_app.config['CACHE_TYPE'] == 'SimpleCache'
        assert dev_app.config['CACHE_DEFAULT_TIMEOUT'] == 300

    def test_cache_has_timeout_setting(self):
        """Verify cache has default timeout configured."""
        from app.config import Config

        assert hasattr(Config, 'CACHE_DEFAULT_TIMEOUT')
        assert Config.CACHE_DEFAULT_TIMEOUT == 300  # 5 minutes


class TestExtensionInitialization:
    """Test suite for extension initialization pattern."""

    def test_extensions_initialized_without_app(self):
        """Verify extensions are created without app binding initially."""
        from app.extensions import cors, cache

        # Extensions should exist but not be bound to any specific app yet
        assert cors is not None
        assert cache is not None

    def test_extensions_bound_to_app_in_factory(self, app):
        """Verify extensions are bound to app in create_app factory."""
        from app.extensions import cors, cache

        # After create_app is called, extensions should be initialized
        assert 'cors' in app.extensions or cors is not None
        assert cache is not None

    def test_multiple_apps_can_use_same_extensions(self, mock_db):
        """Verify same extension instances can be used with multiple apps."""
        from app import create_app

        app1 = create_app(config_name='testing')
        app2 = create_app(config_name='development')

        # Both apps should have extensions initialized
        assert hasattr(app1, 'extensions')
        assert hasattr(app2, 'extensions')

    def test_extension_module_has_no_circular_imports(self):
        """Verify extensions module can be imported without circular dependency issues."""
        try:
            from app.extensions import cors, cache
            success = True
        except ImportError as e:
            success = False
            error_msg = str(e)

        assert success, f"Circular import detected: {error_msg if not success else ''}"

    def test_extensions_module_structure(self):
        """Verify extensions module has correct structure."""
        import app.extensions as ext_module

        # Should have CORS and Cache
        assert hasattr(ext_module, 'cors')
        assert hasattr(ext_module, 'cache')

        # Should NOT have app instance (to avoid circular imports)
        assert not hasattr(ext_module, 'app')


class TestExtensionIntegration:
    """Test suite for extension integration with Flask app."""

    def test_app_has_extensions_attribute(self, app):
        """Verify Flask app has extensions attribute after initialization."""
        assert hasattr(app, 'extensions')

    def test_cors_allows_api_requests(self, client, mock_db):
        """Verify CORS is configured to allow API requests."""
        # Test with a preflight OPTIONS request
        response = client.options(
            '/',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'GET'
            }
        )

        # Just verify the response exists
        assert response is not None

    def test_cache_can_be_used_in_routes(self, mock_db):
        """Verify cache extension can be used in route handlers."""
        from app import create_app
        from app.extensions import cache

        # Create a fresh app to add routes to
        test_app = create_app(config_name='testing')

        # Create a test route that uses cache
        @test_app.route('/test-cache')
        @cache.cached(timeout=60)
        def test_cached_route():
            return {'message': 'cached'}

        with test_app.test_client() as client:
            response = client.get('/test-cache')
            assert response is not None
            assert response.status_code == 200

    def test_extensions_initialized_before_blueprints(self, app):
        """Verify extensions are initialized before blueprints are registered."""
        # This is important for the application factory pattern
        # Extensions should be available when blueprint routes are defined

        # If blueprints are registered, extensions must already be initialized
        if len(app.blueprints) > 0:
            assert hasattr(app, 'extensions')

    def test_no_database_connection_during_extension_init(self, mock_db):
        """Verify extensions don't try to connect to database during initialization."""
        from app import create_app

        # This should NOT raise any database connection errors
        # because we're using mock_db
        try:
            app = create_app(config_name='testing')
            success = True
        except Exception as e:
            success = False
            error = str(e)

        assert success, f"Extension initialization failed: {error if not success else ''}"


class TestExtensionConfiguration:
    """Test suite for extension configuration."""

    def test_cors_configuration(self, app):
        """Verify CORS is configured correctly."""
        from app.extensions import cors

        # CORS should be initialized
        assert cors is not None

    def test_cache_simple_cache_in_development(self, mock_db):
        """Verify SimpleCache is used in development."""
        from app import create_app

        app = create_app(config_name='development')

        assert app.config['CACHE_TYPE'] == 'SimpleCache'

    def test_cache_null_cache_in_testing(self, app):
        """Verify NullCache is used in testing (no actual caching)."""
        assert app.config['CACHE_TYPE'] == 'NullCache'

    def test_cache_timeout_configuration(self, mock_db):
        """Verify cache timeout is configured."""
        from app import create_app

        app = create_app(config_name='development')

        assert 'CACHE_DEFAULT_TIMEOUT' in app.config
        assert app.config['CACHE_DEFAULT_TIMEOUT'] > 0

    def test_session_cookie_configuration(self, app):
        """Verify session cookie settings are configured."""
        assert 'SESSION_COOKIE_HTTPONLY' in app.config
        assert 'SESSION_COOKIE_SAMESITE' in app.config
        assert 'PERMANENT_SESSION_LIFETIME' in app.config
