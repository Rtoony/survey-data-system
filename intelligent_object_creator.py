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

# Import DXFLookupService for layer management
from dxf_lookup_service import DXFLookupService


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
        # Initialize lookup service for layer management
        self.lookup_service = DXFLookupService(db_config, conn=conn)
    
    def create_from_entity(self, entity_data: Dict, project_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Create intelligent object from DXF entity data.

        Args:
            entity_data: Dict with entity info (type, layer, geometry, handle, etc.)
            project_id: UUID of project

        Returns:
            Tuple of (object_type, object_id, table_name) or None
        """
        layer_name = entity_data.get('layer_name', '')
        classification = self.classifier.classify(layer_name)
        
        # Initialize connection if needed (required for ALL object creation paths)
        if self.conn is None:
            self.conn = psycopg2.connect(**self.db_config)
            self.should_close_conn = True
        
        # NEW CLASSIFICATION SYSTEM: No more generic_objects
        # Instead, always create in target table but flag for review if low confidence
        if not classification or classification.confidence < 0.7:
            # Low confidence - create entity but flag for review
            classification_state = 'needs_review'
            # Use best guess for target type, or default to most common
            target_type = classification.object_type if classification else self._guess_type_from_geometry(entity_data)

            # Enrich with spatial context
            spatial_context = self._get_spatial_context(entity_data, project_id)

            # Get top 3 suggestions if uncertain
            suggestions = self._get_classification_suggestions(entity_data, classification, spatial_context)

            # Override classification with best guess
            if not classification:
                from layer_classifier import LayerClassification
                classification = LayerClassification(
                    object_type=target_type,
                    confidence=0.5,
                    properties={},
                    network_mode=None
                )
        else:
            # High confidence - auto-classify
            classification_state = 'auto_classified'
            target_type = classification.object_type
            suggestions = []
            spatial_context = {}
        
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

            elif classification.object_type == 'street_light':
                result = self._create_street_light(entity_data, classification, project_id)

            elif classification.object_type == 'pavement_zone':
                result = self._create_pavement_zone(entity_data, classification, project_id)

            elif classification.object_type == 'service_connection':
                result = self._create_service_connection(entity_data, classification, project_id)

            if result:
                object_type, object_id, table_name = result
                dxf_handle = entity_data.get('dxf_handle', '')
                entity_type = entity_data.get('entity_type', 'UNKNOWN')
                geometry_wkt = entity_data.get('geometry_wkt', '')

                # Ensure drawing_entities record with layer assignment (from classification)
                self._ensure_drawing_entity(
                    entity_id=object_id,
                    project_id=project_id,
                    classification=classification,
                    entity_data=entity_data,
                    is_generic=False
                )

                # NEW: Update standards_entities with classification metadata
                self._update_classification_metadata(
                    entity_id=object_id,
                    classification_state=classification_state,
                    confidence=classification.confidence if classification else 0.5,
                    suggestions=suggestions,
                    spatial_context=spatial_context,
                    target_table=table_name,
                    target_id=object_id,
                    project_id=project_id
                )

                # Create entity link for project-level imports
                if dxf_handle and geometry_wkt:
                    self._create_entity_link(
                        project_id, dxf_handle, entity_type,
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
        
        # Determine network_mode from properties with intelligent fallback
        network_mode = props.get('network_mode')
        if not network_mode:
            # Infer from utility type
            if utility_type.lower() in ['storm', 'sanitary', 'sewer']:
                network_mode = 'gravity'
            elif utility_type.lower() in ['water', 'potable', 'reuse', 'reclaim']:
                network_mode = 'pressure'
            else:
                network_mode = None  # Skip network association
        elif network_mode:
            # Normalize to lowercase for database enum compatibility
            network_mode = network_mode.lower()
        
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
        
        # Determine network_mode from properties with intelligent fallback
        network_mode = props.get('network_mode')
        if not network_mode:
            # Infer from utility type
            if utility_type.lower() in ['storm', 'sanitary', 'sewer']:
                network_mode = 'gravity'
            elif utility_type.lower() in ['water', 'potable', 'reuse', 'reclaim']:
                network_mode = 'pressure'
            else:
                network_mode = None  # Skip network association
        elif network_mode:
            # Normalize to lowercase for database enum compatibility
            network_mode = network_mode.lower()
        
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
        """Create storm_bmps record.
        
        IMPORTANT: storm_bmps.geometry requires MultiPolygon with SRID 3857.
        DXF imports use SRID 2226, so transformation is required.
        
        NOTE: Accepts both POLYGON and closed LINESTRING geometries.
        Closed linestrings (where first point == last point) are converted to polygons.
        """
        geometry_type = entity_data.get('geometry_type', '').upper()
        geometry_wkt = entity_data.get('geometry_wkt')
        
        # Accept polygons or closed linestrings (linestrings can represent polygon boundaries)
        if geometry_type not in ['POLYGON', 'POLYGON Z', 'LINESTRING', 'LINESTRING Z']:
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        # Extract BMP type from classification properties
        # Properties use 'object_type' key for the object type code (BIOR, POND, INFIL, etc.)
        type_code = props.get('object_type', 'UNK')
        
        # Map type codes to friendly names
        type_names = {
            'BIOR': 'Bioretention',
            'BIOF': 'Biofilter',
            'RAIN': 'Rain Garden',
            'POND': 'Detention Pond',
            'INFIL': 'Infiltration Basin',
            'BASIN': 'Detention Basin'
        }
        bmp_type = type_names.get(type_code, type_code)
        bmp_name = f"{bmp_type} - {entity_data.get('layer_name', 'BMP')}"
        design_volume = props.get('design_volume_cf')
        
        # For LINESTRING geometries, convert to polygon using ST_MakePolygon if closed
        if geometry_type in ['LINESTRING', 'LINESTRING Z']:
            # Check if linestring is closed (first point == last point)
            # If closed, convert to polygon using ST_MakePolygon
            geom_sql = "ST_MakePolygon(ST_GeomFromText(%s, 2226))"
        else:
            # Already a polygon, use directly
            geom_sql = "ST_GeomFromText(%s, 2226)"
        
        # Transform geometry from SRID 2226 (CAD) to SRID 3857 (Web Mercator)
        # Storm_bmps requires 2D geometry, so use ST_Force2D to strip Z coordinates
        # and ensure it's a MultiPolygon
        try:
            cur.execute(f"""
                INSERT INTO storm_bmps (
                    project_id, bmp_name, bmp_type, treatment_volume_cf,
                    geometry, attributes
                )
                VALUES (
                    %s, %s, %s, %s,
                    ST_Multi(ST_Force2D(ST_Transform({geom_sql}, 3857))),
                    %s
                )
                RETURNING bmp_id
            """, (
                project_id,
                bmp_name,
                bmp_type,
                design_volume,
                geometry_wkt,
                json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
            ))
            
            result = cur.fetchone()
            cur.close()
            
            if result:
                return ('bmp', str(result[0]), 'storm_bmps')
        except Exception as e:
            cur.close()
            return None
        
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
                alignment_geometry, attributes
            )
            VALUES (%s, %s, %s, ST_GeomFromText(%s, 2226), %s)
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
        """Create grading_limits record for grading features (swales, berms, pads, etc.).
        
        IMPORTANT: grading_limits.boundary_geometry requires Polygon type.
        Linear grading features (swales, berms as lines) are skipped here.
        """
        geometry_type = entity_data.get('geometry_type', '').upper()
        
        # Only accept polygons - grading_limits.boundary_geometry is Polygon-only
        if geometry_type not in ['POLYGON', 'POLYGON Z']:
            # Skip linear grading features - they could be routed to surface_features if needed
            return None
        
        if not self.conn:
            return None
        
        cur = self.conn.cursor()
        props = classification.properties
        
        geometry_wkt = entity_data.get('geometry_wkt')
        layer_name = entity_data.get('layer_name', '')
        
        limit_type = props.get('type', 'Grading')
        limit_name = f"{limit_type} - {layer_name}"
        
        # Calculate area for polygons
        cur.execute("""
            SELECT 
                ST_Area(ST_GeomFromText(%s, 2226)),
                ST_Area(ST_GeomFromText(%s, 2226)) / 43560.0
        """, (geometry_wkt, geometry_wkt))
        result = cur.fetchone()
        area_sqft = result[0] if result else None
        area_acres = result[1] if result else None
        
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
    
    # REMOVED: _create_generic_object - now using classification metadata in standards_entities instead
    
    def _ensure_drawing_entity(self, entity_id: str, project_id: str, classification: Optional[LayerClassification],
                               entity_data: Dict, is_generic: bool = False) -> None:
        """
        Ensure drawing_entities record exists with proper layer_id assignment.
        
        This centralizes layer assignment logic for all object types, including generics.
        
        Args:
            entity_id: UUID of the created entity/object
            project_id: UUID of the project
            classification: LayerClassification result (can be None for generics)
            entity_data: Original entity data dict
            is_generic: Whether this is a generic object (use fallback layer)
        """
        if not self.conn:
            return
        
        cur = self.conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Determine the layer name to use
            if is_generic or not classification:
                # Generic objects get a fallback "GENERIC-UNCLASSIFIED" layer
                layer_name = "GENERIC-UNCLASSIFIED"
            else:
                # Use standard_layer_name from classification, fallback to original
                layer_name = getattr(classification, 'standard_layer_name', None) or \
                            getattr(classification, 'original_layer_name', None) or \
                            entity_data.get('layer_name', 'UNKNOWN')
            
            # Get or create the layer and get its layer_id
            # This will create both layers record (project-specific) and link to layer_standards
            layer_id, layer_standard_id = self.lookup_service.get_or_create_layer(
                layer_name=layer_name,
                project_id=project_id
            )
            
            # Prepare entity data for drawing_entities
            entity_type = entity_data.get('entity_type', 'UNKNOWN')
            geometry_wkt = entity_data.get('geometry_wkt', '')
            
            # Upsert drawing_entities record with layer_id
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
                entity_type,
                geometry_wkt
            ))
            
            self.conn.commit()
            cur.close()
            
        except Exception as e:
            print(f"Error ensuring drawing_entity for {entity_id}: {e}")
            import traceback
            traceback.print_exc()
            cur.close()
    
    def _create_entity_link(self, project_id: str, dxf_handle: str, entity_type: str,
                           layer_name: str, geometry_wkt: str,
                           object_type: str, object_id: str, table_name: str):
        """
        Create link between DXF entity and intelligent object.

        Args:
            project_id: UUID of the project
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

    def _create_street_light(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create street_lights record."""
        if entity_data.get('geometry_type') not in ['POINT', 'POINT Z']:
            return None

        if not self.conn:
            return None

        cur = self.conn.cursor()
        props = classification.properties

        # Extract lamp type and height from properties
        lamp_type = props.get('lamp_type', 'LED')
        pole_height_ft = props.get('height', 25)

        # Generate pole number
        cur.execute("SELECT COUNT(*) FROM street_lights WHERE project_id = %s", (project_id,))
        count = cur.fetchone()[0] if cur.rowcount > 0 else 0
        pole_number = f"L-{count + 1}"

        cur.execute("""
            INSERT INTO street_lights (
                project_id, pole_number, lamp_type, pole_height_ft,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING light_id
        """, (
            project_id,
            pole_number,
            lamp_type,
            pole_height_ft,
            entity_data.get('geometry_wkt'),
            json.dumps({'source': 'dxf_import', 'layer_name': entity_data.get('layer_name')})
        ))

        result = cur.fetchone()
        cur.close()

        if result:
            return ('street_light', str(result[0]), 'street_lights')
        return None

    def _create_pavement_zone(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create pavement_zones record."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['POLYGON', 'POLYGON Z', 'POLYLINE', 'LWPOLYLINE']:
            return None

        if not self.conn:
            return None

        cur = self.conn.cursor()
        props = classification.properties

        # Extract pavement properties
        pavement_type = props.get('pavement_type', 'ASPH')
        thickness_inches = props.get('thickness', 6)

        geometry_wkt = entity_data.get('geometry_wkt')
        layer_name = entity_data.get('layer_name', '')

        # Generate zone name
        cur.execute("SELECT COUNT(*) FROM pavement_zones WHERE project_id = %s", (project_id,))
        count = cur.fetchone()[0] if cur.rowcount > 0 else 0
        zone_name = f"ZONE-{count + 1}"

        # Calculate area from geometry
        cur.execute("""
            SELECT ST_Area(ST_GeomFromText(%s, 2226))
        """, (geometry_wkt,))
        area_result = cur.fetchone()
        area_sqft = area_result[0] if area_result else None

        cur.execute("""
            INSERT INTO pavement_zones (
                project_id, zone_name, pavement_type, thickness_inches, area_sqft,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING zone_id
        """, (
            project_id,
            zone_name,
            pavement_type,
            thickness_inches,
            area_sqft,
            geometry_wkt,
            json.dumps({'source': 'dxf_import', 'layer_name': layer_name})
        ))

        result = cur.fetchone()
        cur.close()

        if result:
            return ('pavement_zone', str(result[0]), 'pavement_zones')
        return None

    def _create_service_connection(self, entity_data: Dict, classification: LayerClassification, project_id: str) -> Optional[Tuple]:
        """Create utility_service_connections record (laterals)."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if geometry_type not in ['LINESTRING', 'LINESTRING Z', 'POLYLINE', 'LWPOLYLINE']:
            return None

        if not self.conn:
            return None

        cur = self.conn.cursor()
        props = classification.properties

        # Extract lateral properties
        service_type_map = {
            'SEW': 'SEWER_LATERAL',
            'WAT': 'WATER_LATERAL',
            'WATER': 'WATER_LATERAL'
        }
        service_type_code = props.get('service_type', 'SEW')
        service_type = service_type_map.get(service_type_code, 'SEWER_LATERAL')

        diameter_in = props.get('diameter', 4)
        size_mm = int(diameter_in * 25.4) if diameter_in else 100

        geometry_wkt = entity_data.get('geometry_wkt')
        layer_name = entity_data.get('layer_name', '')

        # Calculate length
        cur.execute("""
            SELECT ST_Length(ST_GeomFromText(%s, 2226))
        """, (geometry_wkt,))
        length_result = cur.fetchone()
        length_ft = length_result[0] if length_result else None

        cur.execute("""
            INSERT INTO utility_service_connections (
                project_id, service_type, size_mm, length_ft,
                geometry, attributes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING connection_id
        """, (
            project_id,
            service_type,
            size_mm,
            length_ft,
            geometry_wkt,
            json.dumps({'source': 'dxf_import', 'layer_name': layer_name, 'diameter_in': diameter_in})
        ))

        result = cur.fetchone()
        cur.close()

        if result:
            return ('service_connection', str(result[0]), 'utility_service_connections')
        return None

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

    def _get_spatial_context(self, entity_data: Dict, project_id: str, radius_ft: float = 50.0) -> Dict:
        """
        Analyze spatial context around entity.
        Returns counts of nearby objects within radius.
        """
        if not self.conn:
            return {}

        geometry_wkt = entity_data.get('geometry_wkt')
        if not geometry_wkt:
            return {}

        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # Count nearby utility lines
            cur.execute("""
                SELECT COUNT(*) as count
                FROM utility_lines
                WHERE project_id = %s
                AND ST_DWithin(
                    geometry::geography,
                    ST_GeomFromText(%s, 2226)::geography,
                    %s
                )
            """, (project_id, geometry_wkt, radius_ft * 0.3048))  # Convert ft to meters
            nearby_lines = cur.fetchone()['count']

            # Count nearby structures
            cur.execute("""
                SELECT COUNT(*) as count
                FROM utility_structures
                WHERE project_id = %s
                AND ST_DWithin(
                    rim_geometry::geography,
                    ST_GeomFromText(%s, 2226)::geography,
                    %s
                )
            """, (project_id, geometry_wkt, radius_ft * 0.3048))
            nearby_structures = cur.fetchone()['count']

            # Find distance to nearest pipe
            cur.execute("""
                SELECT ST_Distance(
                    geometry::geography,
                    ST_GeomFromText(%s, 2226)::geography
                ) as distance
                FROM utility_lines
                WHERE project_id = %s
                ORDER BY geometry::geography <-> ST_GeomFromText(%s, 2226)::geography
                LIMIT 1
            """, (geometry_wkt, project_id, geometry_wkt))

            nearest = cur.fetchone()
            distance_to_nearest = nearest['distance'] if nearest else None

            cur.close()

            return {
                'nearby_utility_lines': nearby_lines,
                'nearby_structures': nearby_structures,
                'distance_to_nearest_pipe_m': distance_to_nearest,
                'radius_analyzed_ft': radius_ft
            }

        except Exception as e:
            print(f"Spatial context analysis failed: {e}")
            return {}

    def _get_classification_suggestions(self, entity_data: Dict, classification: Optional[LayerClassification], spatial_context: Dict) -> list:
        """
        Generate top 3 classification suggestions with reasons.
        Combines layer classifier + spatial context + geometry heuristics.
        """
        from typing import List
        suggestions = []
        geometry_type = entity_data.get('geometry_type', '').upper()

        # Suggestion 1: Layer classifier result
        if classification and classification.confidence > 0.3:
            suggestions.append({
                'type': classification.object_type,
                'confidence': classification.confidence,
                'reason': 'layer_pattern'
            })

        # Suggestion 2: Spatial context
        if spatial_context.get('nearby_structures', 0) >= 3 and 'POINT' in geometry_type:
            suggestions.append({
                'type': 'utility_structure',
                'confidence': min(0.7, spatial_context['nearby_structures'] / 10.0),
                'reason': f"{spatial_context['nearby_structures']} nearby structures"
            })

        if spatial_context.get('nearby_utility_lines', 0) >= 5 and 'LINESTRING' in geometry_type:
            suggestions.append({
                'type': 'utility_line',
                'confidence': min(0.7, spatial_context['nearby_utility_lines'] / 20.0),
                'reason': f"{spatial_context['nearby_utility_lines']} nearby pipes"
            })

        # Suggestion 3: Geometry-based default
        if 'POINT' in geometry_type:
            suggestions.append({
                'type': 'survey_point',
                'confidence': 0.4,
                'reason': 'point_geometry_default'
            })
        elif 'LINESTRING' in geometry_type:
            suggestions.append({
                'type': 'utility_line',
                'confidence': 0.4,
                'reason': 'line_geometry_default'
            })
        elif 'POLYGON' in geometry_type:
            suggestions.append({
                'type': 'bmp',
                'confidence': 0.4,
                'reason': 'polygon_geometry_default'
            })

        # Deduplicate and sort by confidence
        unique_suggestions = {}
        for s in suggestions:
            if s['type'] not in unique_suggestions or s['confidence'] > unique_suggestions[s['type']]['confidence']:
                unique_suggestions[s['type']] = s

        return sorted(unique_suggestions.values(), key=lambda x: x['confidence'], reverse=True)[:3]

    def _guess_type_from_geometry(self, entity_data: Dict) -> str:
        """Fallback: guess type from geometry when no classification."""
        geometry_type = entity_data.get('geometry_type', '').upper()
        if 'POINT' in geometry_type:
            return 'survey_point'
        elif 'LINESTRING' in geometry_type:
            return 'utility_line'
        elif 'POLYGON' in geometry_type:
            return 'bmp'
        else:
            return 'utility_line'  # Default fallback

    def _update_classification_metadata(self, entity_id: str, classification_state: str,
                                        confidence: float, suggestions: list,
                                        spatial_context: Dict, target_table: str,
                                        target_id: str, project_id: str):
        """Update standards_entities with classification metadata."""
        if not self.conn:
            return

        from datetime import datetime

        try:
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE standards_entities
                SET classification_state = %s,
                    classification_confidence = %s,
                    classification_metadata = %s,
                    target_table = %s,
                    target_id = %s,
                    project_id = %s
                WHERE entity_id = %s
            """, (
                classification_state,
                confidence,
                json.dumps({
                    'suggestions': suggestions,
                    'spatial_context': spatial_context,
                    'classified_at': datetime.utcnow().isoformat()
                }),
                target_table,
                target_id,
                project_id,
                entity_id
            ))
            cur.close()
        except Exception as e:
            print(f"Failed to update classification metadata: {e}")

    def __del__(self):
        """Clean up connection if we created it."""
        # Use hasattr to prevent AttributeError if __init__ failed partway
        if hasattr(self, 'should_close_conn') and self.should_close_conn and hasattr(self, 'conn') and self.conn:
            self.conn.close()
