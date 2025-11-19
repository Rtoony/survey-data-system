"""
Alembic Environment Configuration for SQLAlchemy Core + Flask Integration

This module configures Alembic to work with:
- SQLAlchemy Core (not ORM)
- Flask application factory pattern
- PostgreSQL with PostGIS extension
- Custom metadata from app.data_models
"""
from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Import the Flask app factory and SQLAlchemy Core metadata
from app import create_app
from app.data_models import metadata

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
# This points to our SQLAlchemy Core metadata from app.data_models
target_metadata = metadata


def get_database_url() -> str:
    """
    Get the database URL from Flask app configuration.

    This ensures that Alembic uses the same database connection
    settings as the Flask application.

    Returns:
        Database URL string
    """
    # Create Flask app to access configuration
    flask_app = create_app()

    # Get the database URI from Flask config
    database_url = flask_app.config.get('SQLALCHEMY_DATABASE_URI')

    if not database_url:
        raise ValueError(
            "SQLALCHEMY_DATABASE_URI not found in Flask configuration. "
            "Please ensure your .env file or environment variables are set correctly."
        )

    return database_url


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the
    Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    # Get database URL from Flask config
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    # Get database URL from Flask config
    database_url = get_database_url()

    # Override the sqlalchemy.url in the config
    configuration = config.get_section(config.config_ini_section) or {}
    configuration['sqlalchemy.url'] = database_url

    # Create engine with appropriate settings
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Use NullPool for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default value changes
            # Important: Configure how to handle PostGIS types
            render_as_batch=False,  # PostgreSQL supports transactional DDL
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
