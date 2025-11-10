"""
Database connection and query utilities
Shared across the application
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('PGHOST') or os.getenv('DB_HOST'),
    'port': os.getenv('PGPORT') or os.getenv('DB_PORT', '5432'),
    'database': os.getenv('PGDATABASE') or os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('PGUSER') or os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
    'sslmode': 'require',
    'connect_timeout': 10
}

@contextmanager
def get_db():
    """Get database connection with autocommit enabled"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None):
    """Execute query and return results"""
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            try:
                return [dict(row) for row in cur.fetchall()]
            except:
                return []
