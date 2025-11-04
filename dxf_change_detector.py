"""
DXF Change Detector Module
Detects changes between DXF files and database for intelligent re-import.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple
import hashlib
from layer_classifier import LayerClassifier
from intelligent_object_creator import IntelligentObjectCreator


class DXFChangeDetector:
    """Detect and process changes between CAD and database."""
    
    def __init__(self, db_config: Dict):
        """Initialize change detector with database configuration."""
        self.db_config = db_config
        self.classifier = LayerClassifier()
    
    def detect_changes(self, drawing_id: str, reimported_entities: List[Dict]) -> Dict:
        """
        Detect changes between reimported DXF entities and database.
        
        Args:
            drawing_id: UUID of the drawing being reimported
            reimported_entities: List of entity dicts from DXF reimport
            
        Returns:
            Dictionary with change detection statistics and operations
        """
        stats = {
            'entities_checked': 0,
            'entities_unchanged': 0,
            'geometry_changes': 0,
            'layer_changes': 0,
            'new_entities': 0,
            'new_objects_created': 0,
            'deleted_entities': 0,
            'conflicts': 0,
            'errors': []
        }
        
        conn = psycopg2.connect(**self.db_config)
        
        try:
            # Get all existing entity links for this drawing
            existing_links = self._get_existing_links(drawing_id, conn)
            
            # Get project_id for creating new objects
            project_id = self._get_project_id(drawing_id, conn)
            
            # Initialize intelligent object creator for new entities
            creator = IntelligentObjectCreator(self.db_config, conn=conn)
            
            # Track which handles we've seen in the reimport
            reimport_handles = set()
            
            # Check each reimported entity
            for entity in reimported_entities:
                stats['entities_checked'] += 1
                dxf_handle = entity.get('dxf_handle')
                
                if not dxf_handle:
                    continue
                
                reimport_handles.add(dxf_handle)
                
                if dxf_handle in existing_links:
                    # Entity exists - check for changes
                    link = existing_links[dxf_handle]
                    changes = self._detect_entity_changes(entity, link, conn)
                    
                    if changes['geometry_changed']:
                        stats['geometry_changes'] += 1
                        self._update_geometry(entity, link, conn, stats)
                    
                    if changes['layer_changed']:
                        stats['layer_changes'] += 1
                        self._update_properties_from_layer(entity, link, conn, stats)
                    
                    if not changes['geometry_changed'] and not changes['layer_changed']:
                        stats['entities_unchanged'] += 1
                else:
                    # New entity - create intelligent object
                    stats['new_entities'] += 1
                    if project_id:
                        result = creator.create_from_entity(entity, drawing_id, project_id)
                        if result:
                            stats['new_objects_created'] += 1
            
            # Find deleted entities (in database but not in reimport)
            deleted_handles = set(existing_links.keys()) - reimport_handles
            for handle in deleted_handles:
                stats['deleted_entities'] += 1
                self._mark_as_deleted(existing_links[handle], conn, stats)
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            stats['errors'].append(f"Change detection failed: {str(e)}")
        finally:
            conn.close()
        
        return stats
    
    def _get_project_id(self, drawing_id: str, conn) -> Optional[str]:
        """Get the project_id for a drawing."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT project_id FROM drawings WHERE drawing_id = %s
        """, (drawing_id,))
        
        result = cur.fetchone()
        cur.close()
        
        return str(result['project_id']) if result else None
    
    def _get_existing_links(self, drawing_id: str, conn) -> Dict[str, Dict]:
        """Get all existing entity links for a drawing, indexed by DXF handle."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                dxf_handle,
                entity_type,
                layer_name,
                geometry_hash,
                object_type,
                object_id,
                table_name,
                sync_status,
                last_modified_in_db
            FROM dxf_entity_links
            WHERE drawing_id = %s
        """, (drawing_id,))
        
        links = cur.fetchall()
        cur.close()
        
        # Index by handle for quick lookup
        return {link['dxf_handle']: dict(link) for link in links}
    
    def _detect_entity_changes(self, entity: Dict, link: Dict, conn) -> Dict:
        """
        Detect what changed about an entity.
        
        Returns:
            Dict with boolean flags: geometry_changed, layer_changed
        """
        # Calculate geometry hash from reimported entity
        geometry_wkt = entity.get('geometry_wkt', '')
        new_hash = hashlib.sha256(geometry_wkt.encode()).hexdigest() if geometry_wkt else None
        old_hash = link['geometry_hash']
        
        geometry_changed = (new_hash != old_hash)
        layer_changed = (entity.get('layer_name') != link['layer_name'])
        
        return {
            'geometry_changed': geometry_changed,
            'layer_changed': layer_changed
        }
    
    def _update_geometry(self, entity: Dict, link: Dict, conn, stats: Dict):
        """Update intelligent object geometry when CAD geometry changes."""
        try:
            cur = conn.cursor()
            
            table_name = link['table_name']
            object_id = link['object_id']
            geometry_wkt = entity.get('geometry_wkt')
            
            # Update geometry in the appropriate table
            if table_name == 'utility_lines':
                cur.execute("""
                    UPDATE utility_lines
                    SET line_geometry = ST_GeomFromText(%s, 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE utility_line_id = %s
                """, (geometry_wkt, object_id))
            
            elif table_name == 'utility_structures':
                cur.execute("""
                    UPDATE utility_structures
                    SET point_geometry = ST_GeomFromText(%s, 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE structure_id = %s
                """, (geometry_wkt, object_id))
            
            elif table_name == 'bmps':
                # Update location or boundary depending on geometry type
                geom_type = entity.get('geometry_type', '')
                if 'POINT' in geom_type:
                    cur.execute("""
                        UPDATE bmps
                        SET location = ST_GeomFromText(%s, 4326),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE bmp_id = %s
                    """, (geometry_wkt, object_id))
                else:
                    cur.execute("""
                        UPDATE bmps
                        SET boundary = ST_GeomFromText(%s, 4326),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE bmp_id = %s
                    """, (geometry_wkt, object_id))
            
            elif table_name == 'surface_models':
                cur.execute("""
                    UPDATE surface_models
                    SET surface_geometry = ST_GeomFromText(%s, 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE surface_id = %s
                """, (geometry_wkt, object_id))
            
            elif table_name == 'horizontal_alignments':
                cur.execute("""
                    UPDATE horizontal_alignments
                    SET centerline_geometry = ST_GeomFromText(%s, 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE alignment_id = %s
                """, (geometry_wkt, object_id))
            
            elif table_name == 'survey_points':
                cur.execute("""
                    UPDATE survey_points
                    SET point_geometry = ST_GeomFromText(%s, 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE point_id = %s
                """, (geometry_wkt, object_id))
            
            elif table_name == 'site_trees':
                cur.execute("""
                    UPDATE site_trees
                    SET location = ST_GeomFromText(%s, 4326),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tree_id = %s
                """, (geometry_wkt, object_id))
            
            # Update geometry hash in entity links
            new_hash = hashlib.sha256(geometry_wkt.encode()).hexdigest()
            cur.execute("""
                UPDATE dxf_entity_links
                SET geometry_hash = %s,
                    sync_status = 'synced',
                    last_sync_at = CURRENT_TIMESTAMP
                WHERE dxf_handle = %s AND object_id = %s
            """, (new_hash, entity['dxf_handle'], object_id))
            
            cur.close()
            
        except Exception as e:
            stats['errors'].append(f"Failed to update geometry for {link['object_type']}: {str(e)}")
    
    def _update_properties_from_layer(self, entity: Dict, link: Dict, conn, stats: Dict):
        """Update intelligent object properties when layer name changes."""
        try:
            cur = conn.cursor()
            
            # Classify the new layer name
            new_layer = entity.get('layer_name', '')
            classification = self.classifier.classify(new_layer)
            
            if not classification or classification.confidence < 0.7:
                # Can't reliably classify new layer - mark as conflict
                cur.execute("""
                    UPDATE dxf_entity_links
                    SET sync_status = 'conflict',
                        layer_name = %s,
                        last_sync_at = CURRENT_TIMESTAMP
                    WHERE dxf_handle = %s AND object_id = %s
                """, (new_layer, entity['dxf_handle'], link['object_id']))
                stats['conflicts'] += 1
                cur.close()
                return
            
            table_name = link['table_name']
            object_id = link['object_id']
            props = classification.properties
            
            # Update properties based on table
            if table_name == 'utility_lines':
                diameter_mm = props.get('diameter_inches', 0) * 25.4 if props.get('diameter_inches') else None
                cur.execute("""
                    UPDATE utility_lines
                    SET utility_type = COALESCE(%s, utility_type),
                        diameter_mm = COALESCE(%s, diameter_mm),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE utility_line_id = %s
                """, (props.get('utility_type'), diameter_mm, object_id))
            
            elif table_name == 'utility_structures':
                cur.execute("""
                    UPDATE utility_structures
                    SET structure_type = COALESCE(%s, structure_type),
                        utility_type = COALESCE(%s, utility_type),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE structure_id = %s
                """, (props.get('structure_type'), props.get('utility_type'), object_id))
            
            elif table_name == 'bmps':
                cur.execute("""
                    UPDATE bmps
                    SET bmp_type = COALESCE(%s, bmp_type),
                        design_volume_cf = COALESCE(%s, design_volume_cf),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE bmp_id = %s
                """, (props.get('bmp_type'), props.get('design_volume_cf'), object_id))
            
            elif table_name == 'surface_models':
                cur.execute("""
                    UPDATE surface_models
                    SET surface_type = COALESCE(%s, surface_type),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE surface_id = %s
                """, (props.get('surface_type'), object_id))
            
            elif table_name == 'survey_points':
                cur.execute("""
                    UPDATE survey_points
                    SET point_type = COALESCE(%s, point_type),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE point_id = %s
                """, (props.get('point_type'), object_id))
            
            elif table_name == 'site_trees':
                cur.execute("""
                    UPDATE site_trees
                    SET tree_status = COALESCE(%s, tree_status),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE tree_id = %s
                """, (props.get('tree_status'), object_id))
            
            # Update layer name in entity links
            cur.execute("""
                UPDATE dxf_entity_links
                SET layer_name = %s,
                    sync_status = 'synced',
                    last_sync_at = CURRENT_TIMESTAMP
                WHERE dxf_handle = %s AND object_id = %s
            """, (new_layer, entity['dxf_handle'], object_id))
            
            cur.close()
            
        except Exception as e:
            stats['errors'].append(f"Failed to update properties for {link['object_type']}: {str(e)}")
    
    def _mark_as_deleted(self, link: Dict, conn, stats: Dict):
        """Mark an intelligent object as deleted when its DXF entity is removed."""
        try:
            cur = conn.cursor()
            
            # Update entity link status
            cur.execute("""
                UPDATE dxf_entity_links
                SET sync_status = 'deleted',
                    last_sync_at = CURRENT_TIMESTAMP
                WHERE dxf_handle = %s AND object_id = %s
            """, (link['dxf_handle'], link['object_id']))
            
            # Optionally soft-delete the object or mark it inactive
            # For now, just update the sync status
            # In production, you might want to add a 'deleted_at' timestamp
            # or 'is_active' flag to the object tables
            
            cur.close()
            
        except Exception as e:
            stats['errors'].append(f"Failed to mark {link['object_type']} as deleted: {str(e)}")
