"""
Application Factory
Creates and configures the Flask application instance
"""
from flask import Flask
from flask.json.provider import DefaultJSONProvider
from datetime import datetime, date
from decimal import Decimal
import uuid
import os

from app.extensions import cors, cache
from app.config import config
from database import DB_CONFIG


class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider for datetime, date, Decimal, and UUID objects (Flask 2.2+)"""

    def default(self, o):  # type: ignore[override]
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, uuid.UUID):
            return str(o)
        return super().default(o)


def create_app(config_name: str = None) -> Flask:
    """
    Application Factory Pattern
    Creates and configures the Flask application

    Args:
        config_name: Configuration name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV or defaults to 'development'

    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    flask_app = Flask(__name__,
                      template_folder='../templates',
                      static_folder='../static')

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    flask_app.config.from_object(config[config_name])

    # Set custom JSON provider
    flask_app.json = CustomJSONProvider(flask_app)

    # Initialize extensions
    cors.init_app(flask_app)
    cache.init_app(flask_app)

    # Debug: Print database configuration status
    print("=" * 50)
    print("Database Configuration Status:")
    print(f"DB_HOST: {'SET' if DB_CONFIG['host'] else 'MISSING'}")
    print(f"DB_USER: {'SET' if DB_CONFIG['user'] else 'MISSING'}")
    print(f"DB_NAME: {'SET' if DB_CONFIG['database'] else 'MISSING'}")
    print(f"DB_PASSWORD: {'SET' if DB_CONFIG['password'] else 'MISSING'}")
    print("=" * 50)

    # Register blueprints
    from auth.routes import auth_bp
    from api.graphrag_routes import graphrag_bp
    from api.ai_search_routes import ai_search_bp
    from api.quality_routes import quality_bp
    from app.blueprints.projects import projects_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(graphrag_bp)
    flask_app.register_blueprint(ai_search_bp)
    flask_app.register_blueprint(quality_bp)
    flask_app.register_blueprint(projects_bp)

    return flask_app
