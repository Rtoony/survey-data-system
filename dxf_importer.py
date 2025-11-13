"""
DXF Importer Module
Parses DXF files and stores entities in the database.
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple
import os
import math
import hashlib
from dxf_lookup_service import DXFLookupService
from intelligent_object_creator import IntelligentObjectCreator


class DXFImporter:
    """Import DXF files and store entities in PostgreSQL database."""
    
    def __init__(self, db_config: Dict, create_intelligent_objects: bool = True):
        """Initialize importer with database configuration."""
        self.db_config = db_config
        self.create_intelligent_objects = create_intelligent_objects
    
    def import_dxf(self, file_path: str, project_id: str, 
                   coordinate_system: str = 'LOCAL', 
                   import_modelspace: bool = True,
                   import_paperspace: bool = True,
                   external_conn=None) -> Dict:
        """
        Import a DXF file into the database at project level.
        
        Args:
            file_path: Path to DXF file
            project_id: ID of the project to associate entities with
            coordinate_system: Coordinate system ('LOCAL', 'WGS84', etc.')
            import_modelspace: Whether to import model space entities
            import_paperspace: Whether to import paper space entities
            external_conn: Optional external database connection (will not be closed)
            
        Returns:
            Dictionary with import statistics
        """
        # Map coordinate system to SRID
        srid_map = {
            'LOCAL': 0,  # Local CAD coordinates (no projection)
            'STATE_PLANE': 2226,  # CA State Plane Zone 2, US Survey Feet (NAD83)
            'WGS84': 4326  # WGS84 geographic coordinates
        }
        self.srid = srid_map.get(coordinate_system.upper(), 0)
        
        stats = {
            'entities': 0,
            'text': 0,
            'dimensions': 0,
            'hatches': 0,
            'blocks': 0,
            'viewports': 0,
            'points': 0,
            '3dfaces': 0,
            'solids': 0,
            'meshes': 0,
            'leaders': 0,
            'intelligent_objects_created': 0,
            'layers': set(),
            'linetypes': set(),
            'errors': []
        }
        
        # Use external connection or create new one
        owns_connection = external_conn is None
        conn = external_conn if external_conn else psycopg2.connect(**self.db_config)
        
        try:
            # Read DXF file
            doc = ezdxf.readfile(file_path)
            
            # Set autocommit only if we own the connection
            if owns_connection:
                conn.autocommit = False
            
            try:
                # Initialize lookup service with connection for transaction support
                resolver = DXFLookupService(self.db_config, conn=conn)
                
                # Import layers (project-level, no drawing tracking)
                self._import_layers(doc, project_id, conn, stats, resolver)
                
                # Import linetypes (no drawing-level tracking needed)
                self._import_linetypes(doc, conn, stats, resolver)
                
                # Import model space
                if import_modelspace:
                    modelspace = doc.modelspace()
                    self._import_entities(modelspace, project_id, 'MODEL', conn, stats, resolver)
                
                # Import paper space layouts
                if import_paperspace:
                    for layout_name in doc.layout_names():
                        if layout_name != 'Model':
                            layout = doc.layout(layout_name)
                            self._import_entities(layout, project_id, 'PAPER', conn, stats, resolver)
                            self._import_viewports(layout, project_id, conn, stats, resolver)
                
                # Create intelligent objects from imported entities
                if self.create_intelligent_objects:
                    stats['intelligent_objects_created'] = self._create_intelligent_objects(
                        project_id, conn, stats
                    )
                
                # Only commit if we own the connection
                if owns_connection:
                    conn.commit()
                
            except Exception as e:
                # Only rollback if we own the connection
                if owns_connection:
                    conn.rollback()
                raise e
            finally:
                # Only close if we own the connection
                if owns_connection:
                    conn.close()
                
        except Exception as e:
            stats['errors'].append(f"Import failed: {str(e)}")
        
        # Convert sets to counts for JSON serialization
        stats['layers'] = len(stats['layers'])
        stats['linetypes'] = len(stats['linetypes'])
        
        return stats
    
    def _create_intelligent_objects(self, project_id: str, conn, stats: Dict) -> int:
        """
        Create intelligent civil engineering objects from imported DXF entities.
        
        Args:
            project_id: UUID of the project
            conn: Database connection
            stats: Import statistics dictionary
            
        Returns:
            Count of intelligent objects created
        """
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query recently imported entities from this project (last 10 minutes)
        # Since entities are no longer tied to drawings, we query by project and recent timestamp
        cur.execute(f"""
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
            WHERE de.created_at >= NOW() - INTERVAL '10 minutes'
            ORDER BY de.created_at DESC
        """)
        
        entities = cur.fetchall()
        cur.close()
        
        # Initialize intelligent object creator
        creator = IntelligentObjectCreator(self.db_config, conn=conn)
        
        created_count = 0
        
        for entity in entities:
            try:
                # Prepare entity data dictionary
                entity_data = {
                    'entity_id': str(entity['entity_id']),
                    'entity_type': entity['entity_type'],
                    'layer_name': entity['layer_name'],
                    'geometry_wkt': entity['geometry_wkt'],
                    'geometry_type': entity['geometry_type'].replace('ST_', ''),  # ST_LineString -> LineString
                    'dxf_handle': entity['dxf_handle'],
                    'color_aci': entity['color_aci'],
                    'linetype': entity['linetype'],
                    'space_type': entity['space_type']
                }
                
                # Attempt to create intelligent object (no drawing_id needed)
                result = creator.create_from_entity(entity_data, project_id, None)
                
                if result:
                    created_count += 1
                    object_type, object_id, table_name = result
                    # Optional: Log successful creation
                    # print(f"Created {object_type} {object_id} from {entity['entity_type']} on {entity['layer_name']}")
                    
            except Exception as e:
                stats['errors'].append(f"Failed to create intelligent object from entity {entity.get('dxf_handle', 'unknown')}: {str(e)}")
                continue
        
        return created_count
    
    def _import_layers(self, doc, project_id: str, 
                       conn, stats: Dict, resolver: DXFLookupService):
        """Import layers at project level (no drawing-level tracking)."""
        for layer in doc.layers:
            layer_name = layer.dxf.name
            stats['layers'].add(layer_name)
            
            # Get or create layer (project-level, no drawing association)
            color_aci = layer.dxf.color if hasattr(layer.dxf, 'color') else 7
            linetype = layer.dxf.linetype if hasattr(layer.dxf, 'linetype') else 'Continuous'
            
            layer_id, layer_standard_id = resolver.get_or_create_layer(
                layer_name, 
                project_id=project_id, 
                drawing_id=None,
                color_aci=color_aci, 
                linetype=linetype
            )
    
    def _import_linetypes(self, doc,
                          conn, stats: Dict, resolver: DXFLookupService):
        """Import linetypes (no drawing-level tracking needed)."""
        for linetype in doc.linetypes:
            linetype_name = linetype.dxf.name
            stats['linetypes'].add(linetype_name)
            
            # Get linetype standard ID (no drawing-level usage tracking)
            linetype_standard_id = resolver.get_or_create_linetype(linetype_name)
    
    def _import_entities(self, layout, project_id: str, space: str, 
                         conn, stats: Dict, resolver: DXFLookupService):
        """Import entities from a layout at project level."""
        for entity in layout:
            entity_type = entity.dxftype()
            
            try:
                if entity_type in ['LINE', 'POLYLINE', 'LWPOLYLINE', 'ARC', 
                                   'CIRCLE', 'ELLIPSE', 'SPLINE']:
                    self._import_entity(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type == 'POINT':
                    self._import_point(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type == '3DFACE':
                    self._import_3dface(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type in ['3DSOLID', 'BODY']:
                    self._import_3dsolid(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type in ['MESH', 'POLYMESH', 'POLYFACE']:
                    self._import_mesh(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type in ['LEADER', 'MULTILEADER']:
                    self._import_leader(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type in ['TEXT', 'MTEXT']:
                    self._import_text(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type.startswith('DIMENSION'):
                    self._import_dimension(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type == 'HATCH':
                    self._import_hatch(entity, project_id, space, conn, stats, resolver)
                
                elif entity_type == 'INSERT':
                    self._import_block_insert(entity, project_id, space, conn, stats, resolver)
                    
            except Exception as e:
                stats['errors'].append(
                    f"Failed to import {entity_type}: {str(e)}"
                )
    
    def _import_entity(self, entity, project_id: str, space: str, 
                       conn, stats: Dict, resolver: DXFLookupService):
        """Import generic drawing entity at project level (line, arc, circle, etc.)."""
        cur = conn.cursor()
        
        entity_type = entity.dxftype()
        layer_name = entity.dxf.layer
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        lineweight = entity.dxf.lineweight if hasattr(entity.dxf, 'lineweight') else -1
        linetype = entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer'
        dxf_handle = entity.dxf.handle if hasattr(entity.dxf, 'handle') else None
        transparency = entity.dxf.transparency if hasattr(entity.dxf, 'transparency') else 0
        
        # Resolve layer to get layer_id (no drawing association)
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None,
            color_aci=color_aci, 
            linetype=linetype
        )
        
        # Convert entity to WKT geometry
        geometry_wkt = self._entity_to_wkt(entity)
        
        if geometry_wkt:
            try:
                # Store DXF-specific properties in attributes
                attributes = {
                    'layer_name': layer_name,
                    'linetype': linetype,
                    'entity_type': entity_type
                }
                
                # Insert geometry using ST_GeomFromText
                # The POLYGON Z WKT format should preserve the polygon type
                geom_cast = f"ST_GeomFromText(%s, {self.srid})"
                
                # Insert entity with NULL drawing_id (project-level import)
                cur.execute(f"""
                    INSERT INTO drawing_entities (
                        drawing_id, entity_type, layer_id, space_type,
                        geometry, dxf_handle, color_aci, lineweight, linetype, 
                        transparency, quality_score, tags, attributes
                    )
                    VALUES (NULL, %s, %s, %s, {geom_cast}, %s, %s, %s, %s, %s, 0.5, '{{}}', %s)
                """, (
                    entity_type, layer_id, space,
                    geometry_wkt, dxf_handle, color_aci, lineweight, linetype,
                    transparency, json.dumps(attributes)
                ))
                
                stats['entities'] += 1
            except Exception as e:
                error_msg = f"Failed to insert {entity_type} on layer {layer_name}: {str(e)}"
                print(f"ERROR: {error_msg}")
                stats['errors'].append(error_msg)
        else:
            error_msg = f"Failed to convert {entity_type} on layer {layer_name} to WKT geometry"
            print(f"WARNING: {error_msg}")
            stats['errors'].append(error_msg)
        
        cur.close()
    
    def _entity_to_wkt(self, entity) -> Optional[str]:
        """Convert DXF entity to WKT geometry string."""
        entity_type = entity.dxftype()
        
        try:
            if entity_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                return f'LINESTRING Z ({start.x} {start.y} {start.z}, {end.x} {end.y} {end.z})'
            
            elif entity_type == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                # Approximate circle with 32 points
                points = []
                for i in range(33):
                    angle = 2 * math.pi * i / 32
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    points.append(f'{x} {y} {center.z}')
                return f'LINESTRING Z ({", ".join(points)})'
            
            elif entity_type == 'ARC':
                center = entity.dxf.center
                radius = entity.dxf.radius
                start_angle = math.radians(entity.dxf.start_angle)
                end_angle = math.radians(entity.dxf.end_angle)
                
                # Approximate arc with points
                points = []
                segments = 32
                if end_angle < start_angle:
                    end_angle += 2 * math.pi
                angle_range = end_angle - start_angle
                
                for i in range(segments + 1):
                    angle = start_angle + (angle_range * i / segments)
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    points.append(f'{x} {y} {center.z}')
                return f'LINESTRING Z ({", ".join(points)})'
            
            elif entity_type == 'POLYLINE':
                points = []
                # Use vertices directly to ensure Z-values are preserved
                for vertex in entity.vertices:
                    loc = vertex.dxf.location
                    points.append(f'{loc.x} {loc.y} {loc.z}')
                
                if len(points) > 0:
                    # Check if polyline is closed (closed flag or first==last vertex)
                    is_closed = entity.is_closed or (len(points) >= 3 and points[0] == points[-1])
                    
                    if is_closed:
                        # Ensure first and last points match for valid polygon
                        if points[0] != points[-1]:
                            points.append(points[0])
                        return f'POLYGON Z (({", ".join(points)}))'
                    else:
                        return f'LINESTRING Z ({", ".join(points)})'
            
            elif entity_type == 'LWPOLYLINE':
                points = []
                vertices = list(entity.vertices())
                z = entity.dxf.elevation if hasattr(entity.dxf, 'elevation') else 0
                
                for x, y in vertices:
                    points.append(f'{x} {y} {z}')
                
                if len(points) > 0:
                    # Check if LWPOLYLINE is closed (closed flag or first==last vertex)
                    is_closed = entity.closed or (len(vertices) >= 3 and vertices[0] == vertices[-1])
                    
                    if is_closed:
                        # Ensure first and last points match for valid polygon
                        if vertices[0] != vertices[-1]:
                            x, y = vertices[0]
                            points.append(f'{x} {y} {z}')
                        return f'POLYGON Z (({", ".join(points)}))'
                    else:
                        return f'LINESTRING Z ({", ".join(points)})'
            
            elif entity_type == 'ELLIPSE':
                # Approximate ellipse with points
                center = entity.dxf.center
                major_axis = entity.dxf.major_axis
                ratio = entity.dxf.ratio
                
                points = []
                for i in range(33):
                    angle = 2 * math.pi * i / 32
                    x = center.x + major_axis.x * math.cos(angle)
                    y = center.y + major_axis.y * ratio * math.sin(angle)
                    points.append(f'{x} {y} {center.z}')
                return f'LINESTRING Z ({", ".join(points)})'
            
        except Exception as e:
            print(f"Error converting {entity_type} to WKT: {e}")
            return None
        
        return None
    
    def _import_text(self, entity, project_id: str, space: str, 
                     conn, stats: Dict, resolver: DXFLookupService):
        """Import text entity at project level."""
        cur = conn.cursor()
        
        entity_type = entity.dxftype()
        layer_name = entity.dxf.layer
        dxf_handle = entity.dxf.handle if hasattr(entity.dxf, 'handle') else None
        
        # Resolve layer to get layer_id (no drawing association)
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None
        )
        
        # Get text properties
        text_content = entity.dxf.text if entity_type == 'TEXT' else entity.text
        insert_point = entity.dxf.insert
        height = entity.dxf.height if hasattr(entity.dxf, 'height') else 1.0
        rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0
        
        # Get text style
        style_name = entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard'
        
        # Get alignment
        if entity_type == 'TEXT':
            halign = entity.dxf.halign if hasattr(entity.dxf, 'halign') else 0
            valign = entity.dxf.valign if hasattr(entity.dxf, 'valign') else 0
            h_just = ['LEFT', 'CENTER', 'RIGHT'][min(halign, 2)]
            v_just = ['BASELINE', 'BOTTOM', 'MIDDLE', 'TOP'][min(valign, 3)]
        else:
            attachment_point = entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 1
            h_just = 'LEFT'
            v_just = 'BASELINE'
        
        # Create point geometry (SRID 2226 for California State Plane Zone 2)
        geometry_wkt = f'POINT Z ({insert_point.x} {insert_point.y} {insert_point.z})'
        
        # Attributes for AI optimization
        attributes = {
            'layer_name': layer_name,
            'text_style': style_name,
            'entity_type': entity_type
        }
        
        cur.execute(f"""
            INSERT INTO drawing_text (
                drawing_id, layer_id, space_type, text_content,
                insertion_point, text_height, rotation_angle,
                text_style, horizontal_justification, vertical_justification,
                dxf_handle, quality_score, tags, attributes
            )
            VALUES (NULL, %s::uuid, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s, %s, %s, 0.5, '{{}}', %s)
        """, (
            layer_id, space, text_content,
            geometry_wkt, height, rotation, style_name, h_just, v_just,
            dxf_handle, json.dumps(attributes)
        ))
        
        stats['text'] += 1
        cur.close()
    
    def _import_dimension(self, entity, project_id: str, space: str,
                          conn, stats: Dict, resolver: DXFLookupService):
        """Import dimension entity at project level."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        dim_type = entity.dxftype()
        dxf_handle = entity.dxf.handle if hasattr(entity.dxf, 'handle') else None
        
        # Resolve layer to get layer_id (no drawing association)
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None
        )
        
        # Get measurement and text
        dimension_text = entity.dxf.text if hasattr(entity.dxf, 'text') else ''
        measured_value = float(entity.get_measurement()) if hasattr(entity, 'get_measurement') else None
        
        # Get dimension style
        dimstyle_name = entity.dxf.dimstyle if hasattr(entity.dxf, 'dimstyle') else 'Standard'
        
        # Attributes for AI optimization
        attributes = {
            'layer_name': layer_name,
            'dimension_style': dimstyle_name,
            'entity_type': dim_type
        }
        
        cur.execute(f"""
            INSERT INTO drawing_dimensions (
                drawing_id, layer_id, space_type, dimension_type,
                measured_value, dimension_text, dimension_style,
                dxf_handle, quality_score, tags, attributes
            )
            VALUES (NULL, %s::uuid, %s, %s, %s, %s, %s, %s, 0.5, '{{}}', %s)
        """, (
            layer_id, space, dim_type,
            measured_value, dimension_text, dimstyle_name,
            dxf_handle, json.dumps(attributes)
        ))
        
        stats['dimensions'] += 1
        cur.close()
    
    def _import_hatch(self, entity, project_id: str, space: str,
                      conn, stats: Dict, resolver: DXFLookupService):
        """Import hatch entity at project level."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        pattern_name = entity.dxf.pattern_name if hasattr(entity.dxf, 'pattern_name') else 'SOLID'
        dxf_handle = entity.dxf.handle if hasattr(entity.dxf, 'handle') else None
        
        # Resolve layer to get layer_id (no drawing association)
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None
        )
        
        # Get hatch boundary
        try:
            # Get boundary paths and convert to WKT polygon
            boundaries = []
            for path in entity.paths:
                if path.path_type_flags & 2:  # Polyline path
                    points = [(v[0], v[1]) for v in path.vertices]
                    if len(points) > 2:
                        # Close the polygon
                        if points[0] != points[-1]:
                            points.append(points[0])
                        point_str = ', '.join([f'{p[0]} {p[1]} 0' for p in points])
                        boundaries.append(f'(({point_str}))')
            
            if boundaries:
                geometry_wkt = f'POLYGON Z {boundaries[0]}'
                
                # Get pattern properties
                scale = entity.dxf.pattern_scale if hasattr(entity.dxf, 'pattern_scale') else 1.0
                angle = entity.dxf.pattern_angle if hasattr(entity.dxf, 'pattern_angle') else 0.0
                
                # Attributes for AI optimization
                attributes = {
                    'layer_name': layer_name,
                    'pattern_name': pattern_name,
                    'is_solid': pattern_name.upper() == 'SOLID'
                }
                
                cur.execute(f"""
                    INSERT INTO drawing_hatches (
                        drawing_id, layer_id, space_type, hatch_pattern,
                        boundary_geometry, hatch_scale, hatch_angle,
                        dxf_handle, quality_score, tags, attributes
                    )
                    VALUES (NULL, %s::uuid, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, 0.5, '{{}}', %s)
                """, (
                    layer_id, space, pattern_name,
                    geometry_wkt, scale, angle,
                    dxf_handle, json.dumps(attributes)
                ))
                
                stats['hatches'] += 1
                
        except Exception as e:
            stats['errors'].append(f"Failed to import hatch: {str(e)}")
        
        cur.close()
    
    def _import_block_insert(self, entity, project_id: str, space: str,
                             conn, stats: Dict, resolver: DXFLookupService):
        """Import block insert at project level."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        block_name = entity.dxf.name
        insert_point = entity.dxf.insert
        dxf_handle = entity.dxf.handle if hasattr(entity.dxf, 'handle') else None
        
        # Resolve layer to get layer_id (no drawing association)
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None
        )
        
        # Get transformation
        scale_x = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1.0
        scale_y = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1.0
        scale_z = entity.dxf.zscale if hasattr(entity.dxf, 'zscale') else 1.0
        rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0
        
        # Create point geometry
        geometry_wkt = f'POINT Z ({insert_point.x} {insert_point.y} {insert_point.z})'
        
        # Attributes for AI optimization
        attributes = {
            'layer_name': layer_name,
            'block_name': block_name,
            'entity_type': 'INSERT'
        }
        
        try:
            cur.execute(f"""
                INSERT INTO block_inserts (
                    drawing_id, layer_id, block_name, insertion_point,
                    scale_x, scale_y, scale_z, rotation,
                    dxf_handle, quality_score, tags, attributes
                )
                VALUES (NULL, %s::uuid, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s, %s, 0.5, '{{}}', %s)
            """, (
                layer_id, block_name, geometry_wkt,
                scale_x, scale_y, scale_z, rotation,
                dxf_handle, json.dumps(attributes)
            ))
            
            stats['blocks'] += 1
        except Exception as e:
            stats['errors'].append(f"Failed to import block insert: {str(e)}")
        
        cur.close()
    
    def _import_viewports(self, layout, project_id: str, conn, stats: Dict, resolver: DXFLookupService):
        """Import paper space viewports at project level."""
        cur = conn.cursor()
        
        for viewport in layout.viewports():
            try:
                center = viewport.dxf.center
                view_center = viewport.dxf.view_center_point if hasattr(viewport.dxf, 'view_center_point') else center
                
                # Get viewport properties
                width = viewport.dxf.width if hasattr(viewport.dxf, 'width') else 0
                height = viewport.dxf.height if hasattr(viewport.dxf, 'height') else 0
                scale = viewport.dxf.custom_scale if hasattr(viewport.dxf, 'custom_scale') else 1.0
                
                # Create polygon geometry for viewport boundary
                x1, y1 = center.x - width/2, center.y - height/2
                x2, y2 = center.x + width/2, center.y + height/2
                geometry_wkt = f'POLYGON Z (({x1} {y1} 0, {x2} {y1} 0, {x2} {y2} 0, {x1} {y2} 0, {x1} {y1} 0))'
                
                # Get view center as point
                view_center_wkt = f'POINT Z ({view_center.x} {view_center.y} 0)'
                
                cur.execute(f"""
                    INSERT INTO layout_viewports (
                        drawing_id, layout_name, viewport_geometry,
                        view_center, scale_factor
                    )
                    VALUES (NULL, %s, ST_GeomFromText(%s, {self.srid}), ST_GeomFromText(%s, {self.srid}), %s)
                """, (
                    layout.name, geometry_wkt, view_center_wkt, scale
                ))
                
                stats['viewports'] += 1
                
            except Exception as e:
                stats['errors'].append(f"Failed to import viewport: {str(e)}")
        
        cur.close()
    
    def _import_point(self, entity, project_id: str, space: str,
                      conn, stats: Dict, resolver: DXFLookupService):
        """Import POINT entity at project level."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        location = entity.dxf.location
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        linetype = entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer'
        
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None,
            color_aci=color_aci, 
            linetype=linetype
        )
        
        geometry_wkt = f'POINT Z ({location.x} {location.y} {location.z})'
        
        cur.execute(f"""
            INSERT INTO drawing_entities (
                drawing_id, entity_type, layer_id, space_type,
                geometry, color_aci, lineweight, linetype, attributes
            )
            VALUES (NULL, %s, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s)
        """, (
            'POINT', layer_id, space,
            geometry_wkt, 
            entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
            -1, 'ByLayer',
            json.dumps({'layer_name': layer_name, 'dxf_handle': entity.dxf.handle})
        ))
        
        stats['points'] += 1
        cur.close()
    
    def _import_3dface(self, entity, project_id: str, space: str,
                       conn, stats: Dict, resolver: DXFLookupService):
        """Import 3DFACE entity at project level (triangular/quad surface faces for TIN surfaces)."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        linetype = entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer'
        
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None,
            color_aci=color_aci, 
            linetype=linetype
        )
        
        vtx0 = entity.dxf.vtx0
        vtx1 = entity.dxf.vtx1
        vtx2 = entity.dxf.vtx2
        vtx3 = entity.dxf.vtx3 if hasattr(entity.dxf, 'vtx3') else vtx2
        
        # COORDINATE TRACKING: Log what we read from ezdxf
        print(f"[IMPORT] 3DFACE read from ezdxf:")
        print(f"[IMPORT]   vtx0: ({vtx0.x}, {vtx0.y}, {vtx0.z})")
        print(f"[IMPORT]   vtx1: ({vtx1.x}, {vtx1.y}, {vtx1.z})")
        print(f"[IMPORT]   vtx2: ({vtx2.x}, {vtx2.y}, {vtx2.z})")
        print(f"[IMPORT]   vtx3: ({vtx3.x}, {vtx3.y}, {vtx3.z})")
        
        points = [
            f'{vtx0.x} {vtx0.y} {vtx0.z}',
            f'{vtx1.x} {vtx1.y} {vtx1.z}',
            f'{vtx2.x} {vtx2.y} {vtx2.z}',
            f'{vtx3.x} {vtx3.y} {vtx3.z}',
            f'{vtx0.x} {vtx0.y} {vtx0.z}'
        ]
        
        geometry_wkt = f'POLYGON Z (({", ".join(points)}))'
        print(f"[IMPORT] WKT to DB: {geometry_wkt}")
        
        cur.execute(f"""
            INSERT INTO drawing_entities (
                drawing_id, entity_type, layer_id, space_type,
                geometry, color_aci, lineweight, linetype, attributes
            )
            VALUES (NULL, %s, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s)
        """, (
            '3DFACE', layer_id, space,
            geometry_wkt,
            entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
            -1, 'ByLayer',
            json.dumps({'layer_name': layer_name, 'dxf_handle': entity.dxf.handle})
        ))
        
        stats['3dfaces'] += 1
        cur.close()
    
    def _import_3dsolid(self, entity, project_id: str, space: str,
                        conn, stats: Dict, resolver: DXFLookupService):
        """Import 3DSOLID entity at project level (store as bounding box or centerpoint for now)."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        linetype = entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer'
        
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None,
            color_aci=color_aci, 
            linetype=linetype
        )
        
        try:
            if hasattr(entity, 'get_attribs_and_values'):
                attribs = entity.get_attribs_and_values()
                metadata = {'layer_name': layer_name, 'dxf_handle': entity.dxf.handle, 'attribs': dict(attribs)}
            else:
                metadata = {'layer_name': layer_name, 'dxf_handle': entity.dxf.handle}
            
            geometry_wkt = 'POINT Z (0 0 0)'
            
            cur.execute(f"""
                INSERT INTO drawing_entities (
                    drawing_id, entity_type, layer_id, space_type,
                    geometry, color_aci, lineweight, linetype, attributes
                )
                VALUES (NULL, %s, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s)
            """, (
                '3DSOLID', layer_id, space,
                geometry_wkt,
                entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
                -1, 'ByLayer',
                json.dumps(metadata)
            ))
            
            stats['solids'] += 1
        except Exception as e:
            stats['errors'].append(f"Failed to import 3DSOLID: {str(e)}")
        
        cur.close()
    
    def _import_mesh(self, entity, project_id: str, space: str,
                     conn, stats: Dict, resolver: DXFLookupService):
        """Import MESH/POLYMESH entity at project level (store vertices as multipoint or approximation)."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        linetype = entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer'
        
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None,
            color_aci=color_aci, 
            linetype=linetype
        )
        
        try:
            points = []
            if hasattr(entity, 'vertices'):
                for vertex in entity.vertices:
                    if hasattr(vertex, 'dxf') and hasattr(vertex.dxf, 'location'):
                        loc = vertex.dxf.location
                        points.append(f'{loc.x} {loc.y} {loc.z}')
            
            if points:
                geometry_wkt = f'MULTIPOINT Z ({", ".join(points)})'
            else:
                geometry_wkt = 'POINT Z (0 0 0)'
            
            cur.execute(f"""
                INSERT INTO drawing_entities (
                    drawing_id, entity_type, layer_id, space_type,
                    geometry, color_aci, lineweight, linetype, attributes
                )
                VALUES (NULL, %s, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s)
            """, (
                'MESH', layer_id, space,
                geometry_wkt,
                entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
                -1, 'ByLayer',
                json.dumps({'layer_name': layer_name, 'dxf_handle': entity.dxf.handle})
            ))
            
            stats['meshes'] += 1
        except Exception as e:
            stats['errors'].append(f"Failed to import MESH: {str(e)}")
        
        cur.close()
    
    def _import_leader(self, entity, project_id: str, space: str,
                       conn, stats: Dict, resolver: DXFLookupService):
        """Import LEADER/MULTILEADER entity at project level."""
        cur = conn.cursor()
        
        layer_name = entity.dxf.layer
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        linetype = entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer'
        
        layer_id, _ = resolver.get_or_create_layer(
            layer_name, 
            project_id=project_id, 
            drawing_id=None,
            color_aci=color_aci, 
            linetype=linetype
        )
        
        try:
            points = []
            if hasattr(entity, 'vertices'):
                for vertex in entity.vertices:
                    if len(vertex) >= 2:
                        if len(vertex) == 2:
                            points.append(f'{vertex[0]} {vertex[1]} 0')
                        else:
                            points.append(f'{vertex[0]} {vertex[1]} {vertex[2]}')
            
            if points and len(points) >= 2:
                geometry_wkt = f'LINESTRING Z ({", ".join(points)})'
            else:
                geometry_wkt = 'LINESTRING Z (0 0 0, 1 1 0)'
            
            cur.execute(f"""
                INSERT INTO drawing_entities (
                    drawing_id, entity_type, layer_id, space_type,
                    geometry, color_aci, lineweight, linetype, attributes
                )
                VALUES (NULL, %s, %s, %s, ST_GeomFromText(%s, {self.srid}), %s, %s, %s, %s)
            """, (
                'LEADER', layer_id, space,
                geometry_wkt,
                entity.dxf.color if hasattr(entity.dxf, 'color') else 256,
                -1, 'ByLayer',
                json.dumps({'layer_name': layer_name, 'dxf_handle': entity.dxf.handle})
            ))
            
            stats['leaders'] += 1
        except Exception as e:
            stats['errors'].append(f"Failed to import LEADER: {str(e)}")
        
        cur.close()
