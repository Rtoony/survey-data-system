"""
Database connection and query utilities
Shared across the application
Uses SQLAlchemy for robust connection pooling and resource management.
"""
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Build DATABASE_URL from environment variables
def _build_database_url() -> str:
    """Construct PostgreSQL connection URL from environment variables."""
    host = os.getenv('PGHOST') or os.getenv('DB_HOST')
    port = os.getenv('PGPORT') or os.getenv('DB_PORT', '5432')
    database = os.getenv('PGDATABASE') or os.getenv('DB_NAME', 'postgres')
    user = os.getenv('PGUSER') or os.getenv('DB_USER', 'postgres')
    password = os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD')

    if not all([host, database, user, password]):
        logger.warning("Missing database configuration. Using default localhost connection.")
        return "postgresql://postgres:postgres@localhost:5432/postgres"

    # Include SSL mode and connect timeout in connection args
    return f"postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require&connect_timeout=10"

DATABASE_URL = _build_database_url()

# Centralized Engine (singleton pattern for connection pooling)
_engine: Optional[Engine] = None

def get_engine() -> Engine:
    """
    Initializes and returns the global database engine.
    This engine handles connection pooling and thread safety.
    Connection pool is configured with:
    - pool_size: Number of connections to maintain
    - max_overflow: Additional connections when pool is exhausted
    - pool_pre_ping: Verify connections before using (handles stale connections)
    """
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(
                DATABASE_URL,
                poolclass=QueuePool,
                pool_size=10,           # Base pool size
                max_overflow=20,        # Additional connections when needed
                pool_pre_ping=True,     # Verify connection validity before use
                pool_recycle=3600,      # Recycle connections after 1 hour
                echo=False              # Set to True for SQL debugging
            )
            logger.info("Database Engine initialized with connection pooling.")
        except Exception as e:
            logger.critical(f"FATAL: Could not initialize database engine: {e}")
            raise RuntimeError(f"Database connection failure: {e}")
    return _engine

@contextmanager
def get_db():
    """
    Provides a database connection as a context manager.

    This ensures the connection is properly returned to the pool (closed) on exit,
    preventing resource leaks and connection exhaustion.

    Usage:
        with get_db() as conn:
            result = conn.execute(text("SELECT * FROM table"))
            for row in result:
                print(row)

    The connection is automatically closed/returned to pool when exiting the with block.
    """
    conn = None
    try:
        engine = get_engine()
        conn = engine.connect()
        logger.debug("Database connection acquired from pool.")
        yield conn
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        # Reraise the exception for the calling service to handle
        raise
    finally:
        if conn:
            conn.close()  # CRITICAL: Returns the connection to the pool
            logger.debug("Database connection released back to pool.")

def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a query and return results as a list of dictionaries.

    Args:
        query: SQL query string (use :param_name for parameters)
        params: Dictionary of parameters to bind to the query

    Returns:
        List of dictionaries representing rows

    Example:
        results = execute_query(
            "SELECT * FROM users WHERE id = :user_id",
            {"user_id": 123}
        )
    """
    with get_db() as conn:
        try:
            result = conn.execute(text(query), params or {})
            # Convert rows to dictionaries
            rows = result.fetchall()
            if rows:
                # Get column names from result
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}, Params: {params}")
            raise
