#!/usr/bin/env python3
"""
Retroactively create intelligent objects from already-imported DXF entities.
This script processes drawing_entities that weren't converted due to the case-sensitivity bug.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from intelligent_object_creator import IntelligentObjectCreator

DB_CONFIG = {
    'host': os.getenv('PGHOST') or os.getenv('DB_HOST'),
    'port': os.getenv('PGPORT') or os.getenv('DB_PORT', '5432'),
    'database': os.getenv('PGDATABASE') or os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('PGUSER') or os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('PGPASSWORD') or os.getenv('DB_PASSWORD'),
    'sslmode': 'require'
}

def retroactive_process_drawing(drawing_id: str):
    """Process all entities from a drawing and create intelligent objects."""
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get project_id from drawing
        cur.execute("""
            SELECT project_id FROM drawings WHERE drawing_id = %s
        """, (drawing_id,))
        result = cur.fetchone()
        
        if not result:
            print(f"Drawing {drawing_id} not found")
            cur.close()
            conn.close()
            return
        
        project_id = str(result['project_id'])
        print(f"Processing drawing {drawing_id} for project {project_id}")
        
        # Query all entities from this drawing
        cur.execute("""
            SELECT 
                de.entity_id,
                de.entity_type,
                l.layer_name,
                ST_AsText(de.geometry) as geometry_wkt,
                ST_GeometryType(de.geometry) as geometry_type,
                de.dxf_handle,
                de.color_aci,
                de.linetype,
                de.space_type
            FROM drawing_entities de
            LEFT JOIN layers l ON de.layer_id = l.layer_id
            WHERE de.drawing_id = %s
            ORDER BY de.created_at DESC
        """, (drawing_id,))
        
        entities = cur.fetchall()
        cur.close()
        
        print(f"Found {len(entities)} entities to process")
        
        # Initialize intelligent object creator with shared connection
        creator = IntelligentObjectCreator(DB_CONFIG, conn=conn)
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for entity in entities:
            try:
                # Prepare entity data dictionary
                entity_data = {
                    'entity_id': str(entity['entity_id']),
                    'entity_type': entity['entity_type'],
                    'layer_name': entity['layer_name'],
                    'geometry_wkt': entity['geometry_wkt'],
                    'geometry_type': entity['geometry_type'].replace('ST_', ''),
                    'dxf_handle': entity['dxf_handle'],
                    'color_aci': entity['color_aci'],
                    'linetype': entity['linetype'],
                    'space_type': entity['space_type']
                }
                
                # Attempt to create intelligent object
                result = creator.create_from_entity(entity_data, drawing_id, project_id)
                
                if result:
                    object_type, object_id, table_name = result
                    print(f"✓ Created {object_type} from {entity['entity_type']} on layer {entity['layer_name']}")
                    created_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"✗ Error processing entity {entity['entity_id']}: {e}")
                error_count += 1
        
        # Commit all changes
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"Processing complete!")
        print(f"  Created: {created_count} intelligent objects")
        print(f"  Skipped: {skipped_count} entities (no matching pattern)")
        print(f"  Errors:  {error_count}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == '__main__':
    # Process the recently imported drawing
    drawing_id = '70457d44-c754-491b-95b0-bee2ee5cc2e7'
    print(f"Starting retroactive processing for drawing: {drawing_id}\n")
    retroactive_process_drawing(drawing_id)
