"""
Application Configuration
Centralized configuration management
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration class"""

    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Session Configuration
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.getenv('SESSION_TIMEOUT_HOURS', '8')) * 3600

    # Cache Configuration
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 3600  # 1 hour hard limit
    CELERY_TASK_SOFT_TIME_LIMIT = 3300  # 55 minutes soft limit


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

    # Celery Development Settings
    CELERY_TASK_ALWAYS_EAGER = False  # Set to True to run tasks synchronously for debugging
    CELERY_TASK_EAGER_PROPAGATES = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # Celery Production Settings
    CELERY_TASK_ALWAYS_EAGER = False
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    CACHE_TYPE = 'NullCache'  # Disable caching in tests

    # Celery Testing Settings - Run tasks synchronously in tests
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks immediately (synchronously)
    CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions in eager mode
    CELERY_BROKER_URL = 'memory://'  # Use in-memory broker for tests
    CELERY_RESULT_BACKEND = 'cache+memory://'  # Use in-memory result backend


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
