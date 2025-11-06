#!/usr/bin/env python3
"""
Retroactive Structure Creation
Processes block_inserts that weren't converted to utility_structures and creates them.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from layer_classifier import LayerClassifier
import json

def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=os.environ.get('PGHOST', 'localhost'),
        port=os.environ.get('PGPORT', '5432'),
        database=os.environ.get('PGDATABASE', 'postgres'),
        user=os.environ.get('PGUSER', 'postgres'),
        password=os.environ.get('PGPASSWORD', '')
    )

def get_project_id(conn):
    """Get the first project ID from the database."""
    cur = conn.cursor()
    cur.execute("SELECT project_id FROM projects LIMIT 1")
    result = cur.fetchone()
    cur.close()
    if result:
        return str(result[0])
    return None

def get_or_create_storm_network(conn, project_id):
    """Get or create the Storm Gravity Network."""
    cur = conn.cursor()
    
    cur.execute("""
        SELECT network_id FROM pipe_networks 
        WHERE project_id = %s AND utility_system = 'Storm' AND network_mode = 'gravity'
        LIMIT 1
    """, (project_id,))
    
    result = cur.fetchone()
    if result:
        network_id = str(result[0])
        cur.close()
        return network_id
    
    cur.execute("""
        INSERT INTO pipe_networks (project_id, network_name, utility_system, network_mode)
        VALUES (%s, 'Storm Gravity Network', 'Storm', 'gravity')
        RETURNING network_id
    """, (project_id,))
    
    result = cur.fetchone()
    network_id = str(result[0]) if result else None
    conn.commit()
    cur.close()
    return network_id

def create_structure_from_block(conn, block_insert, layer_name, project_id, classifier):
    """Create a utility_structure from a block insert."""
    classification = classifier.classify(layer_name)
    
    if not classification or classification.object_type != 'utility_structure':
        return None
    
    props = classification.properties
    structure_type = props.get('structure_type', 'Unknown')
    utility_type = props.get('utility_type', 'Storm')
    network_mode = classification.network_mode or 'gravity'
    
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO utility_structures (
                project_id, structure_type, utility_system, utility_mode,
                rim_geometry, attributes
            )
            VALUES (%s, %s, %s, %s::utility_mode_enum, %s, %s)
            RETURNING structure_id
        """, (
            project_id,
            structure_type,
            utility_type,
            network_mode,
            block_insert['insertion_point_wkt'],
            json.dumps({
                'source': 'block_insert_retroactive',
                'layer_name': layer_name,
                'block_name': block_insert['block_name'],
                'insert_id': str(block_insert['insert_id'])
            })
        ))
        
        result = cur.fetchone()
        structure_id = str(result[0]) if result else None
        conn.commit()
        cur.close()
        
        return {
            'structure_id': structure_id,
            'structure_type': structure_type,
            'utility_type': utility_type,
            'network_mode': network_mode,
            'layer_name': layer_name
        }
        
    except Exception as e:
        print(f"Error creating structure: {e}")
        conn.rollback()
        cur.close()
        return None

def assign_structure_to_network(conn, network_id, structure_id):
    """Assign a structure to a pipe network."""
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO utility_network_memberships (network_id, structure_id, member_role)
            VALUES (%s, %s, 'structure')
            ON CONFLICT DO NOTHING
        """, (network_id, structure_id))
        
        conn.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error assigning structure to network: {e}")
        conn.rollback()
        cur.close()
        return False

def main():
    """Main execution function."""
    print("=" * 60)
    print("RETROACTIVE STRUCTURE CREATION FROM BLOCK INSERTS")
    print("=" * 60)
    
    conn = get_db_connection()
    classifier = LayerClassifier()
    
    project_id = get_project_id(conn)
    if not project_id:
        print("ERROR: No project found in database")
        conn.close()
        return
    
    print(f"\nProject ID: {project_id}")
    
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            bi.insert_id,
            bi.block_name,
            l.layer_name,
            ST_AsText(bi.insertion_point) as insertion_point_wkt,
            bi.rotation,
            bi.scale_x,
            bi.scale_y,
            bi.scale_z
        FROM block_inserts bi
        LEFT JOIN layers l ON bi.layer_id = l.layer_id
        WHERE bi.drawing_id IN (SELECT drawing_id FROM drawings WHERE project_id = %s)
        ORDER BY l.layer_name, bi.block_name
    """, (project_id,))
    
    block_inserts = cur.fetchall()
    cur.close()
    
    print(f"\nFound {len(block_inserts)} block inserts to process")
    
    created_structures = []
    skipped_blocks = []
    
    for block in block_inserts:
        layer_name = block['layer_name'] or ''
        block_name = block['block_name'] or 'Unknown'
        
        if not layer_name:
            skipped_blocks.append(f"{block_name} (no layer)")
            continue
        
        result = create_structure_from_block(conn, block, layer_name, project_id, classifier)
        
        if result:
            created_structures.append(result)
            print(f"✓ Created {result['structure_type']} from layer '{result['layer_name']}' (block: {block_name})")
        else:
            skipped_blocks.append(f"{block_name} on layer '{layer_name}'")
    
    print(f"\n{'='*60}")
    print(f"STRUCTURES CREATED: {len(created_structures)}")
    print(f"BLOCKS SKIPPED: {len(skipped_blocks)}")
    print(f"{'='*60}")
    
    if created_structures:
        print("\nCreated structures by type:")
        type_counts = {}
        for s in created_structures:
            stype = s['structure_type']
            type_counts[stype] = type_counts.get(stype, 0) + 1
        
        for stype, count in sorted(type_counts.items()):
            print(f"  - {stype}: {count}")
    
    if skipped_blocks:
        print("\nSkipped blocks (first 10):")
        for block in skipped_blocks[:10]:
            print(f"  - {block}")
    
    storm_structures = [s for s in created_structures if s['utility_type'] == 'Storm']
    
    if storm_structures:
        print(f"\n{'='*60}")
        print(f"ASSIGNING {len(storm_structures)} STORM STRUCTURES TO NETWORK")
        print(f"{'='*60}")
        
        network_id = get_or_create_storm_network(conn, project_id)
        print(f"\nStorm Gravity Network ID: {network_id}")
        
        assigned_count = 0
        for structure in storm_structures:
            if assign_structure_to_network(conn, network_id, structure['structure_id']):
                assigned_count += 1
        
        print(f"\nAssigned {assigned_count}/{len(storm_structures)} structures to Storm Gravity Network")
    
    conn.close()
    
    print("\n" + "="*60)
    print("PROCESS COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
