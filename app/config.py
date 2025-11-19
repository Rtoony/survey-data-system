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

    # Database Configuration (SQLAlchemy Core)
    # Build connection string from individual environment variables or use direct URI
    @staticmethod
    def _build_database_uri():
        """Build PostgreSQL connection URI from environment variables."""
        # First, check for direct database URI
        direct_uri = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL')
        if direct_uri:
            # Heroku-style postgres:// needs to be converted to postgresql://
            if direct_uri.startswith('postgres://'):
                direct_uri = direct_uri.replace('postgres://', 'postgresql://', 1)
            return direct_uri

        # Otherwise, build from individual components
        host = os.getenv('PGHOST') or os.getenv('DB_HOST', 'localhost')
        port = os.getenv('PGPORT') or os.getenv('DB_PORT', '5432')
        database = os.getenv('PGDATABASE') or os.getenv('DB_NAME', 'postgres')
        user = os.getenv('PGUSER') or os.getenv('DB_USER', 'postgres')
        password = os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD', '')

        # Build PostgreSQL URI
        uri = f'postgresql://{user}:{password}@{host}:{port}/{database}'

        # Add SSL mode if required
        sslmode = os.getenv('DB_SSLMODE', 'require')
        if sslmode and sslmode != 'disable':
            uri += f'?sslmode={sslmode}'

        return uri

    SQLALCHEMY_DATABASE_URI = _build_database_uri.__func__()

    # SQLAlchemy Pool Configuration
    SQLALCHEMY_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
    SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    SQLALCHEMY_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hour
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'false').lower() == 'true'

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
