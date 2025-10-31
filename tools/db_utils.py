"""
Database utilities for ACAD-GIS AI-first database operations.
Provides connection pooling and helper functions for common operations.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection pool
_pool = None


def init_pool(minconn=1, maxconn=10):
    """Initialize database connection pool."""
    global _pool
    if _pool is None:
        # Check for DATABASE_URL first (Replit/Heroku style)
        database_url = os.environ.get('DATABASE_URL')
        
        # Otherwise construct from individual components
        if not database_url:
            db_config = {
                'host': os.getenv('DB_HOST'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'postgres'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD'),
                'sslmode': 'require'
            }
            
            if not db_config['host'] or not db_config['password']:
                raise ValueError("Database configuration not set. Need DATABASE_URL or DB_HOST/DB_PASSWORD")
            
            _pool = SimpleConnectionPool(minconn, maxconn, **db_config)
        else:
            _pool = SimpleConnectionPool(minconn, maxconn, database_url)
    return _pool


@contextmanager
def get_connection():
    """Get a connection from the pool with automatic return."""
    pool = init_pool()
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor(dict_cursor=True):
    """Get a cursor with automatic commit/rollback."""
    with get_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True) -> Optional[List[Dict]]:
    """Execute a query and optionally fetch results."""
    with get_cursor() as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return None


def execute_many(query: str, params_list: List[tuple]):
    """Execute a query with multiple parameter sets efficiently."""
    with get_cursor() as cursor:
        execute_batch(cursor, query, params_list, page_size=100)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def get_or_create_entity(
    entity_type: str,
    canonical_name: str,
    source_table: str,
    source_id: str,
    tags: Optional[List[str]] = None,
    attributes: Optional[Dict] = None
) -> str:
    """
    Get existing entity_id or create a new entity in standards_entities.
    Returns the entity_id (UUID).
    """
    # Check if entity already exists
    query = """
        SELECT entity_id FROM standards_entities
        WHERE entity_type = %s AND canonical_name = %s
    """
    result = execute_query(query, (entity_type, canonical_name))
    
    if result and len(result) > 0:
        return str(result[0]['entity_id'])
    
    # Create new entity
    entity_id = generate_uuid()
    insert_query = """
        INSERT INTO standards_entities (
            entity_id, entity_type, canonical_name, source_table, source_id,
            tags, attributes, quality_score
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 0.5)
        RETURNING entity_id
    """
    tags = tags or []
    attributes = attributes or {}
    
    result = execute_query(
        insert_query,
        (entity_id, entity_type, canonical_name, source_table, source_id, tags, attributes)
    )
    if result:
        return str(result[0]['entity_id'])
    return entity_id


def update_quality_score(entity_id: str, required_fields_filled: int, total_required: int = 10):
    """Update quality score for an entity using the compute_quality_score function."""
    query = """
        UPDATE standards_entities
        SET quality_score = compute_quality_score(
            %s::integer,
            %s::integer,
            EXISTS(SELECT 1 FROM entity_embeddings WHERE entity_id = %s AND is_current = true),
            EXISTS(SELECT 1 FROM entity_relationships WHERE subject_entity_id = %s OR object_entity_id = %s)
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE entity_id = %s
    """
    execute_query(query, (required_fields_filled, total_required, entity_id, entity_id, entity_id, entity_id), fetch=False)


def refresh_materialized_views():
    """Refresh all materialized views."""
    views = [
        'mv_survey_points_enriched',
        'mv_entity_graph_summary',
        'mv_spatial_clusters'
    ]
    
    with get_cursor() as cursor:
        for view in views:
            print(f"Refreshing {view}...")
            cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
    
    print("All materialized views refreshed successfully")


def get_table_stats() -> Dict[str, int]:
    """Get row counts for all major tables."""
    query = """
        SELECT 
            schemaname,
            relname as tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC
        LIMIT 20
    """
    results = execute_query(query)
    return {row['tablename']: row['row_count'] for row in results} if results else {}


def get_entity_stats() -> Dict[str, Any]:
    """Get statistics about entities and embeddings."""
    stats: Dict[str, Any] = {}
    
    # Total entities
    result = execute_query("SELECT COUNT(*) as count FROM standards_entities")
    stats['total_entities'] = result[0]['count'] if result else 0
    
    # Entities by type
    result = execute_query("""
        SELECT entity_type, COUNT(*) as count 
        FROM standards_entities 
        GROUP BY entity_type 
        ORDER BY count DESC
    """)
    stats['entities_by_type'] = {row['entity_type']: row['count'] for row in result} if result else {}
    
    # Embeddings count
    result = execute_query("""
        SELECT COUNT(*) as total, 
               COUNT(CASE WHEN is_current THEN 1 END) as current
        FROM entity_embeddings
    """)
    stats['embeddings'] = dict(result[0]) if result else {'total': 0, 'current': 0}
    
    # Relationships count
    result = execute_query("SELECT COUNT(*) as count FROM entity_relationships")
    stats['relationships'] = result[0]['count'] if result else 0
    
    # Average quality score
    result = execute_query("""
        SELECT 
            AVG(quality_score) as avg_quality,
            MIN(quality_score) as min_quality,
            MAX(quality_score) as max_quality
        FROM standards_entities
        WHERE quality_score IS NOT NULL
    """)
    stats['quality'] = dict(result[0]) if result else {'avg_quality': None, 'min_quality': None, 'max_quality': None}
    
    return stats
