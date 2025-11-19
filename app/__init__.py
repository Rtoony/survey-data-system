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
from app.db_session import init_app as init_db_session


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

    # Initialize database session management
    init_db_session(flask_app)

    # Debug: Print database configuration status
    print("=" * 50)
    print("Database Configuration Status:")
    print(f"SQLAlchemy Engine: {'Initialized' if flask_app.config.get('SQLALCHEMY_DATABASE_URI') else 'MISSING'}")
    print("=" * 50)

    # Register blueprints
    from auth.routes import auth_bp
    from api.graphrag_routes import graphrag_bp
    from api.ai_search_routes import ai_search_bp
    from api.quality_routes import quality_bp
    from app.blueprints.projects import projects_bp
    from app.blueprints.standards import standards_bp
    from app.blueprints.gis_engine import gis_bp
    # Phase 13 extracted blueprints
    from app.blueprints.blocks_management import blocks_bp
    from app.blueprints.details_management import details_bp
    from app.blueprints.pipe_networks import pipes_bp
    from app.blueprints.specialized_tools import specialized_tools_bp
    from app.blueprints.survey_codes import survey_codes_bp
    from app.blueprints.classification import classification_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(graphrag_bp)
    flask_app.register_blueprint(ai_search_bp)
    flask_app.register_blueprint(quality_bp)
    flask_app.register_blueprint(projects_bp)
    flask_app.register_blueprint(standards_bp)
    flask_app.register_blueprint(gis_bp)
    # Phase 13 blueprints
    flask_app.register_blueprint(blocks_bp)
    flask_app.register_blueprint(details_bp)
    flask_app.register_blueprint(pipes_bp)
    flask_app.register_blueprint(specialized_tools_bp)
    flask_app.register_blueprint(survey_codes_bp)
    flask_app.register_blueprint(classification_bp)

    return flask_app
