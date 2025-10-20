"""
Database connection and query helpers for ACAD=GIS.
Handles all PostgreSQL + pgvector operations.
"""

import os
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
import uuid

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Database configuration - loads from .env file
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': 'prefer',  # More forgiving than 'require'
    'connect_timeout': 10,
    'keepalives': 1,
    'keepalives_idle': 30,
    'keepalives_interval': 10,
    'keepalives_count': 5
}

# Validate required environment variables
required_vars = ['DB_HOST', 'DB_PASSWORD']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    raise Exception(
        f"Missing required environment variables: {', '.join(missing_vars)}\n"
        f"Please create a .env file with these variables or set them in your environment."
    )


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Execute a SQL query and return results."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                return [dict(row) for row in cur.fetchall()]
            return []

def execute_single(query: str, params: tuple = None) -> Optional[Dict]:
    """Execute a SQL query and return single result."""
    results = execute_query(query, params, fetch=True)
    return results[0] if results else None

# ============================================
# BLOCK DEFINITIONS (SYMBOLS)
# ============================================

def create_block_definition(
    block_name: str,
    svg_content: str,
    domain: str = None,
    category: str = None,
    semantic_type: str = None,
    semantic_label: str = None,
    usage_context: str = None,
    tags: List[str] = None,
    metadata: Dict = None
) -> str:
    """Create a new block definition (symbol)."""
    
    block_id = str(uuid.uuid4())
    
    query = """
        INSERT INTO block_definitions (
            block_id, block_name, svg_content, domain, category,
            semantic_type, semantic_label, usage_context, tags, metadata,
            space_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (block_name) DO UPDATE SET
            svg_content = EXCLUDED.svg_content,
            domain = EXCLUDED.domain,
            category = EXCLUDED.category,
            semantic_type = EXCLUDED.semantic_type,
            semantic_label = EXCLUDED.semantic_label,
            usage_context = EXCLUDED.usage_context,
            tags = EXCLUDED.tags,
            metadata = EXCLUDED.metadata
        RETURNING block_id
    """
    
    result = execute_single(query, (
        block_id, block_name, svg_content, domain, category,
        semantic_type, semantic_label, usage_context, tags,
        Json(metadata) if metadata else None, 'BOTH'
    ))
    
    return result['block_id']

def get_block_definition(block_name: str) -> Optional[Dict]:
    """Get block definition by name."""
    query = "SELECT * FROM block_definitions WHERE block_name = %s"
    return execute_single(query, (block_name,))

def get_all_blocks() -> List[Dict]:
    """Get all block definitions."""
    return execute_query("SELECT * FROM block_definitions ORDER BY block_name")

# ============================================
# DRAWINGS
# ============================================

def create_drawing(
    project_id: str,
    drawing_name: str,
    drawing_number: str = None,
    drawing_type: str = None,
    scale: str = None,
    dxf_content: str = None,
    description: str = None,
    tags: List[str] = None,
    metadata: Dict = None
) -> str:
    """Create a new drawing record."""
    
    drawing_id = str(uuid.uuid4())
    
    query = """
        INSERT INTO drawings (
            drawing_id, project_id, drawing_name, drawing_number,
            drawing_type, scale, dxf_content, description, tags, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING drawing_id
    """
    
    result = execute_single(query, (
        drawing_id, project_id, drawing_name, drawing_number,
        drawing_type, scale, dxf_content, description, tags,
        Json(metadata) if metadata else None
    ))
    
    return result['drawing_id']

def get_drawing(drawing_id: str) -> Optional[Dict]:
    """Get drawing by ID."""
    query = "SELECT * FROM drawings WHERE drawing_id = %s"
    return execute_single(query, (drawing_id,))

def update_drawing_dxf(drawing_id: str, dxf_content: str):
    """Update the DXF content of a drawing."""
    query = """
        UPDATE drawings 
        SET dxf_content = %s, updated_at = CURRENT_TIMESTAMP
        WHERE drawing_id = %s
    """
    execute_query(query, (dxf_content, drawing_id), fetch=False)

# ============================================
# LAYERS
# ============================================

def create_layer(
    drawing_id: str,
    layer_name: str,
    color: int = None,
    linetype: str = 'CONTINUOUS',
    lineweight: float = 0.25,
    is_plottable: bool = True,
    is_locked: bool = False,
    is_frozen: bool = False,
    layer_standard_id: str = None
) -> str:
    """Create a layer for a specific drawing."""
    
    layer_id = str(uuid.uuid4())
    
    # Try to find matching layer standard
    if not layer_standard_id:
        standard = execute_single(
            "SELECT layer_standard_id FROM layer_standards WHERE layer_name = %s",
            (layer_name,)
        )
        if standard:
            layer_standard_id = standard['layer_standard_id']
    
    query = """
        INSERT INTO layers (
            layer_id, drawing_id, layer_name, color, linetype, lineweight,
            is_plottable, is_locked, is_frozen, layer_standard_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (drawing_id, layer_name) DO UPDATE SET
            color = EXCLUDED.color,
            linetype = EXCLUDED.linetype,
            lineweight = EXCLUDED.lineweight
        RETURNING layer_id
    """
    
    result = execute_single(query, (
        layer_id, drawing_id, layer_name, color, linetype, lineweight,
        is_plottable, is_locked, is_frozen, layer_standard_id
    ))
    
    return result['layer_id']

def get_layers(drawing_id: str) -> List[Dict]:
    """Get all layers for a drawing."""
    query = "SELECT * FROM layers WHERE drawing_id = %s ORDER BY layer_name"
    return execute_query(query, (drawing_id,))

# ============================================
# BLOCK INSERTS (SYMBOL PLACEMENTS)
# ============================================

def create_block_insert(
    drawing_id: str,
    block_name: str,
    insert_x: float,
    insert_y: float,
    insert_z: float = 0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    rotation: float = 0,
    layer_name: str = '0',
    metadata: Dict = None
) -> str:
    """Create a block insert (symbol placement)."""
    
    insert_id = str(uuid.uuid4())
    
    # Get block_id from block_name
    block = get_block_definition(block_name)
    if not block:
        raise ValueError(f"Block definition '{block_name}' not found")
    
    block_id = block['block_id']
    
    query = """
        INSERT INTO block_inserts (
            insert_id, drawing_id, block_id, insert_x, insert_y, insert_z,
            scale_x, scale_y, rotation, layout_name, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING insert_id
    """
    
    result = execute_single(query, (
        insert_id, drawing_id, block_id, insert_x, insert_y, insert_z,
        scale_x, scale_y, rotation, 'Model',
        Json(metadata) if metadata else None
    ))
    
    return result['insert_id']

def get_block_inserts(drawing_id: str) -> List[Dict]:
    """Get all block inserts for a drawing."""
    query = """
        SELECT 
            bi.*,
            bd.block_name,
            bd.domain,
            bd.category
        FROM block_inserts bi
        JOIN block_definitions bd ON bi.block_id = bd.block_id
        WHERE bi.drawing_id = %s
        ORDER BY bi.created_at
    """
    return execute_query(query, (drawing_id,))

# ============================================
# LAYER STANDARDS
# ============================================

def get_layer_standard(layer_name: str) -> Optional[Dict]:
    """Get layer standard by name."""
    query = "SELECT * FROM layer_standards WHERE layer_name = %s"
    return execute_single(query, (layer_name,))

def get_all_layer_standards() -> List[Dict]:
    """Get all layer standards."""
    return execute_query(
        "SELECT * FROM layer_standards ORDER BY display_order, layer_name"
    )

# ============================================
# PROJECTS
# ============================================

def create_project(
    project_name: str,
    project_number: str = None,
    client_name: str = None,
    description: str = None,
    metadata: Dict = None
) -> str:
    """Create a new project."""
    
    project_id = str(uuid.uuid4())
    
    query = """
        INSERT INTO projects (
            project_id, project_name, project_number, client_name,
            description, metadata
        ) VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING project_id
    """
    
    result = execute_single(query, (
        project_id, project_name, project_number, client_name,
        description, Json(metadata) if metadata else None
    ))
    
    return result['project_id']

def get_project(project_id: str) -> Optional[Dict]:
    """Get project by ID."""
    query = "SELECT * FROM projects WHERE project_id = %s"
    return execute_single(query, (project_id,))

# ============================================
# EMBEDDINGS
# ============================================

def update_block_embedding(block_id: str, embedding: List[float]):
    """Update block embedding vector."""
    query = """
        UPDATE block_definitions 
        SET block_embedding = %s
        WHERE block_id = %s
    """
    execute_query(query, (embedding, block_id), fetch=False)

def update_layer_embedding(layer_standard_id: str, embedding: List[float]):
    """Update layer standard embedding vector."""
    query = """
        UPDATE layer_standards 
        SET layer_embedding = %s
        WHERE layer_standard_id = %s
    """
    execute_query(query, (embedding, layer_standard_id), fetch=False)

def update_drawing_embedding(drawing_id: str, embedding: List[float]):
    """Update drawing embedding vector."""
    query = """
        UPDATE drawings 
        SET drawing_embedding = %s
        WHERE drawing_id = %s
    """
    execute_query(query, (embedding, drawing_id), fetch=False)

# ============================================
# SEMANTIC SEARCH
# ============================================

def vector_search(
    table: str,
    embedding_column: str,
    query_embedding: List[float],
    limit: int = 10
) -> List[Dict]:
    """
    Perform vector similarity search.
    
    Args:
        table: 'block_definitions', 'layer_standards', or 'drawings'
        embedding_column: 'block_embedding', 'layer_embedding', or 'drawing_embedding'
        query_embedding: Vector to search for
        limit: Number of results
    """
    
    id_column = {
        'block_definitions': 'block_id',
        'layer_standards': 'layer_standard_id',
        'drawings': 'drawing_id'
    }[table]
    
    name_column = {
        'block_definitions': 'block_name',
        'layer_standards': 'layer_name',
        'drawings': 'drawing_name'
    }[table]
    
    query = f"""
        SELECT 
            {id_column},
            {name_column},
            1 - ({embedding_column} <=> %s::vector) as similarity
        FROM {table}
        WHERE {embedding_column} IS NOT NULL
        ORDER BY {embedding_column} <=> %s::vector
        LIMIT %s
    """
    
    return execute_query(query, (query_embedding, query_embedding, limit))

# ============================================
# CIVILMICROTOOLS STUB HELPERS
# ============================================

def list_pipe_networks() -> List[Dict]:
    return []

def list_pipes() -> List[Dict]:
    return []

def list_structures() -> List[Dict]:
    return []

def list_alignments() -> List[Dict]:
    return []

def list_bmps() -> List[Dict]:
    return []

def list_utilities() -> List[Dict]:
    return []

def list_conflicts() -> List[Dict]:
    return []

if __name__ == "__main__":
    # Test connection
    print("Testing database connection...")
    try:
        with get_db_connection() as conn:
            print("✅ Database connection successful!")
            
            # Test query
            result = execute_single("SELECT COUNT(*) as count FROM block_definitions")
            print(f"✅ Found {result['count']} block definitions")
            
            result = execute_single("SELECT COUNT(*) as count FROM layer_standards")
            print(f"✅ Found {result['count']} layer standards")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
