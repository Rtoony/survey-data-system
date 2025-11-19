"""
Celery Worker Entry Point

This module initializes the Celery worker process for handling asynchronous tasks.
The worker is designed to execute long-running operations (such as DXF imports)
in the background while keeping the Flask application responsive.

Architecture:
    - Celery is configured via the Flask application factory pattern
    - Separate queues for testing and production environments
    - Redis backend for result storage and message broker
    - Worker can be scaled horizontally by running multiple instances

Usage:
    Development (with auto-reload):
        celery -A celery_worker.celery worker --loglevel=info --pool=solo

    Production:
        celery -A celery_worker.celery worker --loglevel=info --concurrency=4

    With specific queue:
        celery -A celery_worker.celery worker -Q dxf_imports --loglevel=info

Dependencies:
    - Redis server must be running (default: localhost:6379)
    - Flask app configuration must include Celery settings
    - Database connection pool should be configured for multi-worker usage

Author: The Builder (Phase 8: Asynchronous Infrastructure)
"""

import os
from app import create_app
from app.celery_config import create_celery_app

# Determine environment from FLASK_ENV or default to development
config_name = os.getenv('FLASK_ENV', 'development')

# Create Flask application instance
flask_app = create_app(config_name)

# Create and configure Celery application
celery = create_celery_app(flask_app)

if __name__ == '__main__':
    """
    Direct execution for debugging purposes.
    In production, use the celery CLI command shown above.
    """
    celery.start()
