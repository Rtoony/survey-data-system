"""
Intelligent Object Creator
Creates database objects from DXF entities based on layer classification.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional, Tuple
import hashlib
import json
from layer_classifier import LayerClassifier, LayerClassification


class IntelligentObjectCreator:
    """
    Creates intelligent database objects from DXF entities.
    Maps DXF geometry + layer patterns to civil engineering objects.
    """
    
    def __init__(self, db_config: Dict, conn=None):
        """Initialize with database configuration."""
        self.db_config = db_config
        self.conn = conn
        self.classifier = LayerClassifier()
        self.should_close_conn = conn is None
    
    def create_from_entity(self, entity_data: Dict, drawing_id: str, project_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Create intelligent object from DXF entity data.
        
        Args:
            entity_data: Dict with entity info (type, layer, geometry, handle, etc.)
            drawing_id: UUID of drawing
            project_id: UUID of project
            
        Returns:
            Tuple of (object_type, object_id, table_name) or None
        """
        layer_name = entity_data.get('layer_name', '')
        classification = self.classifier.classify(layer_name)
        
        if not classification or classification.confidence < 0.7:
            return None
        
        if self.conn is None:
            self.conn = psycopg2.connect(**self.db_config)
        
        try:
            result = None
            
            if classification.object_type == 'utility_line':
                result = self._create_utility_line(entity_data, classification, project_id)
            
            elif classification.object_type == 'utility_structure':
                result = self._create_utility_structure(entity_data, classification, project_id)
            
            elif classification.object_type == 'bmp':
                result = self._create_bmp(entity_data, classification, project_id)
            
            elif classification.object_type == 'surface_model':
                result = self._create_surface_model(entity_data, classification, project_id)
            
            elif classification.object_type == 'alignment':
                result = self._create_alignment(entity_data, classification, project_id)
            
            elif classification.object_type == 'survey_point':
                result = self._create_survey_point(entity_data, classification, project_id)
            
            elif classification.object_type == 'site_tree':
                result = self._create_site_tree(entity_data, classification, project_id)
            
            if result:
                object_type, object_id, table_name = result
                self._create_entity_link(
                    drawing_id, entity_data.get('dxf_handle'), entity_data.get('entity_type'),
                    layer_name, entity_data.get('geometry_wkt'),
                    object_type, object_id, table_name
                )
            
            return result
            
        except Exception as e:
            print(f"Error creating intelligent object: {e}")
            return None
    
    def _create_utility_line(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create utility_lines record."""
        if entity_data.get('geometry_type') not in ['LINESTRING', 'LINESTRING Z']:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        utility_type = props.get('utility_type', 'Unknown')
        diameter = props.get('diameter_inches')
        
        cur.execute("""
            INSERT INTO utility_lines (
                project_id, utility_type, pipe_material, diameter_mm,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING line_id
        """, (
            project_id,
            utility_type,
            'Unknown',
            int(diameter * 25.4) if diameter else None,
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('utility_line', str(result[0]), 'utility_lines')
        return None
    
    def _create_utility_structure(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create utility_structures record."""
        if entity_data.get('geometry_type') not in ['POINT', 'POINT Z']:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        structure_type = props.get('structure_type', 'Unknown')
        utility_type = props.get('utility_type', 'Unknown')
        
        cur.execute("""
            INSERT INTO utility_structures (
                project_id, structure_type, utility_type,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING structure_id
        """, (
            project_id,
            structure_type,
            utility_type,
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('utility_structure', str(result[0]), 'utility_structures')
        return None
    
    def _create_bmp(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create bmps record."""
        cur = self.conn.cursor()
        props = classification.properties
        
        bmp_type = props.get('bmp_type', 'Unknown')
        design_volume = props.get('design_volume_cf')
        
        geometry_wkt = entity_data.get('geometry_wkt')
        area_sqft = None
        
        if entity_data.get('geometry_type') in ['POLYGON', 'POLYGON Z']:
            cur.execute("SELECT ST_Area(ST_GeomFromText(%s, 0))", (geometry_wkt,))
            area_result = cur.fetchone()
            if area_result:
                area_sqft = area_result[0]
        
        cur.execute("""
            INSERT INTO bmps (
                project_id, bmp_type, area_sqft, design_volume_cf,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING bmp_id
        """, (
            project_id,
            bmp_type,
            area_sqft,
            design_volume,
            geometry_wkt,
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('bmp', str(result[0]), 'bmps')
        return None
    
    def _create_surface_model(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create surface_models record or add to existing surface."""
        cur = self.conn.cursor()
        props = classification.properties
        
        surface_type = props.get('surface_type', 'Unknown')
        surface_name = f"{surface_type} - {entity_data.get('layer_name')}"
        
        cur.execute("""
            SELECT surface_id FROM surface_models
            WHERE project_id = %s AND surface_name = %s
        """, (project_id, surface_name))
        
        result = cur.fetchone()
        
        if not result:
            cur.execute("""
                INSERT INTO surface_models (
                    project_id, surface_name, surface_type, attributes
                )
                VALUES (%s, %s, %s, %s)
                RETURNING surface_id
            """, (
                project_id,
                surface_name,
                surface_type,
                json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
            ))
            result = cur.fetchone()
        
        cur.close()
        
        if result:
            return ('surface_model', str(result[0]), 'surface_models')
        return None
    
    def _create_alignment(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create horizontal_alignments record."""
        if entity_data.get('geometry_type') not in ['LINESTRING', 'LINESTRING Z']:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        alignment_name = props.get('description', entity_data.get('layer_name'))
        
        cur.execute("""
            INSERT INTO horizontal_alignments (
                project_id, alignment_name, alignment_type,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING alignment_id
        """, (
            project_id,
            alignment_name,
            'Centerline',
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('alignment', str(result[0]), 'horizontal_alignments')
        return None
    
    def _create_survey_point(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create survey_points record."""
        if entity_data.get('geometry_type') not in ['POINT', 'POINT Z']:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        point_type = props.get('point_type', 'Topo')
        
        cur.execute("""
            INSERT INTO survey_points (
                project_id, point_number, point_type,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING point_id
        """, (
            project_id,
            f"PT-{entity_data.get('dxf_handle', 'AUTO')}",
            point_type,
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('survey_point', str(result[0]), 'survey_points')
        return None
    
    def _create_site_tree(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create site_trees record."""
        if entity_data.get('geometry_type') not in ['POINT', 'POINT Z']:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        tree_status = props.get('tree_status', 'Existing')
        
        cur.execute("""
            INSERT INTO site_trees (
                project_id, tree_status,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s)
            RETURNING tree_id
        """, (
            project_id,
            tree_status,
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('site_tree', str(result[0]), 'site_trees')
        return None
    
    def _create_entity_link(self, drawing_id: str, dxf_handle: str, entity_type: str,
                           layer_name: str, geometry_wkt: str,
                           object_type: str, object_id: str, table_name: str):
        """Create link between DXF entity and intelligent object."""
        cur = self.conn.cursor()
        
        geometry_hash = hashlib.sha256(geometry_wkt.encode()).hexdigest() if geometry_wkt else None
        
        cur.execute("""
            INSERT INTO dxf_entity_links (
                drawing_id, dxf_handle, entity_type, layer_name, geometry_hash,
                object_type, object_id, object_table_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (drawing_id, dxf_handle) DO UPDATE SET
                object_type = EXCLUDED.object_type,
                object_id = EXCLUDED.object_id,
                object_table_name = EXCLUDED.object_table_name,
                geometry_hash = EXCLUDED.geometry_hash,
                updated_at = CURRENT_TIMESTAMP
        """, (
            drawing_id, dxf_handle, entity_type, layer_name, geometry_hash,
            object_type, object_id, table_name
        ))
        
        cur.close()
    
    def __del__(self):
        """Clean up connection if we created it."""
        if self.should_close_conn and self.conn:
            self.conn.close()
