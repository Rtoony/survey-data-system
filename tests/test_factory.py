"""
Test Application Factory Pattern
Tests for the create_app() factory function

Tests verify:
- Flask app creation with different configurations
- Configuration loading (Development, Production, Testing)
- Extension initialization
- Blueprint registration
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask


class TestCreateApp:
    """Test suite for the create_app factory function."""

    def test_create_app_returns_flask_instance(self, mock_db):
        """Verify create_app() returns a valid Flask application instance."""
        from app import create_app

        app = create_app(config_name='testing')

        assert app is not None
        assert isinstance(app, Flask)

    def test_create_app_with_testing_config(self, mock_db):
        """Verify create_app() loads testing configuration correctly."""
        from app import create_app

        app = create_app(config_name='testing')

        assert app.config['TESTING'] is True
        assert app.config['CACHE_TYPE'] == 'NullCache'

    def test_create_app_with_development_config(self, mock_db):
        """Verify create_app() loads development configuration correctly."""
        from app import create_app

        app = create_app(config_name='development')

        assert app.config['DEBUG'] is True
        assert 'SECRET_KEY' in app.config

    def test_create_app_with_production_config(self, mock_db):
        """Verify create_app() loads production configuration correctly."""
        from app import create_app

        app = create_app(config_name='production')

        assert app.config['DEBUG'] is False

    @patch.dict('os.environ', {'FLASK_ENV': 'production'})
    def test_create_app_uses_env_variable_when_no_config_provided(self, mock_db):
        """Verify create_app() uses FLASK_ENV environment variable when config_name is None."""
        from app import create_app

        app = create_app(config_name=None)

        assert app.config['DEBUG'] is False  # Production config

    @patch.dict('os.environ', {}, clear=True)
    def test_create_app_defaults_to_development_when_no_env(self, mock_db):
        """Verify create_app() defaults to development when FLASK_ENV is not set."""
        from app import create_app

        # Remove FLASK_ENV if it exists
        import os
        os.environ.pop('FLASK_ENV', None)

        app = create_app(config_name=None)

        # Should default to development
        assert app.config['DEBUG'] is True

    def test_create_app_has_custom_json_provider(self, mock_db):
        """Verify create_app() sets a custom JSON provider for datetime/UUID serialization."""
        from app import create_app
        from app import CustomJSONProvider

        app = create_app(config_name='testing')

        assert isinstance(app.json, CustomJSONProvider)

    def test_custom_json_provider_handles_datetime(self, mock_db):
        """Verify CustomJSONProvider can serialize datetime objects."""
        from app import CustomJSONProvider, create_app
        from datetime import datetime, date

        app = create_app(config_name='testing')

        test_datetime = datetime(2025, 1, 1, 12, 0, 0)
        test_date = date(2025, 1, 1)

        with app.app_context():
            # Test datetime serialization using Flask's json.dumps
            from flask import json
            result = json.dumps({'dt': test_datetime})
            assert '2025-01-01' in result

    def test_custom_json_provider_handles_decimal(self, mock_db):
        """Verify CustomJSONProvider can serialize Decimal objects."""
        from app import create_app
        from decimal import Decimal

        app = create_app(config_name='testing')

        test_decimal = Decimal('123.45')

        with app.app_context():
            from flask import json
            result = json.dumps({'value': test_decimal})
            assert '123.45' in result

    def test_custom_json_provider_handles_uuid(self, mock_db):
        """Verify CustomJSONProvider can serialize UUID objects."""
        from app import create_app
        import uuid

        app = create_app(config_name='testing')

        test_uuid = uuid.UUID('f47ac10b-58cc-4372-a567-0e02b2c3d479')

        with app.app_context():
            from flask import json
            result = json.dumps({'id': test_uuid})
            assert 'f47ac10b-58cc-4372-a567-0e02b2c3d479' in result

    def test_create_app_has_correct_template_folder(self, mock_db):
        """Verify create_app() sets the correct template folder."""
        from app import create_app

        app = create_app(config_name='testing')

        assert app.template_folder is not None
        assert 'templates' in app.template_folder

    def test_create_app_has_correct_static_folder(self, mock_db):
        """Verify create_app() sets the correct static folder."""
        from app import create_app

        app = create_app(config_name='testing')

        assert app.static_folder is not None
        assert 'static' in app.static_folder

    def test_create_app_registers_blueprints(self, mock_db):
        """Verify create_app() registers all required blueprints."""
        from app import create_app

        app = create_app(config_name='testing')

        # Check that blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        # These blueprints should be registered based on app/__init__.py
        expected_blueprints = ['auth', 'graphrag', 'ai_search', 'quality']

        for bp_name in expected_blueprints:
            assert bp_name in blueprint_names, f"Blueprint '{bp_name}' not registered"

    def test_create_app_prints_db_config_status(self, mock_db, capsys):
        """Verify create_app() prints database configuration status on startup."""
        from app import create_app

        app = create_app(config_name='testing')

        # Capture stdout
        captured = capsys.readouterr()

        # Verify debug output is printed
        assert 'Database Configuration Status' in captured.out

    def test_create_app_loads_secret_key(self, mock_db):
        """Verify create_app() loads SECRET_KEY from configuration."""
        from app import create_app

        app = create_app(config_name='testing')

        assert 'SECRET_KEY' in app.config
        assert app.config['SECRET_KEY'] is not None
        assert len(app.config['SECRET_KEY']) > 0

    def test_create_app_multiple_instances_are_independent(self, mock_db):
        """Verify multiple app instances created by create_app() are independent."""
        from app import create_app

        app1 = create_app(config_name='testing')
        app2 = create_app(config_name='development')

        # They should be different instances
        assert app1 is not app2

        # They should have different configurations
        assert app1.config['TESTING'] is True
        assert app2.config['DEBUG'] is True
        assert app2.config.get('TESTING') != True


class TestConfigurationClasses:
    """Test suite for configuration classes."""

    def test_base_config_has_secret_key(self):
        """Verify base Config class has SECRET_KEY."""
        from app.config import Config

        assert hasattr(Config, 'SECRET_KEY')
        assert Config.SECRET_KEY is not None

    def test_base_config_has_session_settings(self):
        """Verify base Config class has session configuration."""
        from app.config import Config

        assert hasattr(Config, 'SESSION_COOKIE_SECURE')
        assert hasattr(Config, 'SESSION_COOKIE_HTTPONLY')
        assert hasattr(Config, 'SESSION_COOKIE_SAMESITE')
        assert hasattr(Config, 'PERMANENT_SESSION_LIFETIME')

    def test_base_config_has_cache_settings(self):
        """Verify base Config class has cache configuration."""
        from app.config import Config

        assert hasattr(Config, 'CACHE_TYPE')
        assert hasattr(Config, 'CACHE_DEFAULT_TIMEOUT')

    def test_development_config_inherits_from_base(self):
        """Verify DevelopmentConfig inherits from Config."""
        from app.config import DevelopmentConfig, Config

        assert issubclass(DevelopmentConfig, Config)
        assert DevelopmentConfig.DEBUG is True

    def test_production_config_inherits_from_base(self):
        """Verify ProductionConfig inherits from Config."""
        from app.config import ProductionConfig, Config

        assert issubclass(ProductionConfig, Config)
        assert ProductionConfig.DEBUG is False

    def test_testing_config_inherits_from_base(self):
        """Verify TestingConfig inherits from Config."""
        from app.config import TestingConfig, Config

        assert issubclass(TestingConfig, Config)
        assert TestingConfig.TESTING is True
        assert TestingConfig.CACHE_TYPE == 'NullCache'

    def test_config_dictionary_contains_all_configs(self):
        """Verify config dictionary contains all configuration classes."""
        from app.config import config

        assert 'development' in config
        assert 'production' in config
        assert 'testing' in config
        assert 'default' in config

    def test_config_dictionary_default_points_to_development(self):
        """Verify default config points to DevelopmentConfig."""
        from app.config import config, DevelopmentConfig

        assert config['default'] == DevelopmentConfig


class TestBlueprintRegistration:
    """Test suite for new blueprint-based architecture."""

    def test_auth_blueprint_registered(self, app):
        """Verify that auth blueprint is registered."""
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # The auth blueprint routes should be registered
        assert any('/auth/' in route for route in routes), \
            "Auth blueprint routes not found"

    def test_graphrag_blueprint_registered(self, app):
        """Verify that graphrag blueprint is registered."""
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # The graphrag blueprint routes should be registered
        assert any('/api/graphrag/' in route for route in routes), \
            "GraphRAG blueprint routes not found"

    def test_ai_search_blueprint_registered(self, app):
        """Verify that AI search blueprint is registered."""
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # The AI search blueprint routes should be registered
        assert any('/api/ai/search/' in route for route in routes), \
            "AI Search blueprint routes not found"

    def test_quality_blueprint_registered(self, app):
        """Verify that quality blueprint is registered."""
        routes = [str(rule) for rule in app.url_map.iter_rules()]

        # The quality blueprint routes should be registered
        assert any('/api/ai/quality/' in route for route in routes), \
            "Quality blueprint routes not found"

    def test_all_expected_blueprints_present(self, app):
        """Verify all expected blueprints are registered."""
        blueprint_names = [bp.name for bp in app.blueprints.values()]

        expected_blueprints = ['auth', 'graphrag', 'ai_search', 'quality']

        for bp_name in expected_blueprints:
            assert bp_name in blueprint_names, f"Blueprint '{bp_name}' not registered"
