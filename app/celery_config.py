"""
Celery Application Configuration

This module provides the Celery application factory that integrates with Flask.
It follows the application factory pattern to ensure proper configuration
inheritance from the Flask app.

Architecture:
    - Celery is configured using Flask app settings
    - Task context is automatically bridged to Flask app context
    - Supports multiple configuration environments (dev, prod, test)
    - Redis backend for message broker and result storage

Key Features:
    - Automatic Flask app context management for tasks
    - Configuration inheritance from Flask config
    - Separate queues for different task types
    - Task result expiration and cleanup
    - Error handling and retry policies

Author: The Builder (Phase 8: Asynchronous Infrastructure)
"""

from typing import TYPE_CHECKING
from celery import Celery

if TYPE_CHECKING:
    from flask import Flask


def create_celery_app(flask_app: 'Flask') -> Celery:
    """
    Create and configure a Celery application instance.

    This factory function integrates Celery with the Flask application,
    ensuring that Celery tasks have access to Flask configuration and
    application context.

    Args:
        flask_app: Configured Flask application instance

    Returns:
        Configured Celery application instance

    Configuration:
        The Celery app inherits all settings from Flask config that start
        with 'CELERY_'. Key settings include:
            - CELERY_BROKER_URL: Redis connection string for message broker
            - CELERY_RESULT_BACKEND: Redis connection for result storage
            - CELERY_TASK_SERIALIZER: Serialization format (json)
            - CELERY_TASK_TIME_LIMIT: Maximum task execution time
            - CELERY_TASK_ALWAYS_EAGER: Run tasks synchronously (testing)

    Task Context:
        All tasks automatically run within Flask application context,
        providing access to:
            - Flask config via current_app.config
            - Database connections via app context
            - Extensions (cache, cors, etc.)

    Example:
        >>> from app import create_app
        >>> from app.celery_config import create_celery_app
        >>> flask_app = create_app('production')
        >>> celery = create_celery_app(flask_app)
        >>> celery.start()

    Usage in Tasks:
        >>> from celery import current_app as celery_app
        >>> from flask import current_app
        >>>
        >>> @celery_app.task
        >>> def my_task():
        >>>     # Flask app context is automatically available
        >>>     broker_url = current_app.config['CELERY_BROKER_URL']
        >>>     return {'status': 'success'}
    """

    # Create Celery instance with Flask app name
    celery = Celery(
        flask_app.import_name,
        broker=flask_app.config.get('CELERY_BROKER_URL'),
        backend=flask_app.config.get('CELERY_RESULT_BACKEND')
    )

    # Update Celery config from Flask config
    # All Flask config keys starting with 'CELERY_' are used
    celery.conf.update(flask_app.config)

    # Additional Celery-specific configuration
    celery.conf.update(
        # Task Configuration
        task_serializer=flask_app.config.get('CELERY_TASK_SERIALIZER', 'json'),
        result_serializer=flask_app.config.get('CELERY_RESULT_SERIALIZER', 'json'),
        accept_content=flask_app.config.get('CELERY_ACCEPT_CONTENT', ['json']),
        timezone=flask_app.config.get('CELERY_TIMEZONE', 'UTC'),
        enable_utc=flask_app.config.get('CELERY_ENABLE_UTC', True),

        # Task Execution
        task_track_started=flask_app.config.get('CELERY_TASK_TRACK_STARTED', True),
        task_time_limit=flask_app.config.get('CELERY_TASK_TIME_LIMIT', 3600),
        task_soft_time_limit=flask_app.config.get('CELERY_TASK_SOFT_TIME_LIMIT', 3300),

        # Result Backend
        result_expires=3600,  # Results expire after 1 hour
        result_extended=True,  # Store additional task metadata

        # Worker Configuration
        worker_prefetch_multiplier=1,  # Fetch one task at a time (for long tasks)
        worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)

        # Task Routing
        task_routes={
            'app.tasks.process_dxf_import': {'queue': 'dxf_imports'},
            'app.tasks.*': {'queue': 'default'}
        },

        # Retry Policy
        task_default_retry_delay=300,  # 5 minutes between retries
        task_max_retries=3,
    )

    # Create a context manager class to bridge Flask and Celery contexts
    class ContextTask(celery.Task):
        """
        Custom Task class that runs within Flask application context.

        This ensures that all Celery tasks have access to Flask's
        current_app, config, extensions, and other context-dependent
        features.
        """

        def __call__(self, *args, **kwargs):
            """
            Execute the task within Flask application context.

            This method is called when a task is invoked. It ensures
            the Flask app context is active during task execution.
            """
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    # Register the custom task class
    celery.Task = ContextTask

    # Auto-discover tasks from app.tasks module
    # This ensures all @celery_app.task decorated functions are registered
    celery.autodiscover_tasks(['app'], force=True)

    return celery


# ==================== Celery CLI Integration ====================

def get_celery_app() -> Celery:
    """
    Get the configured Celery application for CLI usage.

    This function is used by the celery_worker.py entry point
    to retrieve the Celery instance.

    Returns:
        Configured Celery application

    Note:
        This is a convenience function for the Celery CLI.
        In most cases, you should use create_celery_app() directly.
    """
    from app import create_app
    import os

    # Determine environment
    config_name = os.getenv('FLASK_ENV', 'development')

    # Create Flask app
    flask_app = create_app(config_name)

    # Create and return Celery app
    return create_celery_app(flask_app)
