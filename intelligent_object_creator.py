"""
Intelligent Object Creator
Creates database objects from DXF entities based on layer classification.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional, Tuple
import hashlib
import json
import sys
import os

# Try to use new standards-based classifier, fall back to legacy
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from standards.layer_classifier_v2 import LayerClassifierV2 as LayerClassifier, LayerClassification
except ImportError:
    # Fall back to legacy classifier
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
    
    def create_from_entity(self, entity_data: Dict, project_id: str, drawing_id: Optional[str] = None) -> Optional[Tuple[str, str, str]]:
        """
        Create intelligent object from DXF entity data.
        
        Args:
            entity_data: Dict with entity info (type, layer, geometry, handle, etc.)
            project_id: UUID of project
            drawing_id: Optional UUID of drawing (None for project-level entities)
            
        Returns:
            Tuple of (object_type, object_id, table_name) or None
        """
        layer_name = entity_data.get('layer_name', '')
        classification = self.classifier.classify(layer_name)
        
        # Initialize connection if needed (required for ALL object creation paths)
        if self.conn is None:
            self.conn = psycopg2.connect(**self.db_config)
            self.should_close_conn = True
        
        # If no classification or low confidence, create a generic object for review
        if not classification or classification.confidence < 0.7:
            result = self._create_generic_object(entity_data, classification, project_id)
            # Create entity link for generic objects too
            if result:
                object_type, object_id, table_name = result
                dxf_handle = entity_data.get('dxf_handle', '')
                entity_type = entity_data.get('entity_type', 'UNKNOWN')
                geometry_wkt = entity_data.get('geometry_wkt', '')
                layer_name = entity_data.get('layer_name', '')
                
                if dxf_handle and geometry_wkt:
                    self._create_entity_link(
                        project_id, drawing_id, dxf_handle, entity_type,
                        layer_name, geometry_wkt,
                        object_type, object_id, table_name
                    )
            return result
        
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
            
            elif classification.object_type == 'parcel':
                result = self._create_parcel(entity_data, classification, project_id)
            
            elif classification.object_type == 'grading_feature':
                result = self._create_grading_feature(entity_data, classification, project_id)
            
            elif classification.object_type in ['surface_feature', 'ada_feature']:
                result = self._create_surface_feature(entity_data, classification, project_id)
            
            elif classification.object_type == 'contour':
                result = self._create_contour(entity_data, classification, project_id)
            
            elif classification.object_type == 'spot_elevation':
                result = self._create_spot_elevation(entity_data, classification, project_id)
            
            if result:
                object_type, object_id, table_name = result
                dxf_handle = entity_data.get('dxf_handle', '')
                entity_type = entity_data.get('entity_type', 'UNKNOWN')
                geometry_wkt = entity_data.get('geometry_wkt', '')
                
                # Create entity link for project-level imports (drawing_id can be None)
                if dxf_handle and geometry_wkt:
                    self._create_entity_link(
                        project_id, drawing_id, dxf_handle, entity_type,
                        layer_name, geometry_wkt,
                        object_type, object_id, table_name
                    )
            
            return result
            
        except Exception as e:
            print(f"Error creating intelligent object: {e}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def _create_utility_line(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create utility_lines record."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['LINESTRING', 'LINESTRING Z']:
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        utility_type = props.get('utility_type', 'Unknown')
        diameter = props.get('diameter_inches')
        network_mode = classification.network_mode
        
        cur.execute("""
            INSERT INTO utility_lines (
                project_id, utility_system, utility_mode, material, diameter_mm,
                geometry, attributes
            )
            VALUES (%s, %s, %s::utility_mode_enum, %s, %s, %s, %s)
            RETURNING line_id
        """, (
            project_id,
            utility_type,
            network_mode,
            'Unknown',
            int(diameter * 25.4) if diameter else None,
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        line_id = str(result[0]) if result else None
        
        if line_id and network_mode:
            network_id = self._get_or_create_network(project_id, utility_type, network_mode, cur)
            if network_id:
                self._add_to_network(network_id, line_id=line_id, cur=cur)
        
        cur.close()
        
        if line_id:
            return ('utility_line', line_id, 'utility_lines')
        return None
    
    def _create_utility_structure(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create utility_structures record."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['POINT', 'POINT Z']:
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        structure_type = props.get('structure_type', 'Unknown')
        utility_type = props.get('utility_type', 'Unknown')
        network_mode = classification.network_mode
        
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
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))
        
        result = cur.fetchone()
        structure_id = str(result[0]) if result else None
        
        if structure_id and network_mode:
            network_id = self._get_or_create_network(project_id, utility_type, network_mode, cur)
            if network_id:
                self._add_to_network(network_id, structure_id=structure_id, cur=cur)
        
        cur.close()
        
        if structure_id:
            return ('utility_structure', structure_id, 'utility_structures')
        return None
    
    def _create_bmp(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create bmps record."""
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        bmp_type = props.get('bmp_type', 'Unknown')
        design_volume = props.get('design_volume_cf')
        
        geometry_wkt = entity_data.get('geometry_wkt')
        area_sqft = None
        
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type in ['POLYGON', 'POLYGON Z']:
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
        if not self.conn:
            return None
        
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
        
        if not self.conn:
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
        
        if not self.conn:
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
        
        if not self.conn:
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
    
    def _create_parcel(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create parcels record."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['POLYGON', 'POLYGON Z']:
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        geometry_wkt = entity_data.get('geometry_wkt')
        layer_name = entity_data.get('layer_name', '')
        
        parcel_name = f"Parcel - {layer_name}"
        
        area_sqft = None
        area_acres = None
        perimeter = None
        
        cur.execute("""
            SELECT 
                ST_Area(ST_GeomFromText(%s, 2226)),
                ST_Area(ST_GeomFromText(%s, 2226)) / 43560.0,
                ST_Perimeter(ST_GeomFromText(%s, 2226))
        """, (geometry_wkt, geometry_wkt, geometry_wkt))
        result = cur.fetchone()
        if result:
            area_sqft = result[0]
            area_acres = result[1]
            perimeter = result[2]
        
        cur.execute("""
            INSERT INTO parcels (
                project_id, parcel_name, boundary_geometry,
                area_sqft, area_acres, perimeter, attributes
            )
            VALUES (%s, %s, ST_GeomFromText(%s, 2226), %s, %s, %s, %s)
            RETURNING parcel_id
        """, (
            project_id,
            parcel_name,
            geometry_wkt,
            area_sqft,
            area_acres,
            perimeter,
            json.dumps({'source': 'dxf_import', 'layer_name': layer_name, 'phase': props.get('phase', 'EXIST')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('parcel', str(result[0]), 'parcels')
        return None
    
    def _create_grading_feature(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create grading_limits record for grading features (swales, berms, pads, etc.)."""
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        geometry_wkt = entity_data.get('geometry_wkt')
        layer_name = entity_data.get('layer_name', '')
        geometry_type = entity_data.get('geometry_type', '').upper()
        
        limit_type = props.get('type', 'Grading')
        limit_name = f"{limit_type} - {layer_name}"
        
        area_sqft = None
        area_acres = None
        
        if geometry_type in ['POLYGON', 'POLYGON Z']:
            cur.execute("""
                SELECT 
                    ST_Area(ST_GeomFromText(%s, 2226)),
                    ST_Area(ST_GeomFromText(%s, 2226)) / 43560.0
            """, (geometry_wkt, geometry_wkt))
            result = cur.fetchone()
            if result:
                area_sqft = result[0]
                area_acres = result[1]
        
        cur.execute("""
            INSERT INTO grading_limits (
                project_id, limit_name, limit_type, boundary_geometry,
                area_sqft, area_acres, attributes
            )
            VALUES (%s, %s, %s, ST_GeomFromText(%s, 2226), %s, %s, %s)
            RETURNING limit_id
        """, (
            project_id,
            limit_name,
            limit_type,
            geometry_wkt,
            area_sqft,
            area_acres,
            json.dumps({'source': 'dxf_import', 'layer_name': layer_name, 'phase': props.get('phase', 'EXIST')})
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('grading_feature', str(result[0]), 'grading_limits')
        return None
    
    def _create_surface_feature(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create surface_features record for road features, ADA features, etc."""
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        geometry_wkt = entity_data.get('geometry_wkt')
        layer_name = entity_data.get('layer_name', '')
        
        feature_type = props.get('type', classification.object_type)
        
        cur.execute("""
            INSERT INTO surface_features (
                project_id, feature_type, geometry, attributes
            )
            VALUES (%s, %s, ST_GeomFromText(%s, 2226), %s)
            RETURNING feature_id
        """, (
            project_id,
            feature_type,
            geometry_wkt,
            json.dumps({
                'source': 'dxf_import',
                'layer_name': layer_name,
                'phase': props.get('phase', 'EXIST'),
                'object_type': classification.object_type
            })
        ))
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            return ('surface_feature', str(result[0]), 'surface_features')
        return None
    
    def _create_contour(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create surface_models record for contour lines."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['LINESTRING', 'LINESTRING Z']:
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        layer_name = entity_data.get('layer_name', '')
        surface_name = f"Contours - {layer_name}"
        
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
                'Contour',
                json.dumps({'source': 'dxf_import', 'layer_name': layer_name, 'phase': props.get('phase', 'EXIST')})
            ))
            result = cur.fetchone()
        
        cur.close()
        
        if result:
            return ('contour', str(result[0]), 'surface_models')
        return None
    
    def _create_spot_elevation(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create surface_models record for spot elevations."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['POINT', 'POINT Z']:
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        layer_name = entity_data.get('layer_name', '')
        surface_name = f"Spot Elevations - {layer_name}"
        
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
                'Spot Elevation',
                json.dumps({'source': 'dxf_import', 'layer_name': layer_name, 'phase': props.get('phase', 'EXIST')})
            ))
            result = cur.fetchone()
        
        cur.close()
        
        if result:
            return ('spot_elevation', str(result[0]), 'surface_models')
        return None
    
    def _create_generic_object(self, entity_data: Dict, classification: Optional[LayerClassification], project_id: str) -> Optional[Tuple]:
        """
        Create generic_objects record for unclassified or low-confidence entities.
        
        Args:
            entity_data: Dict with entity info
            classification: Optional classification result (may be None or low confidence)
            project_id: UUID of project
            
        Returns:
            Tuple of (object_type, object_id, table_name) or None
        """
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        
        layer_name = entity_data.get('layer_name', '')
        entity_type = entity_data.get('entity_type', 'UNKNOWN')
        geometry_wkt = entity_data.get('geometry_wkt', '')
        dxf_handle = entity_data.get('dxf_handle', '')
        
        # Extract classification info if available
        confidence = classification.confidence if classification else 0.0
        suggested_type = classification.object_type if classification else None
        
        # Generate a descriptive name
        object_name = f"{layer_name} ({entity_type})"
        
        try:
            # Use ST_GeomFromText with SRID 2226 (CA State Plane)
            # Note: If geometry is in SRID 0 (local CAD), it will be stored with that SRID
            cur.execute("""
                INSERT INTO generic_objects (
                    project_id, object_name, original_layer_name, original_entity_type,
                    classification_confidence, suggested_object_type,
                    geometry, source_dxf_handle, needs_review, review_status,
                    attributes
                )
                VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 2226), %s, TRUE, 'pending', %s)
                RETURNING object_id
            """, (
                project_id,
                object_name,
                layer_name,
                entity_type,
                confidence,
                suggested_type,
                geometry_wkt,
                dxf_handle,
                json.dumps({
                    'source': 'dxf_import',
                    'import_reason': 'low_confidence_classification',
                    'geometry_type': entity_data.get('geometry_type', '')
                })
            ))
            
            result = cur.fetchone()
            cur.close()
            
            if result:
                return ('generic_object', str(result[0]), 'generic_objects')
            return None
            
        except Exception as e:
            print(f"Error creating generic object: {e}")
            cur.close()
            return None
    
    def _create_entity_link(self, project_id: str, drawing_id: Optional[str], dxf_handle: str, entity_type: str,
                           layer_name: str, geometry_wkt: str,
                           object_type: str, object_id: str, table_name: str):
        """
        Create link between DXF entity and intelligent object.
        Supports both drawing-level and project-level imports (drawing_id can be None).
        
        Args:
            project_id: UUID of the project
            drawing_id: Optional UUID of the drawing (None for project-level imports)
            dxf_handle: DXF entity handle
            entity_type: Type of DXF entity
            layer_name: Layer name
            geometry_wkt: WKT representation of geometry
            object_type: Type of intelligent object created
            object_id: UUID of intelligent object
            table_name: Database table name for the object
        """
        if not self.conn:
            return
        
        cur = self.conn.cursor()
        
        geometry_hash = hashlib.sha256(geometry_wkt.encode()).hexdigest() if geometry_wkt else None
        
        # For project-level imports (drawing_id = None), use project_id + dxf_handle as unique key
        if drawing_id:
            # Legacy drawing-based import
            cur.execute("""
                INSERT INTO dxf_entity_links (
                    drawing_id, project_id, dxf_handle, entity_type, layer_name, 
                    entity_geom_hash, object_table_name, object_id, sync_state
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
                ON CONFLICT (drawing_id, dxf_handle) DO UPDATE SET
                    object_table_name = EXCLUDED.object_table_name,
                    object_id = EXCLUDED.object_id,
                    entity_geom_hash = EXCLUDED.entity_geom_hash,
                    sync_state = 'active',
                    last_seen_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                drawing_id, project_id, dxf_handle, entity_type, layer_name,
                geometry_hash, table_name, object_id
            ))
        else:
            # Project-level import (no drawing_id)
            # Use project_id + dxf_handle combination to track entity links
            cur.execute("""
                INSERT INTO dxf_entity_links (
                    drawing_id, project_id, dxf_handle, entity_type, layer_name, 
                    entity_geom_hash, object_table_name, object_id, sync_state
                )
                VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, 'active')
                ON CONFLICT (project_id, dxf_handle) 
                WHERE drawing_id IS NULL
                DO UPDATE SET
                    object_table_name = EXCLUDED.object_table_name,
                    object_id = EXCLUDED.object_id,
                    entity_geom_hash = EXCLUDED.entity_geom_hash,
                    sync_state = 'active',
                    last_seen_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                project_id, dxf_handle, entity_type, layer_name,
                geometry_hash, table_name, object_id
            ))
        
        cur.close()
    
    def _get_or_create_network(self, project_id: str, utility_system: str, network_mode: str, cur) -> Optional[str]:
        """Get existing network or create a new one for this project/utility/mode combination."""
        network_name = f"{utility_system} {network_mode.capitalize()} Network"
        
        cur.execute("""
            SELECT network_id FROM pipe_networks
            WHERE project_id = %s AND utility_system = %s AND network_mode = %s::utility_mode_enum
        """, (project_id, utility_system, network_mode))
        
        result = cur.fetchone()
        if result:
            return str(result[0])
        
        cur.execute("""
            INSERT INTO pipe_networks (
                project_id, network_name, utility_system, network_mode, network_status
            )
            VALUES (%s, %s, %s, %s::utility_mode_enum, 'active')
            RETURNING network_id
        """, (project_id, network_name, utility_system, network_mode))
        
        result = cur.fetchone()
        return str(result[0]) if result else None
    
    def _add_to_network(self, network_id: str, line_id: Optional[str] = None, structure_id: Optional[str] = None, cur=None):
        """Add a pipe or structure to a network."""
        if not cur:
            return
        
        cur.execute("""
            INSERT INTO utility_network_memberships (
                network_id, line_id, structure_id
            )
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (network_id, line_id, structure_id))
    
    def __del__(self):
        """Clean up connection if we created it."""
        # Use hasattr to prevent AttributeError if __init__ failed partway
        if hasattr(self, 'should_close_conn') and self.should_close_conn and hasattr(self, 'conn') and self.conn:
            self.conn.close()
