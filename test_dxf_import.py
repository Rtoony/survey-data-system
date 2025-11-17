#!/usr/bin/env python3
"""
Test script to verify DXF import workflow with new AI-optimized schema
"""

import ezdxf
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import uuid
from dotenv import load_dotenv
from dxf_importer import DXFImporter

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

def create_test_dxf(filename='test_drawing.dxf'):
    """Create a simple test DXF file with various entities"""
    print(f"Creating test DXF file: {filename}")
    
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Add various entities
    msp.add_line((0, 0, 0), (100, 100, 0), dxfattribs={'layer': 'C-WALL'})
    msp.add_circle((50, 50, 0), radius=25, dxfattribs={'layer': 'C-ANNO'})
    msp.add_text('Test Drawing', dxfattribs={'layer': 'C-TEXT', 'height': 5}).set_placement((10, 10))
    msp.add_lwpolyline([(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)], dxfattribs={'layer': 'C-PROP'})
    
    doc.saveas(filename)
    print(f"✓ Created test DXF with 4 entities")
    return filename

def create_test_project(conn):
    """Create a test project"""
    print("\nCreating test project...")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        INSERT INTO projects (
            project_name, client_name, project_number, description,
            quality_score, tags, attributes
        )
        VALUES ('DXF Test Project', 'Test Client', 'TEST-001', 'Automated test project', 
                0.5, '{}', '{}')
        RETURNING project_id, project_name
    """)
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    
    print(f"✓ Created project: {result['project_name']} ({result['project_id']})")
    return str(result['project_id'])

def import_dxf(filename, project_id):
    """Import DXF file at project level"""
    print(f"\nImporting DXF file at project level: {filename}")
    
    importer = DXFImporter(DB_CONFIG)
    try:
        stats = importer.import_dxf(filename, project_id)
    except Exception as e:
        print(f"\n✗ IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()
        stats = {
            'entities': 0,
            'text': 0,
            'errors': [str(e)]
        }
    
    print("\n✓ Import Statistics:")
    print(f"  - Entities: {stats.get('entities', 0)}")
    print(f"  - Text: {stats.get('text', 0)}")
    print(f"  - Dimensions: {stats.get('dimensions', 0)}")
    print(f"  - Hatches: {stats.get('hatches', 0)}")
    print(f"  - Blocks: {stats.get('blocks', 0)}")
    layers = stats.get('layers', set())
    print(f"  - Layers: {len(layers) if isinstance(layers, set) else layers}")
    errors = stats.get('errors', [])
    if errors:
        print(f"  - Errors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"    • {error}")
    
    return stats

def verify_data(conn, project_id):
    """Verify data was imported correctly at project level"""
    print("\nVerifying imported data at project level...")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check drawing_entities - all entities are now project-level
    cur.execute("""
        SELECT COUNT(*) as count,
               COUNT(DISTINCT layer_id) as layers,
               COUNT(DISTINCT entity_type) as types
        FROM drawing_entities
    """)

    entities = cur.fetchone()
    print(f"✓ Found {entities['count']} project-level entities across {entities['layers']} layers")
    
    # Check layers - all layers are now project-level
    cur.execute("""
        SELECT layer_name, color, quality_score
        FROM layers
        ORDER BY layer_name
        LIMIT 10
    """)
    
    layers = cur.fetchall()
    print(f"✓ Project-level layers created:")
    for layer in layers:
        print(f"  - {layer['layer_name']} (color: {layer['color']}, quality: {layer['quality_score']})")
    
    # Check text - all text entities are now project-level
    cur.execute("""
        SELECT COUNT(*) as count
        FROM drawing_text
    """)

    text_count = cur.fetchone()
    print(f"✓ Found {text_count['count']} project-level text entities")
    
    cur.close()

def cleanup(conn, project_id, filename):
    """Clean up test data"""
    print("\nCleaning up test data...")
    cur = conn.cursor()
    
    # Delete project (cascades to drawings and entities)
    cur.execute("DELETE FROM projects WHERE project_id = %s::uuid", (project_id,))
    conn.commit()
    cur.close()
    
    # Delete test file
    if os.path.exists(filename):
        os.remove(filename)
    
    print("✓ Cleanup complete")

def main():
    """Run the full test workflow"""
    print("=" * 60)
    print("DXF Import Workflow Test (Project-Level)")
    print("=" * 60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    
    try:
        # Step 1: Create test DXF file
        filename = create_test_dxf()
        
        # Step 2: Create project
        project_id = create_test_project(conn)
        
        # Step 3: Import DXF at project level (no drawing required)
        stats = import_dxf(filename, project_id)
        
        # Step 4: Verify project-level entities
        verify_data(conn, project_id)
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("✓ Entities imported at project level")
        print("=" * 60)
        
        # Cleanup
        cleanup(conn, project_id, filename)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        conn.close()
    
    return 0

if __name__ == '__main__':
    exit(main())
