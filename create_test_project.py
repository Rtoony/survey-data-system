#!/usr/bin/env python3
"""
Create a test project with DXF drawings and entities at valid Sonoma County coordinates.
This script creates spatial data that will display properly on the Map Viewer.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

def create_test_project():
    """Create a test project with spatial data in Sonoma County"""
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Debug: Check database connection
    cur.execute("SELECT current_database(), current_schema();")
    db_info = cur.fetchone()
    print(f"Connected to database: {db_info['current_database']}, schema: {db_info['current_schema']}")
    
    # Check if bbox columns exist
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'drawings' AND column_name LIKE 'bbox%'
    """)
    bbox_cols = cur.fetchall()
    print(f"BBox columns found: {[col['column_name'] for col in bbox_cols]}")
    
    try:
        print("\nCreating test project with Sonoma County spatial data...")
        
        # 1. Create a test project
        project_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO projects (
                project_id, project_name, project_number, client_name, description
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING project_id, project_name
        """, (
            project_id,
            'Sonoma County Test Site',
            'DEMO-001',
            'Test Client',
            'Test project with valid Sonoma County State Plane coordinates (SRID 2226)'
        ))
        project = cur.fetchone()
        print(f"✓ Created project: {project['project_name']} ({project_id})")
        
        # 2. Create entities with Sonoma County State Plane coordinates (SRID 2226)
        # These coordinates are for downtown Santa Rosa area
        # Approximate center: 38.4404° N, 122.7144° W
        # In SRID 2226: X ≈ 6,049,000 ft, Y ≈ 2,001,000 ft
        
        center_x = 6049000  # Feet
        center_y = 2001000  # Feet
        
        # Calculate bounding box for the drawing (based on entity extents)
        bbox_min_x = center_x - 250
        bbox_min_y = center_y - 50  
        bbox_max_x = center_x + 400
        bbox_max_y = center_y + 300
        
        # Create a test drawing with bounding box
        drawing_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO drawings (
                drawing_id, project_id, drawing_name, drawing_number,
                bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING drawing_id, drawing_name
        """, (
            drawing_id,
            project_id,
            'Site Plan - Santa Rosa',
            'SP-001',
            bbox_min_x,
            bbox_min_y,
            bbox_max_x,
            bbox_max_y
        ))
        drawing = cur.fetchone()
        print(f"✓ Created drawing: {drawing['drawing_name']} ({drawing_id})")
        
        # Create a simple layer first
        cur.execute("""
            INSERT INTO layers (layer_name, color, description)
            VALUES (%s, %s, %s)
            RETURNING layer_id
        """, (
            '0',  # Default layer
            7,    # White color (ACI)
            'Default layer'
        ))
        layer_id = cur.fetchone()['layer_id']
        
        entities = [
            # Create a rectangular building outline (100ft x 150ft)
            {
                'name': 'Building A',
                'type': 'LWPOLYLINE',
                'color': 1,  # Red
                'coords': [
                    (center_x, center_y),
                    (center_x + 100, center_y),
                    (center_x + 100, center_y + 150),
                    (center_x, center_y + 150),
                    (center_x, center_y)  # Close the polygon
                ]
            },
            # Create another building (80ft x 120ft)
            {
                'name': 'Building B',
                'type': 'LWPOLYLINE',
                'color': 2,  # Yellow
                'coords': [
                    (center_x + 150, center_y),
                    (center_x + 230, center_y),
                    (center_x + 230, center_y + 120),
                    (center_x + 150, center_y + 120),
                    (center_x + 150, center_y)
                ]
            },
            # Create a road centerline
            {
                'name': 'Main Street Centerline',
                'type': 'LINE',
                'color': 3,  # Green
                'coords': [
                    (center_x - 200, center_y + 75),
                    (center_x + 400, center_y + 75)
                ]
            },
            # Create a parking lot circle
            {
                'name': 'Parking Lot Roundabout',
                'type': 'CIRCLE',
                'color': 4,  # Cyan
                'coords': [(center_x + 300, center_y + 200)],  # Center point
                'radius': 50
            }
        ]
        
        entity_count = 0
        for ent in entities:
            entity_id = str(uuid.uuid4())
            
            # Build WKT geometry based on type (with Z=0 for 3D geometries)
            if ent['type'] == 'LWPOLYLINE':
                coords_str = ', '.join([f'{x} {y} 0' for x, y in ent['coords']])
                wkt = f'LINESTRING Z ({coords_str})'
            elif ent['type'] == 'LINE':
                coords_str = ', '.join([f'{x} {y} 0' for x, y in ent['coords']])
                wkt = f'LINESTRING Z ({coords_str})'
            elif ent['type'] == 'CIRCLE':
                # Approximate circle as a polygon with 32 points
                import math
                center_x_c, center_y_c = ent['coords'][0]
                radius = ent['radius']
                points = []
                for i in range(33):  # 32 segments + close
                    angle = (i / 32.0) * 2 * math.pi
                    x = center_x_c + radius * math.cos(angle)
                    y = center_y_c + radius * math.sin(angle)
                    points.append(f'{x} {y} 0')
                coords_str = ', '.join(points)
                wkt = f'LINESTRING Z ({coords_str})'
            
            cur.execute("""
                INSERT INTO drawing_entities (
                    entity_id, drawing_id, layer_id, entity_type,
                    geometry, color_aci
                )
                VALUES (
                    %s, %s, %s, %s,
                    ST_GeomFromText(%s, 0), %s
                )
            """, (
                entity_id,
                drawing_id,
                layer_id,
                ent['type'],
                wkt,
                ent['color']
            ))
            entity_count += 1
            print(f"  ✓ Created {ent['type']}: {ent['name']}")
        
        # Commit all changes
        conn.commit()
        
        print(f"\n✅ SUCCESS! Created test project with {entity_count} entities")
        print(f"\nProject Details:")
        print(f"  - Project ID: {project_id}")
        print(f"  - Drawing ID: {drawing_id}")
        print(f"  - Location: Santa Rosa, Sonoma County")
        print(f"  - Coordinates: EPSG:2226 (CA State Plane Zone 2)")
        print(f"  - Center: ({center_x}, {center_y}) feet")
        print(f"\nNext steps:")
        print(f"  1. Refresh the Drawing Manager to see the new entities")
        print(f"  2. Go to Map Viewer and look for 'Sonoma County Test Site' project")
        print(f"  3. The entities should be visible near downtown Santa Rosa")
        
        return project_id, drawing_id
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    create_test_project()
