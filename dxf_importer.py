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


class DXFImporter:
    """Import DXF files and store entities in PostgreSQL database."""
    
    def __init__(self, db_config: Dict):
        """Initialize importer with database configuration."""
        self.db_config = db_config
    
    def import_dxf(self, file_path: str, drawing_id: int, 
                   coordinate_system: str = 'LOCAL', 
                   import_modelspace: bool = True,
                   import_paperspace: bool = True) -> Dict:
        """
        Import a DXF file into the database.
        
        Args:
            file_path: Path to DXF file
            drawing_id: ID of the drawing to associate entities with
            coordinate_system: Coordinate system ('LOCAL', 'WGS84', etc.)
            import_modelspace: Whether to import model space entities
            import_paperspace: Whether to import paper space entities
            
        Returns:
            Dictionary with import statistics
        """
        stats = {
            'entities': 0,
            'text': 0,
            'dimensions': 0,
            'hatches': 0,
            'blocks': 0,
            'viewports': 0,
            'layers': set(),
            'linetypes': set(),
            'errors': []
        }
        
        try:
            # Read DXF file
            doc = ezdxf.readfile(file_path)
            
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False
            
            try:
                # Import layers
                self._import_layers(doc, drawing_id, conn, stats)
                
                # Import linetypes
                self._import_linetypes(doc, drawing_id, conn, stats)
                
                # Import model space
                if import_modelspace:
                    modelspace = doc.modelspace()
                    self._import_entities(modelspace, drawing_id, 'MODEL', conn, stats)
                
                # Import paper space layouts
                if import_paperspace:
                    for layout_name in doc.layout_names():
                        if layout_name != 'Model':
                            layout = doc.layout(layout_name)
                            self._import_entities(layout, drawing_id, 'PAPER', conn, stats)
                            self._import_viewports(layout, drawing_id, conn, stats)
                
                conn.commit()
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            stats['errors'].append(f"Import failed: {str(e)}")
        
        # Convert sets to counts for JSON serialization
        stats['layers'] = len(stats['layers'])
        stats['linetypes'] = len(stats['linetypes'])
        
        return stats
    
    def _import_layers(self, doc: ezdxf.document.Drawing, drawing_id: int, 
                       conn, stats: Dict):
        """Import layers and track usage."""
        cur = conn.cursor()
        
        for layer in doc.layers:
            layer_name = layer.dxf.name
            stats['layers'].add(layer_name)
            
            # For now, skip recording layer usage - table structure requires layer_id lookups
            # This would need to match layer names to layer_standards and get layer_id
            # TODO: Implement layer usage tracking with proper FK lookups
        
        cur.close()
    
    def _import_linetypes(self, doc: ezdxf.document.Drawing, drawing_id: int,
                          conn, stats: Dict):
        """Import linetypes and track usage."""
        cur = conn.cursor()
        
        for linetype in doc.linetypes:
            linetype_name = linetype.dxf.name
            stats['linetypes'].add(linetype_name)
            
            # Try to record linetype usage if the linetype exists
            try:
                cur.execute("""
                    INSERT INTO drawing_linetype_usage (drawing_id, linetype_name)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (drawing_id, linetype_name))
            except:
                # Skip if error - usage tracking is optional
                pass
        
        cur.close()
    
    def _import_entities(self, layout, drawing_id: int, space: str, 
                         conn, stats: Dict):
        """Import entities from a layout."""
        for entity in layout:
            entity_type = entity.dxftype()
            
            try:
                if entity_type in ['LINE', 'POLYLINE', 'LWPOLYLINE', 'ARC', 
                                   'CIRCLE', 'ELLIPSE', 'SPLINE']:
                    self._import_entity(entity, drawing_id, space, conn, stats)
                
                elif entity_type in ['TEXT', 'MTEXT']:
                    self._import_text(entity, drawing_id, space, conn, stats)
                
                elif entity_type.startswith('DIMENSION'):
                    self._import_dimension(entity, drawing_id, space, conn, stats)
                
                elif entity_type == 'HATCH':
                    self._import_hatch(entity, drawing_id, space, conn, stats)
                
                elif entity_type == 'INSERT':
                    self._import_block_insert(entity, drawing_id, space, conn, stats)
                    
            except Exception as e:
                stats['errors'].append(
                    f"Failed to import {entity_type}: {str(e)}"
                )
    
    def _import_entity(self, entity, drawing_id: int, space: str, 
                       conn, stats: Dict):
        """Import generic drawing entity (line, arc, circle, etc.)."""
        cur = conn.cursor()
        
        entity_type = entity.dxftype()
        layer = entity.dxf.layer
        color_aci = entity.dxf.color if hasattr(entity.dxf, 'color') else 256
        lineweight = entity.dxf.lineweight if hasattr(entity.dxf, 'lineweight') else -1
        
        # Convert entity to WKT geometry
        geometry_wkt = self._entity_to_wkt(entity)
        
        if geometry_wkt:
            # Store DXF-specific properties in metadata
            metadata = {
                'linetype': entity.dxf.linetype if hasattr(entity.dxf, 'linetype') else 'ByLayer',
            }
            
            cur.execute("""
                INSERT INTO drawing_entities (
                    drawing_id, entity_type, layer_name, space_type,
                    geometry, color_aci, lineweight, metadata
                )
                VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 0), %s, %s, %s)
            """, (
                drawing_id, entity_type, layer, space,
                geometry_wkt, color_aci, lineweight, json.dumps(metadata)
            ))
            
            stats['entities'] += 1
        
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
                import math
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
            
            elif entity_type in ['POLYLINE', 'LWPOLYLINE']:
                points = []
                for point in entity.get_points():
                    if len(point) == 2:
                        points.append(f'{point[0]} {point[1]} 0')
                    else:
                        points.append(f'{point[0]} {point[1]} {point[2]}')
                
                if len(points) > 0:
                    return f'LINESTRING Z ({", ".join(points)})'
            
            elif entity_type == 'ELLIPSE':
                # Approximate ellipse with points
                center = entity.dxf.center
                major_axis = entity.dxf.major_axis
                ratio = entity.dxf.ratio
                
                points = []
                import math
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
    
    def _import_text(self, entity, drawing_id: int, space: str, 
                     conn, stats: Dict):
        """Import text entity."""
        cur = conn.cursor()
        
        entity_type = entity.dxftype()
        layer = entity.dxf.layer
        
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
            justification = f'{halign},{valign}'
        else:
            attachment_point = entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 1
            justification = str(attachment_point)
        
        # Create point geometry
        geometry_wkt = f'POINT Z ({insert_point.x} {insert_point.y} {insert_point.z})'
        
        cur.execute("""
            INSERT INTO drawing_text (
                drawing_id, layer_name, space_type, text_content,
                insertion_point, text_height, rotation_angle,
                text_style, justification
            )
            VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 0), %s, %s, %s, %s)
        """, (
            drawing_id, layer, space, text_content,
            geometry_wkt, height, rotation, style_name, justification
        ))
        
        stats['text'] += 1
        cur.close()
    
    def _import_dimension(self, entity, drawing_id: int, space: str,
                          conn, stats: Dict):
        """Import dimension entity."""
        cur = conn.cursor()
        
        layer = entity.dxf.layer
        dim_type = entity.dxftype()
        
        # Get dimension points
        defpoint = entity.dxf.defpoint
        defpoint2 = entity.dxf.defpoint2 if hasattr(entity.dxf, 'defpoint2') else defpoint
        
        # Create line geometry from dimension points
        geometry_wkt = f'LINESTRING Z ({defpoint.x} {defpoint.y} {defpoint.z}, {defpoint2.x} {defpoint2.y} {defpoint2.z})'
        
        # Get measurement
        measurement = entity.dxf.text if hasattr(entity.dxf, 'text') else ''
        
        # Get dimension style
        dimstyle = entity.dxf.dimstyle if hasattr(entity.dxf, 'dimstyle') else 'Standard'
        
        cur.execute("""
            INSERT INTO drawing_dimensions (
                drawing_id, layer_name, space_type, dimension_type,
                geometry, measurement_override, dimension_style
            )
            VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 0), %s, %s)
        """, (
            drawing_id, layer, space, dim_type,
            geometry_wkt, measurement, dimstyle
        ))
        
        stats['dimensions'] += 1
        cur.close()
    
    def _import_hatch(self, entity, drawing_id: int, space: str,
                      conn, stats: Dict):
        """Import hatch entity."""
        cur = conn.cursor()
        
        layer = entity.dxf.layer
        pattern_name = entity.dxf.pattern_name
        
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
                
                cur.execute("""
                    INSERT INTO drawing_hatches (
                        drawing_id, layer_name, space_type, pattern_name,
                        boundary_geometry, pattern_scale, pattern_angle
                    )
                    VALUES (%s, %s, %s, %s, ST_GeomFromText(%s, 0), %s, %s)
                """, (
                    drawing_id, layer, space, pattern_name,
                    geometry_wkt, scale, angle
                ))
                
                stats['hatches'] += 1
                
        except Exception as e:
            stats['errors'].append(f"Failed to import hatch: {str(e)}")
        
        cur.close()
    
    def _import_block_insert(self, entity, drawing_id: int, space: str,
                             conn, stats: Dict):
        """Import block insert (existing block_inserts table)."""
        cur = conn.cursor()
        
        block_name = entity.dxf.name
        insert_point = entity.dxf.insert
        
        # Get transformation
        scale_x = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1.0
        scale_y = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1.0
        scale_z = entity.dxf.zscale if hasattr(entity.dxf, 'zscale') else 1.0
        rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0
        
        # Create point geometry
        geometry_wkt = f'POINT Z ({insert_point.x} {insert_point.y} {insert_point.z})'
        
        try:
            cur.execute("""
                INSERT INTO block_inserts (
                    drawing_id, block_name, insertion_point,
                    scale_x, scale_y, scale_z, rotation
                )
                VALUES (%s, %s, ST_GeomFromText(%s, 0), %s, %s, %s, %s)
            """, (
                drawing_id, block_name, geometry_wkt,
                scale_x, scale_y, scale_z, rotation
            ))
            
            stats['blocks'] += 1
        except Exception as e:
            stats['errors'].append(f"Failed to import block insert: {str(e)}")
        
        cur.close()
    
    def _import_viewports(self, layout, drawing_id: int, conn, stats: Dict):
        """Import paper space viewports."""
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
                
                cur.execute("""
                    INSERT INTO layout_viewports (
                        drawing_id, layout_name, viewport_geometry,
                        view_center, scale_factor
                    )
                    VALUES (%s, %s, ST_GeomFromText(%s, 0), ST_GeomFromText(%s, 0), %s)
                """, (
                    drawing_id, layout.name, geometry_wkt, view_center_wkt, scale
                ))
                
                stats['viewports'] += 1
                
            except Exception as e:
                stats['errors'].append(f"Failed to import viewport: {str(e)}")
        
        cur.close()
