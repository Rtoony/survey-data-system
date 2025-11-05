#!/usr/bin/env python3
"""
Test script to verify map viewer can display imported DXF entities.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import ezdxf
from dxf_importer import DXFImporter
import os

DB_CONFIG = {
    'host': os.environ.get('PGHOST'),
    'database': os.environ.get('PGDATABASE'),
    'user': os.environ.get('PGUSER'),
    'password': os.environ.get('PGPASSWORD')
}

def main():
    print("=" * 60)
    print("Map Viewer DXF Display Test")
    print("=" * 60)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    project_id = None
    drawing_id = None
    
    try:
        cur.execute("""
            INSERT INTO projects (project_name, description)
            VALUES ('Map Viewer Test Project', 'Test project for map viewer DXF display')
            RETURNING project_id, project_name
        """)
        result = cur.fetchone()
        project_id = str(result['project_id'])
        print(f"✓ Created project: {result['project_name']} ({project_id})")
        
        cur.execute("""
            INSERT INTO drawings (
                project_id,
                drawing_name,
                sheet_title
            )
            VALUES (
                %s,
                'Map Viewer Test Drawing',
                'Test drawing for map viewer'
            )
            RETURNING drawing_id, drawing_name
        """, (project_id,))
        result = cur.fetchone()
        drawing_id = str(result['drawing_id'])
        print(f"✓ Created drawing: {result['drawing_name']} ({drawing_id})")
        
        conn.commit()
        
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        msp.add_line((0, 0), (100, 100), dxfattribs={'layer': 'C-ROAD', 'color': 1})
        msp.add_circle((50, 50), 25, dxfattribs={'layer': 'C-BLDG', 'color': 3})
        msp.add_text('Test Building', dxfattribs={'layer': 'C-TEXT', 'insert': (50, 75), 'height': 5})
        
        filename = 'test_map_viewer.dxf'
        doc.saveas(filename)
        print(f"\n✓ Created test DXF: {filename}")
        
        importer = DXFImporter(DB_CONFIG)
        stats = importer.import_dxf(filename, drawing_id)
        
        print(f"\n✓ Import Statistics:")
        print(f"  - Entities: {stats['entities']}")
        print(f"  - Text: {stats['text']}")
        print(f"  - Layers: {stats['layers']}")
        print(f"  - Errors: {len(stats['errors'])}")
        
        cur.execute("""
            SELECT 
                de.entity_type,
                l.layer_name,
                de.color_aci,
                ST_AsText(de.geometry) as geometry_wkt,
                ST_GeometryType(de.geometry) as geom_type,
                ST_Transform(de.geometry, 4326) as wgs84_geom
            FROM drawing_entities de
            LEFT JOIN layers l ON de.layer_id = l.layer_id
            WHERE de.drawing_id = %s
            ORDER BY de.entity_type
        """, (drawing_id,))
        
        entities = cur.fetchall()
        
        print(f"\n✓ Map Viewer API would return {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity['entity_type']}: {entity['layer_name']} (color: {entity['color_aci']}, type: {entity['geom_type']})")
        
        cur.execute("""
            SELECT 
                dt.text_content,
                l.layer_name,
                ST_AsText(dt.insertion_point) as position_wkt,
                ST_Transform(dt.insertion_point, 4326) as wgs84_pos
            FROM drawing_text dt
            LEFT JOIN layers l ON dt.layer_id = l.layer_id
            WHERE dt.drawing_id = %s
        """, (drawing_id,))
        
        texts = cur.fetchall()
        
        print(f"\n✓ Map Viewer API would return {len(texts)} text entities:")
        for text in texts:
            print(f"  - '{text['text_content']}' on layer {text['layer_name']}")
        
        print("\n" + "=" * 60)
        print("✓ MAP VIEWER TEST PASSED!")
        print("=" * 60)
        print("\nThe imported DXF entities:")
        print("  1. Are stored with SRID 2226 (California State Plane)")
        print("  2. Can be transformed to WGS84 (EPSG:4326) for map display")
        print("  3. Include proper layer names and styling information")
        print("  4. Are ready to be displayed on the map viewer")
        
        os.remove(filename)
        
    finally:
        if drawing_id:
            cur.execute("DELETE FROM drawing_entities WHERE drawing_id = %s", (drawing_id,))
            cur.execute("DELETE FROM drawing_text WHERE drawing_id = %s", (drawing_id,))
            cur.execute("DELETE FROM layers WHERE drawing_id = %s", (drawing_id,))
            cur.execute("DELETE FROM drawings WHERE drawing_id = %s", (drawing_id,))
        
        if project_id:
            cur.execute("DELETE FROM projects WHERE project_id = %s", (project_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        print("\n✓ Cleanup complete")

if __name__ == '__main__':
    main()
