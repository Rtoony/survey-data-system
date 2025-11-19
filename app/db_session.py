"""
SQLAlchemy Core Database Session Manager
Provides thread-safe connection pooling and context management for Flask

This module replaces the raw psycopg2 connection handling with a robust,
production-ready SQLAlchemy Core layer that provides:
- Connection pooling with configurable limits
- Thread-safe database access using contextvars
- Automatic transaction management
- Connection lifecycle management
- Performance monitoring hooks
"""

from typing import Optional, Generator
from contextlib import contextmanager
from contextvars import ContextVar
import logging

from sqlalchemy import create_engine, event, Connection, Engine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app, g, has_app_context

# ============================================================================
# MODULE-LEVEL CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

# Thread-safe storage for database connections
# Uses contextvars for proper async/thread isolation
_db_connection: ContextVar[Optional[Connection]] = ContextVar('_db_connection', default=None)

# Global engine instance (lazy-initialized)
_engine: Optional[Engine] = None


# ============================================================================
# ENGINE INITIALIZATION
# ============================================================================

def init_engine(app=None, database_uri: Optional[str] = None) -> Engine:
    """
    Initialize the SQLAlchemy engine with connection pooling.

    This should be called once during application startup, typically from
    the Flask application factory.

    Args:
        app: Flask application instance (optional)
        database_uri: SQLAlchemy database URI (optional, falls back to app config)

    Returns:
        Configured SQLAlchemy Engine instance

    Example:
        >>> from flask import Flask
        >>> from app.db_session import init_engine
        >>> app = Flask(__name__)
        >>> engine = init_engine(app)
    """
    global _engine

    if _engine is not None:
        logger.warning("Engine already initialized. Returning existing instance.")
        return _engine

    # Get database URI from config
    if database_uri is None:
        if app is not None:
            database_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        else:
            raise ValueError("Either 'app' or 'database_uri' must be provided")

    if not database_uri:
        raise ValueError("SQLALCHEMY_DATABASE_URI not found in app config")

    # Determine pool class based on environment
    pool_class = QueuePool
    if app and app.config.get('TESTING'):
        # Use NullPool for testing to avoid connection issues
        pool_class = NullPool
        logger.info("Using NullPool for testing environment")

    # Create engine with production-ready settings
    _engine = create_engine(
        database_uri,
        poolclass=pool_class,
        pool_size=10,              # Number of connections to maintain
        max_overflow=20,           # Additional connections when pool is exhausted
        pool_timeout=30,           # Seconds to wait for connection from pool
        pool_pre_ping=True,        # Test connections before using them
        pool_recycle=3600,         # Recycle connections after 1 hour
        echo=False,                # Set to True to log all SQL statements
        future=True,               # Use SQLAlchemy 2.0 style
        connect_args={
            'connect_timeout': 10,
            'options': '-c statement_timeout=300000'  # 5 minute query timeout
        }
    )

    # Register event listeners for monitoring
    _register_event_listeners(_engine)

    logger.info(f"SQLAlchemy engine initialized with {pool_class.__name__}")

    return _engine


def get_engine() -> Engine:
    """
    Get the global SQLAlchemy engine instance.

    Raises:
        RuntimeError: If engine has not been initialized

    Returns:
        The configured Engine instance
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine not initialized. Call init_engine() first, "
            "typically from your Flask application factory."
        )
    return _engine


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager for database connections with automatic transaction management.

    This is the PRIMARY method for executing database queries. It provides:
    - Automatic connection checkout from pool
    - Transaction management (commit on success, rollback on error)
    - Connection cleanup and return to pool
    - Thread-safe operation via contextvars

    Usage:
        >>> from app.db_session import get_db_connection
        >>> from app.data_models import projects
        >>>
        >>> with get_db_connection() as conn:
        >>>     result = conn.execute(
        >>>         projects.select().where(projects.c.project_name == 'Demo Project')
        >>>     )
        >>>     rows = result.fetchall()

    Yields:
        SQLAlchemy Connection object

    Raises:
        SQLAlchemyError: On database errors (after rollback)
    """
    engine = get_engine()

    # Check if we're already in a connection context
    existing_conn = _db_connection.get()
    if existing_conn is not None:
        # Reuse existing connection (nested context)
        logger.debug("Reusing existing database connection")
        yield existing_conn
        return

    # Create new connection
    conn = engine.connect()
    _db_connection.set(conn)

    try:
        # Begin transaction
        trans = conn.begin()

        logger.debug("Database connection acquired from pool")
        yield conn

        # Commit transaction on success
        trans.commit()
        logger.debug("Transaction committed successfully")

    except Exception as e:
        # Rollback on any error
        trans.rollback()
        logger.error(f"Transaction rolled back due to error: {e}")
        raise

    finally:
        # Clean up connection context
        _db_connection.set(None)
        conn.close()
        logger.debug("Database connection returned to pool")


def get_flask_db_connection() -> Connection:
    """
    Get a database connection bound to Flask request context (g object).

    This is useful for Flask routes where you want a single connection
    per request that's automatically cleaned up after the request.

    The connection is cached in Flask's 'g' object and reused for the
    entire request lifecycle.

    Usage in Flask route:
        >>> from flask import Blueprint
        >>> from app.db_session import get_flask_db_connection
        >>> from app.data_models import projects
        >>>
        >>> @bp.route('/projects')
        >>> def list_projects():
        >>>     conn = get_flask_db_connection()
        >>>     result = conn.execute(projects.select())
        >>>     return jsonify([dict(row) for row in result])

    Returns:
        SQLAlchemy Connection object bound to request context

    Raises:
        RuntimeError: If called outside Flask request context
    """
    if not has_app_context():
        raise RuntimeError("get_flask_db_connection() must be called within Flask app context")

    # Check if connection already exists in request context
    if 'db_connection' not in g:
        engine = get_engine()
        g.db_connection = engine.connect()
        g.db_transaction = g.db_connection.begin()
        logger.debug("Created new database connection for Flask request")

    return g.db_connection


def close_flask_db_connection(error=None):
    """
    Close the database connection for the current Flask request.

    This should be registered as a teardown handler in your Flask app:

        >>> from app.db_session import close_flask_db_connection
        >>> app.teardown_appcontext(close_flask_db_connection)

    Args:
        error: Exception that triggered teardown (if any)
    """
    db_connection = g.pop('db_connection', None)
    db_transaction = g.pop('db_transaction', None)

    if db_connection is not None:
        try:
            if error is None:
                # Commit transaction on successful request
                db_transaction.commit()
                logger.debug("Flask request transaction committed")
            else:
                # Rollback on error
                db_transaction.rollback()
                logger.error(f"Flask request transaction rolled back: {error}")
        finally:
            db_connection.close()
            logger.debug("Flask request connection closed")


# ============================================================================
# EVENT LISTENERS (Performance Monitoring & Logging)
# ============================================================================

def _register_event_listeners(engine: Engine) -> None:
    """
    Register SQLAlchemy event listeners for monitoring and debugging.

    These listeners provide:
    - Connection pool checkout/checkin logging
    - Query performance monitoring
    - Connection lifecycle tracking

    Args:
        engine: SQLAlchemy engine to attach listeners to
    """

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log when new connections are created."""
        logger.debug("New database connection established")

    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log when connections are checked out from pool."""
        logger.debug("Connection checked out from pool")

    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        """Log when connections are returned to pool."""
        logger.debug("Connection returned to pool")

    # Optional: Add query timing for performance monitoring
    # Uncomment to enable query performance logging
    # @event.listens_for(engine, "before_cursor_execute")
    # def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    #     conn.info.setdefault('query_start_time', []).append(time.time())
    #     logger.debug(f"Executing query: {statement[:100]}...")
    #
    # @event.listens_for(engine, "after_cursor_execute")
    # def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    #     total = time.time() - conn.info['query_start_time'].pop(-1)
    #     logger.debug(f"Query completed in {total:.4f}s")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def dispose_engine() -> None:
    """
    Dispose of the engine and close all connections.

    This should be called during application shutdown or when
    reinitializing the database connection.
    """
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")


def get_pool_status() -> dict:
    """
    Get current connection pool status for monitoring.

    Returns:
        Dictionary with pool statistics including:
        - size: Current pool size
        - checked_out: Connections currently in use
        - overflow: Overflow connections in use
        - checked_in: Available connections

    Example:
        >>> from app.db_session import get_pool_status
        >>> status = get_pool_status()
        >>> print(f"Active connections: {status['checked_out']}")
    """
    engine = get_engine()
    pool = engine.pool

    return {
        'size': pool.size(),
        'checked_out': pool.checkedout(),
        'overflow': pool.overflow(),
        'checked_in': pool.size() - pool.checkedout()
    }


# ============================================================================
# FLASK INTEGRATION
# ============================================================================

def init_app(app) -> None:
    """
    Initialize database session management with Flask app.

    This should be called from your application factory:

        >>> from flask import Flask
        >>> from app import db_session
        >>>
        >>> def create_app():
        >>>     app = Flask(__name__)
        >>>     db_session.init_app(app)
        >>>     return app

    Args:
        app: Flask application instance
    """
    # Initialize engine
    init_engine(app)

    # Register teardown handler
    app.teardown_appcontext(close_flask_db_connection)

    # Add health check endpoint
    @app.route('/api/db/health')
    def db_health_check():
        """Database health check endpoint."""
        try:
            with get_db_connection() as conn:
                result = conn.execute("SELECT 1 as health")
                row = result.fetchone()

            pool_status = get_pool_status()

            return {
                'status': 'healthy',
                'pool': pool_status
            }, 200

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }, 500

    logger.info("Database session management initialized with Flask app")
