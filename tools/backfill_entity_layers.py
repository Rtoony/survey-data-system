"""
Backfill script to populate drawing_entities.layer_id for existing entities.

This script finds all entities that are missing layer assignments and populates
them using the same logic as IntelligentObjectCreator._ensure_drawing_entity().
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB_CONFIG
from dxf_lookup_service import DXFLookupService
from standards.layer_classifier_v2 import LayerClassifierV2 as LayerClassifier


def backfill_entity_layers():
    """
    Backfill drawing_entities.layer_id for all existing entities.
    
    Process:
    1. Find all entities missing layer_id in drawing_entities
    2. For each entity, determine its layer name:
       - For utility_lines, utility_structures, survey_points: use DXF layer name
       - For generic_objects: use GENERIC-UNCLASSIFIED
    3. Get/create the layer_id using DXFLookupService
    4. Update drawing_entities with the layer_id
    """
    db_config = DB_CONFIG
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    classifier = LayerClassifier()
    lookup_service = DXFLookupService(db_config, conn=conn)
    
    print("=" * 60)
    print("Backfilling drawing_entities.layer_id for existing entities")
    print("=" * 60)
    
    try:
        # Find all entities without layer_id
        # We need to join with dxf_entity_links to get the original layer name
        query = """
            WITH entities_missing_layer AS (
                -- Utility lines
                SELECT 
                    ul.entity_id,
                    ul.project_id,
                    'utility_lines' as source_table,
                    del.layer_name as dxf_layer_name,
                    ST_AsText(ul.geometry) as geometry_wkt
                FROM utility_lines ul
                LEFT JOIN drawing_entities de ON de.entity_id = ul.entity_id
                LEFT JOIN dxf_entity_links del ON del.object_id = ul.line_id 
                    AND del.object_table_name = 'utility_lines'
                WHERE de.layer_id IS NULL OR de.entity_id IS NULL
                
                UNION ALL
                
                -- Utility structures
                SELECT 
                    us.entity_id,
                    us.project_id,
                    'utility_structures' as source_table,
                    del.layer_name as dxf_layer_name,
                    ST_AsText(us.rim_geometry) as geometry_wkt
                FROM utility_structures us
                LEFT JOIN drawing_entities de ON de.entity_id = us.entity_id
                LEFT JOIN dxf_entity_links del ON del.object_id = us.structure_id 
                    AND del.object_table_name = 'utility_structures'
                WHERE de.layer_id IS NULL OR de.entity_id IS NULL
                
                UNION ALL
                
                -- Survey points
                SELECT 
                    sp.entity_id,
                    sp.project_id,
                    'survey_points' as source_table,
                    COALESCE(sp.layer_name, del.layer_name) as dxf_layer_name,
                    ST_AsText(sp.geometry) as geometry_wkt
                FROM survey_points sp
                LEFT JOIN drawing_entities de ON de.entity_id = sp.entity_id
                LEFT JOIN dxf_entity_links del ON del.object_id = sp.point_id 
                    AND del.object_table_name = 'survey_points'
                WHERE (de.layer_id IS NULL OR de.entity_id IS NULL) AND sp.is_active = true
                
                UNION ALL
                
                -- Generic objects
                SELECT 
                    go.object_id as entity_id,
                    go.project_id,
                    'generic_objects' as source_table,
                    go.original_layer_name as dxf_layer_name,
                    ST_AsText(go.geometry) as geometry_wkt
                FROM generic_objects go
                LEFT JOIN drawing_entities de ON de.entity_id = go.object_id
                WHERE (de.layer_id IS NULL OR de.entity_id IS NULL) AND go.is_active = true
            )
            SELECT * FROM entities_missing_layer
            WHERE entity_id IS NOT NULL AND project_id IS NOT NULL
            ORDER BY source_table, entity_id
        """
        
        cur.execute(query)
        entities = cur.fetchall()
        
        print(f"\nFound {len(entities)} entities missing layer assignments")
        
        if not entities:
            print("No entities need backfilling. All done!")
            return
        
        # Group by source table for reporting
        by_table = {}
        for entity in entities:
            table = entity['source_table']
            by_table[table] = by_table.get(table, 0) + 1
        
        print("\nBreakdown by table:")
        for table, count in by_table.items():
            print(f"  {table}: {count} entities")
        
        print("\nStarting backfill process...")
        print("-" * 60)
        
        updated_count = 0
        error_count = 0
        
        for i, entity in enumerate(entities, 1):
            entity_id = str(entity['entity_id'])
            project_id = str(entity['project_id'])
            source_table = entity['source_table']
            dxf_layer_name = entity['dxf_layer_name'] or 'UNKNOWN'
            geometry_wkt = entity.get('geometry_wkt')
            
            if not geometry_wkt:
                print(f"  SKIP entity {entity_id} ({source_table}): missing geometry")
                continue
            
            try:
                # Determine the layer name to use
                if source_table == 'generic_objects':
                    layer_name = "GENERIC-UNCLASSIFIED"
                else:
                    # Classify the DXF layer name to get standard layer name
                    classification = classifier.classify(dxf_layer_name)
                    if classification and hasattr(classification, 'standard_layer_name'):
                        layer_name = classification.standard_layer_name or dxf_layer_name
                    else:
                        layer_name = dxf_layer_name
                
                # Get or create the layer
                layer_id, layer_standard_id = lookup_service.get_or_create_layer(
                    layer_name=layer_name,
                    project_id=project_id,
                    drawing_id=None  # Project-level layers
                )
                
                # Upsert drawing_entities record with geometry
                cur.execute("""
                    INSERT INTO drawing_entities (
                        entity_id, project_id, layer_id, entity_type, geometry
                    )
                    VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 2226))
                    ON CONFLICT (entity_id) DO UPDATE SET
                        layer_id = EXCLUDED.layer_id,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    entity_id,
                    project_id,
                    layer_id,
                    'UNKNOWN',  # We don't have entity_type here
                    geometry_wkt
                ))
                
                updated_count += 1
                
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(entities)} entities... ({updated_count} updated)")
                
            except Exception as e:
                error_count += 1
                print(f"  ERROR processing entity {entity_id} ({source_table}): {e}")
        
        # Commit all changes
        conn.commit()
        
        print("-" * 60)
        print(f"\nBackfill complete!")
        print(f"  Total processed: {len(entities)}")
        print(f"  Successfully updated: {updated_count}")
        print(f"  Errors: {error_count}")
        
        if updated_count > 0:
            print(f"\n✓ {updated_count} entities now have layer assignments!")
            print("  The Entity Browser will now show database layer names.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    backfill_entity_layers()
