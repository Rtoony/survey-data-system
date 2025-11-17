"""
DXF Exporter Module
Reads entities from database and generates DXF files.
Uses database-driven CAD standards for layer naming.

PHASE 2 REFACTORING - PROJECT-LEVEL EXPORTS:
- export_dxf() now accepts project_id instead of drawing_id
- Queries ALL entities in a project (regardless of drawing_id)
- Generates layer names dynamically from entity attributes using ExportLayerGenerator
- Supports entities with drawing_id IS NULL (new project-level imports)
- Preserves all geometry generation and DXF structure
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from typing import Dict, List, Optional
import os
import sys

# Import standards-based layer generator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from standards.export_layer_generator import ExportLayerGenerator
    STANDARDS_AVAILABLE = True
except ImportError:
    STANDARDS_AVAILABLE = False
    print("Warning: ExportLayerGenerator not available, using legacy layer naming")


class DXFExporter:
    """Export database entities to DXF files using database-driven standards."""
    
    def __init__(self, db_config: Dict, use_standards: bool = True):
        """
        Initialize exporter with database configuration.
        
        Args:
            db_config: Database connection parameters
            use_standards: Use database-driven layer naming (default: True)
        """
        self.db_config = db_config
        self.use_standards = use_standards and STANDARDS_AVAILABLE
        
        # Initialize layer generator if standards are enabled
        if self.use_standards:
            try:
                self.layer_generator = ExportLayerGenerator()
            except Exception as e:
                print(f"Warning: Could not initialize ExportLayerGenerator: {e}")
                self.use_standards = False
                self.layer_generator = None
        else:
            self.layer_generator = None
    
    def export_dxf(self, project_id: str, output_path: str,
                   dxf_version: str = 'AC1027',
                   include_modelspace: bool = True,
                   layer_filter: Optional[List[str]] = None,
                   external_conn=None) -> Dict:
        """
        Export a project to DXF file.

        Args:
            project_id: ID of the project to export
            output_path: Path to save DXF file
            dxf_version: DXF version (AC1027 = AutoCAD 2013)
            include_modelspace: Whether to export model space entities
            layer_filter: Optional list of layer names to include
            external_conn: Optional external database connection (will not be closed)

        Returns:
            Dictionary with export statistics
        """
        stats = {
            'entities': 0,
            'text': 0,
            'dimensions': 0,
            'hatches': 0,
            'blocks': 0,
            'viewports': 0,
            'layers': set(),
            'errors': []
        }
        
        # Use external connection or create new one
        owns_connection = external_conn is None
        conn = external_conn if external_conn else psycopg2.connect(**self.db_config)
        
        try:
            # Create new DXF document
            doc = ezdxf.new(dxf_version)
            
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            try:
                # Setup linetypes
                self._setup_linetypes(project_id, doc, cur, stats)
                
                # Export model space
                if include_modelspace:
                    msp = doc.modelspace()
                    self._export_entities(project_id, 'MODEL', msp, doc, cur, stats, layer_filter)
                    self._export_text(project_id, 'MODEL', msp, doc, cur, stats, layer_filter)
                    self._export_dimensions(project_id, 'MODEL', msp, doc, cur, stats, layer_filter)
                    self._export_hatches(project_id, 'MODEL', msp, doc, cur, stats, layer_filter)
                    self._export_block_inserts(project_id, 'MODEL', msp, doc, cur, stats, layer_filter)

                # Save DXF file
                doc.saveas(output_path)
                
                # Record export job
                self._record_export_job(project_id, output_path, dxf_version,
                                       stats, cur, conn)
                
            finally:
                cur.close()
                # Only close connection if we own it
                if owns_connection:
                    conn.close()
                
        except Exception as e:
            import traceback
            error_msg = f"Export failed: {str(e)}\n{traceback.format_exc()}"
            print(f"DXF EXPORT ERROR: {error_msg}")  # Explicit logging
            stats['errors'].append(error_msg)
            raise  # Re-raise to see in logs
        
        # Convert sets to counts
        stats['layers'] = len(stats['layers'])
        
        return stats
    
    
    def _generate_layer_name(self, object_type: str, properties: Dict, geometry_type: str = 'LINE') -> str:
        """
        Generate layer name using standards system or fall back to legacy.
        
        Args:
            object_type: Database object type (e.g., 'utility_line')
            properties: Object properties dict
            geometry_type: DXF geometry type
            
        Returns:
            Layer name string
        """
        if self.use_standards and self.layer_generator:
            try:
                layer_name = self.layer_generator.generate_layer_name(
                    object_type,
                    properties,
                    geometry_type
                )
                if layer_name:
                    return layer_name
            except Exception as e:
                print(f"Warning: Layer generation failed, using fallback: {e}")
        
        # Legacy fallback
        return self._generate_legacy_layer_name(object_type, properties, geometry_type)
    
    def _generate_legacy_layer_name(self, object_type: str, properties: Dict, geometry_type: str) -> str:
        """Legacy layer name generation (fallback)"""
        # Simple fallback logic
        utility_type = properties.get('utility_type', 'UTIL')
        diameter = properties.get('diameter', properties.get('diameter_inches'))
        phase = properties.get('phase', 'EXIST')
        
        if diameter:
            return f"{diameter}IN-{utility_type.upper()}"
        return utility_type.upper()
    
    def _ensure_layer(self, layer_name: str, doc: ezdxf.document.Drawing, stats: Dict):
        """Ensure layer exists in DXF document, create if needed."""
        if layer_name not in doc.layers:
            doc.layers.add(layer_name)
            stats['layers'].add(layer_name)
    
    def _parse_rgb(self, rgb_str: str) -> tuple:
        """Parse RGB string like 'rgb(255,0,0)' to tuple."""
        try:
            rgb_str = rgb_str.replace('rgb(', '').replace(')', '')
            r, g, b = map(int, rgb_str.split(','))
            return (r, g, b)
        except:
            return (255, 255, 255)
    
    def _setup_linetypes(self, project_id: str, doc: ezdxf.document.Drawing,
                         cur, stats: Dict):
        """Setup linetypes in DXF document."""
        try:
            cur.execute("""
                SELECT DISTINCT linetype
                FROM drawing_entities
                WHERE project_id = %s::uuid
                AND linetype IS NOT NULL
                AND linetype NOT IN ('ByLayer', 'ByBlock', 'Continuous')
            """, (project_id,))
            
            linetypes = cur.fetchall()
            
            for lt in linetypes:
                linetype_name = lt['linetype']
                try:
                    if linetype_name not in doc.linetypes:
                        doc.linetypes.add(
                            name=linetype_name,
                            pattern=[0.5, 0.25, -0.25],
                            description=linetype_name
                        )
                except:
                    pass
        except Exception:
            pass
    
    def _export_entities(self, project_id: str, space: str, layout, doc,
                         cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export generic entities to DXF layout."""
        query = """
            SELECT de.entity_type,
                   ST_AsText(de.geometry) as geom_wkt,
                   de.color_aci, de.lineweight, de.attributes,
                   l.layer_name,
                   l.discipline,
                   se.entity_type as standards_entity_type
            FROM drawing_entities de
            LEFT JOIN layers l ON de.layer_id = l.layer_id
            LEFT JOIN standards_entities se ON de.standards_entity_id = se.entity_id
            WHERE de.project_id = %s::uuid
        """

        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (project_id, layer_filter))
        else:
            cur.execute(query, (project_id,))
        
        entities = cur.fetchall()
        
        for entity in entities:
            try:
                layer_name = self._determine_layer_name(entity, doc, stats)
                entity_with_layer = dict(entity)
                entity_with_layer['layer_name'] = layer_name
                self._create_entity(entity_with_layer, layout)
                stats['entities'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export {entity['entity_type']}: {str(e)}")
    
    def _create_entity(self, entity: Dict, layout):
        """Create DXF entity from database record with full 3D support."""
        entity_type = entity['entity_type']
        layer = entity['layer_name']
        geom_wkt = entity['geom_wkt']
        
        # Parse WKT to coordinates (includes Z values)
        coords = self._parse_wkt_coords(geom_wkt)
        
        # COORDINATE TRACKING: Log 3DFACE coordinates at export
        if entity_type == '3DFACE':
            print(f"[EXPORT] 3DFACE WKT from DB: {geom_wkt}")
            print(f"[EXPORT] Parsed coords (len={len(coords)}): {coords}")
        
        if entity_type == 'LINE' and len(coords) >= 2:
            # Lines support 3D coordinates directly
            layout.add_line(
                start=coords[0],
                end=coords[1],
                dxfattribs={'layer': layer}
            )
        
        elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
            # Use true 3D polyline to preserve Z values
            # If coordinates have Z dimension (from GeometryZ), always preserve it
            # even if Z values are all zero (e.g., flat pad at elevation 0)
            is_3d = len(coords) > 0 and len(coords[0]) > 2
            
            if is_3d:
                # Create 3D polyline to preserve GeometryZ data
                layout.add_polyline3d(
                    points=coords,
                    dxfattribs={'layer': layer}
                )
            else:
                # Use lightweight polyline only for true 2D data (no Z coordinate)
                layout.add_lwpolyline(
                    points=[(c[0], c[1]) for c in coords],
                    dxfattribs={'layer': layer}
                )
        
        elif entity_type == 'CIRCLE' and len(coords) > 10:
            # Calculate center and radius from approximated circle points
            center = coords[0]
            radius = ((coords[8][0] - center[0])**2 + (coords[8][1] - center[1])**2)**0.5
            
            # Preserve elevation using the elevation attribute
            circle = layout.add_circle(
                center=(center[0], center[1]),
                radius=radius,
                dxfattribs={'layer': layer}
            )
            # Set elevation for 3D positioning (preserve even if Z=0)
            if len(center) > 2:
                circle.dxf.elevation = center[2]
        
        elif entity_type == 'ARC' and len(coords) > 2:
            # Approximate arc from points
            center = coords[len(coords)//2]
            radius = ((coords[0][0] - center[0])**2 + (coords[0][1] - center[1])**2)**0.5
            
            # Create arc and preserve elevation
            arc = layout.add_arc(
                center=(center[0], center[1]),
                radius=radius,
                start_angle=0,
                end_angle=180,
                dxfattribs={'layer': layer}
            )
            # Set elevation for 3D positioning (preserve even if Z=0)
            if len(center) > 2:
                arc.dxf.elevation = center[2]
        
        elif entity_type == '3DFACE' and len(coords) >= 3:
            # Export 3D faces with full vertex elevations
            # Civil 3D exports triangular faces as POLYGON Z: [v0,v1,v2,v2,v0] (duplicate v2 + closing v0)
            # Quadrilateral faces as POLYGON Z: [v0,v1,v2,v3,v0] (just closing v0)
            
            # Remove closing point if present (first == last)
            if len(coords) >= 4:
                first, last = coords[0], coords[-1]
                is_closed = (abs(first[0] - last[0]) < 1e-9 and 
                            abs(first[1] - last[1]) < 1e-9 and 
                            abs(first[2] - last[2]) < 1e-9)
                if is_closed:
                    print(f"[EXPORT] Removing closing point (first==last)")
                    coords = coords[:-1]  # Drop closing point
            
            # Remove duplicate vertices (Civil 3D duplicates last vertex for triangles)
            # Check if we have 4 vertices but v3 == v2 (triangle stored as quad)
            if len(coords) == 4:
                v2, v3 = coords[2], coords[3]
                is_duplicate = (abs(v2[0] - v3[0]) < 1e-9 and 
                               abs(v2[1] - v3[1]) < 1e-9 and 
                               abs(v2[2] - v3[2]) < 1e-9)
                if is_duplicate:
                    print(f"[EXPORT] Removing duplicate v2==v3 (triangle)")
                    coords = coords[:3]  # Remove duplicate, now a true triangle
            
            # Ensure we have exactly 4 points for DXF 3DFACE (duplicate last if triangle)
            if len(coords) == 3:
                points = coords + [coords[-1]]  # Triangle -> Quad by duplicating last vertex
                print(f"[EXPORT] Triangle: duplicating last vertex")
            else:
                points = coords[:4]  # True quad, take first 4
                print(f"[EXPORT] Quad: using first 4 vertices")
            
            print(f"[EXPORT] Final points to ezdxf: {points}")
            layout.add_3dface(
                points=points,
                dxfattribs={'layer': layer}
            )
        
        elif entity_type == 'POINT' and len(coords) >= 1:
            # Points support 3D coordinates
            layout.add_point(
                location=coords[0],
                dxfattribs={'layer': layer}
            )
    
    def _parse_wkt_coords(self, wkt: str) -> List[tuple]:
        """Parse WKT geometry to coordinate tuples with Z values."""
        try:
            # Remove geometry type prefix
            wkt = wkt.split('(', 1)[1].rsplit(')', 1)[0]
            
            # Handle nested parentheses (polygons)
            if wkt.startswith('('):
                wkt = wkt[1:-1]
            
            # Parse coordinates
            coords = []
            for point_str in wkt.split(','):
                parts = point_str.strip().split()
                if len(parts) >= 2:
                    x, y = float(parts[0]), float(parts[1])
                    z = float(parts[2]) if len(parts) > 2 else 0.0
                    coords.append((x, y, z))
            
            return coords
        except Exception as e:
            print(f"Error parsing WKT: {e}")
            return []
    
    def _has_elevation_data(self, coords: List[tuple]) -> bool:
        """
        Check if coordinate list has 3D (Z) dimension.
        Returns True if coordinates have Z values, regardless of magnitude.
        Even Z=0 is valid elevation data that must be preserved.
        """
        if not coords:
            return False
        # Check if coordinates are 3D (have Z component)
        return len(coords[0]) > 2 if coords else False
    
    def _extract_z_from_metadata(self, metadata: Dict, key: str = 'elevation') -> Optional[float]:
        """
        Extract elevation from entity metadata.
        Useful for cases where processing tools calculated elevation but it's not in geometry.
        
        Args:
            metadata: Entity metadata dictionary
            key: Key to look for elevation data (default: 'elevation')
        
        Returns:
            Float elevation value or None if not found
        """
        if not metadata:
            return None
        
        # Try common elevation keys
        elevation_keys = [key, 'z', 'invert_elevation', 'rim_elevation', 'top_elevation', 'bottom_elevation']
        
        for k in elevation_keys:
            if k in metadata and metadata[k] is not None:
                try:
                    return float(metadata[k])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _enrich_coords_with_metadata_z(self, coords: List[tuple], metadata: Dict) -> List[tuple]:
        """
        Enrich 2D coordinates with Z values from metadata if available.
        Used when processing tools have calculated elevations that aren't yet in geometry.
        
        Args:
            coords: List of coordinate tuples (may be 2D or 3D)
            metadata: Entity metadata that may contain elevation info
        
        Returns:
            List of 3D coordinate tuples
        """
        if self._has_elevation_data(coords):
            # Already has elevation data, return as-is
            return coords
        
        # Try to get elevation from metadata
        z_value = self._extract_z_from_metadata(metadata)
        
        if z_value is not None:
            # Apply metadata elevation to all coordinates
            return [(c[0], c[1], z_value) for c in coords]
        
        # No elevation data available, ensure 3D tuples with Z=0
        return [(c[0], c[1], c[2] if len(c) > 2 else 0.0) for c in coords]
    
    def _determine_layer_name(self, entity: Dict, doc: ezdxf.document.Drawing, stats: Dict) -> str:
        """Determine layer name for entity from attributes or generate from standards."""
        if entity.get('layer_name'):
            layer_name = entity['layer_name']
            self._ensure_layer(layer_name, doc, stats)
            return layer_name
        
        properties = {}
        attributes = entity.get('attributes') or {}
        
        if entity.get('category'):
            properties['category'] = entity['category']
        if entity.get('object_type'):
            properties['object_type'] = entity['object_type']
        if entity.get('phase'):
            properties['phase'] = entity['phase']
        
        if attributes:
            if isinstance(attributes, str):
                import json
                try:
                    attributes = json.loads(attributes)
                except:
                    attributes = {}
            properties.update(attributes)
        
        entity_type = entity.get('entity_type', 'unknown')
        geometry_type = entity_type.upper()
        
        layer_name = self._generate_layer_name(entity_type.lower(), properties, geometry_type)
        self._ensure_layer(layer_name, doc, stats)
        return layer_name
    
    def _export_text(self, project_id: str, space: str, layout, doc,
                     cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export text entities to DXF layout."""
        query = """
            SELECT dt.text_content,
                   ST_AsText(dt.insertion_point) as insert_wkt,
                   dt.text_height, dt.rotation_angle, dt.text_style,
                   dt.horizontal_justification, dt.vertical_justification,
                   l.layer_name,
                   l.discipline
            FROM drawing_text dt
            JOIN drawing_entities de ON dt.entity_id = de.entity_id
            LEFT JOIN layers l ON dt.layer_id = l.layer_id
            WHERE de.project_id = %s::uuid
        """

        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (project_id, layer_filter))
        else:
            cur.execute(query, (project_id,))
        
        texts = cur.fetchall()
        
        for text in texts:
            try:
                layer_name = self._determine_layer_name(text, doc, stats)
                coords = self._parse_wkt_coords(text['insert_wkt'])
                if coords:
                    layout.add_text(
                        text=text['text_content'],
                        dxfattribs={
                            'layer': layer_name,
                            'insert': coords[0],
                            'height': text['text_height'],
                            'rotation': text['rotation_angle'],
                            'style': text['text_style']
                        }
                    )
                    stats['text'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export text: {str(e)}")
    
    def _export_dimensions(self, project_id: str, space: str, layout, doc,
                           cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export dimension entities to DXF layout."""
        query = """
            SELECT dd.dimension_type,
                   ST_AsText(de.geometry) as geom_wkt,
                   dd.dimension_text, dd.dimension_style,
                   l.layer_name,
                   l.discipline
            FROM drawing_dimensions dd
            JOIN drawing_entities de ON dd.entity_id = de.entity_id
            LEFT JOIN layers l ON dd.layer_id = l.layer_id
            WHERE de.project_id = %s::uuid
        """

        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (project_id, layer_filter))
        else:
            cur.execute(query, (project_id,))
        
        dimensions = cur.fetchall()
        
        for dim in dimensions:
            try:
                if not dim['geom_wkt']:
                    continue
                layer_name = self._determine_layer_name(dim, doc, stats)
                coords = self._parse_wkt_coords(dim['geom_wkt'])
                if len(coords) >= 2:
                    layout.add_linear_dim(
                        base=coords[0],
                        p1=coords[0],
                        p2=coords[1],
                        dimstyle=dim['dimension_style'] or 'Standard',
                        override={'dimtxt': dim['dimension_text']} if dim['dimension_text'] else None,
                        dxfattribs={'layer': layer_name}
                    )
                    stats['dimensions'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export dimension: {str(e)}")
    
    def _export_hatches(self, project_id: str, space: str, layout, doc,
                        cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export hatch entities to DXF layout."""
        query = """
            SELECT dh.hatch_pattern,
                   ST_AsText(dh.boundary_geometry) as boundary_wkt,
                   dh.hatch_scale, dh.hatch_angle,
                   l.layer_name,
                   l.discipline
            FROM drawing_hatches dh
            JOIN drawing_entities de ON dh.entity_id = de.entity_id
            LEFT JOIN layers l ON dh.layer_id = l.layer_id
            WHERE de.project_id = %s::uuid
        """

        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (project_id, layer_filter))
        else:
            cur.execute(query, (project_id,))
        
        hatches = cur.fetchall()
        
        for hatch in hatches:
            try:
                layer_name = self._determine_layer_name(hatch, doc, stats)
                coords = self._parse_wkt_coords(hatch['boundary_wkt'])
                if len(coords) >= 3:
                    h = layout.add_hatch(dxfattribs={'layer': layer_name})
                    h.paths.add_polyline_path(coords[:-1])
                    h.set_pattern_fill(
                        hatch['hatch_pattern'],
                        scale=hatch['hatch_scale'],
                        angle=hatch['hatch_angle']
                    )
                    stats['hatches'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export hatch: {str(e)}")
    
    def _export_block_inserts(self, project_id: str, space: str, layout, doc,
                              cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export block inserts to DXF layout."""
        try:
            query = """
                SELECT bi.insert_x, bi.insert_y, bi.insert_z,
                       bi.scale_x, bi.scale_y, bi.rotation,
                       l.layer_name,
                       l.discipline
                FROM block_inserts bi
                JOIN drawing_entities de ON bi.entity_id = de.entity_id
                LEFT JOIN layers l ON bi.layer_id = l.layer_id
                WHERE de.project_id = %s::uuid
                LIMIT 0
            """

            cur.execute(query, (project_id,))
            
        except Exception:
            pass
    
    def _record_export_job(self, project_id: str, output_path: str,
                           dxf_version: str, stats: Dict, cur, conn):
        """Record export job in database."""
        try:
            conn.rollback()
            
            layers_count = len(stats['layers']) if isinstance(stats['layers'], set) else stats['layers']
            
            metrics = {
                'entities': stats['entities'],
                'text': stats['text'],
                'dimensions': stats['dimensions'],
                'hatches': stats['hatches'],
                'blocks': stats['blocks'],
                'viewports': stats['viewports'],
                'layers': layers_count
            }
            
            status = 'completed' if not stats['errors'] else 'failed'
            error_message = '\n'.join(stats['errors']) if stats['errors'] else None
            
            cur.execute("""
                INSERT INTO export_jobs (
                    project_id, export_format, dxf_version, status,
                    output_file_path, entities_exported, text_exported,
                    dimensions_exported, hatches_exported, error_message, completed_at
                )
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id, 'DXF', dxf_version, status,
                output_path, metrics['entities'], metrics['text'],
                metrics['dimensions'], metrics['hatches'], error_message, datetime.now()
            ))
            
            conn.commit()
            
        except Exception:
            conn.rollback()
            pass
    
    def export_intelligent_objects_to_dxf(self, project_id: str, output_path: str,
                                          include_types: Optional[List[str]] = None) -> Dict:
        """
        Export a project's intelligent civil engineering objects to DXF file.
        Generates layer names from object properties (reverse of layer classification).
        
        Args:
            project_id: UUID of the project to export
            output_path: Path where DXF file should be saved
            include_types: Optional list of object types to include 
                          (e.g., ['utility_line', 'bmp', 'surface_model'])
                          If None, exports all types
            
        Returns:
            Dictionary with export statistics
        """
        stats = {
            'utility_lines': 0,
            'utility_structures': 0,
            'bmps': 0,
            'surface_models': 0,
            'alignments': 0,
            'survey_points': 0,
            'site_trees': 0,
            'total_entities': 0,
            'errors': []
        }
        
        try:
            # Create new DXF document
            doc = ezdxf.new('R2018')
            msp = doc.modelspace()
            
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            
            try:
                # Export each object type
                if not include_types or 'utility_line' in include_types:
                    stats['utility_lines'] = self._export_intelligent_utility_lines(
                        conn, project_id, doc, msp
                    )
                
                if not include_types or 'utility_structure' in include_types:
                    stats['utility_structures'] = self._export_intelligent_utility_structures(
                        conn, project_id, doc, msp
                    )
                
                if not include_types or 'bmp' in include_types:
                    stats['bmps'] = self._export_intelligent_bmps(
                        conn, project_id, doc, msp
                    )
                
                if not include_types or 'surface_model' in include_types:
                    stats['surface_models'] = self._export_intelligent_surface_models(
                        conn, project_id, doc, msp
                    )
                
                if not include_types or 'alignment' in include_types:
                    stats['alignments'] = self._export_intelligent_alignments(
                        conn, project_id, doc, msp
                    )
                
                if not include_types or 'survey_point' in include_types:
                    stats['survey_points'] = self._export_intelligent_survey_points(
                        conn, project_id, doc, msp
                    )
                
                if not include_types or 'site_tree' in include_types:
                    stats['site_trees'] = self._export_intelligent_site_trees(
                        conn, project_id, doc, msp
                    )
                
                # Calculate total
                stats['total_entities'] = sum([
                    stats['utility_lines'],
                    stats['utility_structures'],
                    stats['bmps'],
                    stats['surface_models'],
                    stats['alignments'],
                    stats['survey_points'],
                    stats['site_trees']
                ])
                
                # Save DXF file
                doc.saveas(output_path)
                
            finally:
                conn.close()
                
        except Exception as e:
            stats['errors'].append(f"Export failed: {str(e)}")
        
        return stats
    
    def _export_intelligent_utility_lines(self, conn, project_id: str, doc, msp) -> int:
        """Export utility lines using database-driven CAD standards."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                utility_line_id,
                utility_type,
                diameter_mm,
                material,
                phase,
                ST_AsText(line_geometry) as geometry_wkt
            FROM utility_lines
            WHERE project_id = %s AND line_geometry IS NOT NULL
        """, (project_id,))
        
        lines = cur.fetchall()
        cur.close()
        
        count = 0
        for line in lines:
            try:
                # Build properties dict for layer generation
                diameter_mm = line.get('diameter_mm')
                diameter_in = round(diameter_mm / 25.4) if diameter_mm else None
                
                properties = {
                    'utility_type': line.get('utility_type', 'unknown'),
                    'diameter': diameter_in,
                    'diameter_inches': diameter_in,
                    'material': line.get('material'),
                    'phase': line.get('phase', 'existing')
                }
                
                # Generate layer name using standards system
                layer_name = self._generate_layer_name('utility_line', properties, 'LINE')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Parse WKT and create 3D polyline to preserve elevations
                coords = self._parse_wkt_coords(line['geometry_wkt'])
                if coords:
                    # Check if coordinates are 3D (preserve Z even if zero)
                    is_3d = len(coords[0]) > 2 if coords else False
                    
                    if is_3d:
                        # Use 3D polyline to preserve pipe invert elevations
                        msp.add_polyline3d(coords, dxfattribs={'layer': layer_name})
                    else:
                        # Use lightweight polyline only for true 2D data
                        msp.add_lwpolyline([(c[0], c[1]) for c in coords], dxfattribs={'layer': layer_name})
                    count += 1
                    
            except Exception as e:
                continue
        
        return count
    
    def _export_intelligent_utility_structures(self, conn, project_id: str, doc, msp) -> int:
        """Export utility structures with layer names like 'MH-STORM'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                structure_id,
                structure_type,
                utility_type,
                ST_X(point_geometry) as x,
                ST_Y(point_geometry) as y,
                ST_Z(point_geometry) as z
            FROM utility_structures
            WHERE project_id = %s AND point_geometry IS NOT NULL
        """, (project_id,))
        
        structures = cur.fetchall()
        cur.close()
        
        count = 0
        for struct in structures:
            try:
                properties = {
                    'structure_type': struct.get('structure_type', 'manhole'),
                    'utility_type': struct.get('utility_type'),
                    'diameter': struct.get('diameter'),
                    'phase': struct.get('phase', 'existing')
                }
                
                # Generate layer name using standards system
                layer_name = self._generate_layer_name('utility_structure', properties, 'POINT')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Create point
                x = struct.get('x', 0)
                y = struct.get('y', 0)
                z = struct.get('z', 0)
                msp.add_point((x, y, z), dxfattribs={'layer': layer_name})
                count += 1
                
            except Exception as e:
                continue
        
        return count
    
    def _export_intelligent_bmps(self, conn, project_id: str, doc, msp) -> int:
        """Export BMPs with layer names like 'BMP-BIORETENTION-500CF'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                bmp_id,
                bmp_type,
                design_volume_cf,
                ST_AsText(location) as location_wkt,
                ST_AsText(boundary) as boundary_wkt,
                ST_GeometryType(location) as location_geom_type,
                ST_GeometryType(boundary) as boundary_geom_type
            FROM bmps
            WHERE project_id = %s AND (location IS NOT NULL OR boundary IS NOT NULL)
        """, (project_id,))
        
        bmps = cur.fetchall()
        cur.close()
        
        count = 0
        for bmp in bmps:
            try:
                # Generate layer name using standards system
                properties = {
                    'bmp_type': bmp.get('bmp_type', 'bioretention'),
                    'design_volume_cf': bmp.get('design_volume_cf'),
                    'phase': bmp.get('phase', 'new')
                }
                
                layer_name = self._generate_layer_name('bmp', properties, 'POLYGON')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Export as polygon or point with elevation support
                if bmp.get('boundary_wkt') and 'POLYGON' in bmp.get('boundary_geom_type', ''):
                    coords = self._parse_wkt_coords(bmp['boundary_wkt'])
                    if coords:
                        is_3d = len(coords[0]) > 2 if coords else False
                        
                        if is_3d:
                            # Use 3D polyline for BMPs with Z dimension
                            msp.add_polyline3d(coords + [coords[0]], dxfattribs={'layer': layer_name})
                        else:
                            # Use lightweight polyline only for true 2D BMPs
                            msp.add_lwpolyline([(c[0], c[1]) for c in coords], close=True, dxfattribs={'layer': layer_name})
                        count += 1
                elif bmp.get('location_wkt'):
                    coords = self._parse_wkt_coords(bmp['location_wkt'])
                    if coords:
                        # Point with 3D support
                        msp.add_point(coords[0], dxfattribs={'layer': layer_name})
                        count += 1
                    
            except Exception as e:
                continue
        
        return count
    
    def _export_intelligent_surface_models(self, conn, project_id: str, doc, msp) -> int:
        """Export surface models on layers like 'SURFACE-EG'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                surface_id,
                surface_type,
                phase,
                ST_AsText(surface_geometry) as geometry_wkt,
                ST_GeometryType(surface_geometry) as geometry_type
            FROM surface_models
            WHERE project_id = %s AND surface_geometry IS NOT NULL
        """, (project_id,))
        
        surfaces = cur.fetchall()
        cur.close()
        
        count = 0
        for surface in surfaces:
            try:
                # Generate layer name using standards system
                properties = {
                    'surface_type': surface.get('surface_type', 'existing_grade'),
                    'phase': surface.get('phase', 'existing')
                }
                
                layer_name = self._generate_layer_name('surface_model', properties, 'POLYGON')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Export boundary polyline with elevation support for terrain surfaces
                coords = self._parse_wkt_coords(surface['geometry_wkt'])
                if coords:
                    is_3d = len(coords[0]) > 2 if coords else False
                    
                    if is_3d:
                        # Use 3D polyline for surfaces with Z dimension
                        msp.add_polyline3d(coords + [coords[0]], dxfattribs={'layer': layer_name})
                    else:
                        # Use lightweight polyline only for true 2D surfaces
                        msp.add_lwpolyline([(c[0], c[1]) for c in coords], close=True, dxfattribs={'layer': layer_name})
                    count += 1
                    
            except Exception as e:
                continue
        
        return count
    
    def _export_intelligent_alignments(self, conn, project_id: str, doc, msp) -> int:
        """Export alignments on layers like 'CENTERLINE-ROAD'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                alignment_id,
                alignment_type,
                phase,
                name,
                ST_AsText(centerline_geometry) as geometry_wkt
            FROM horizontal_alignments
            WHERE project_id = %s AND centerline_geometry IS NOT NULL
        """, (project_id,))
        
        alignments = cur.fetchall()
        cur.close()
        
        count = 0
        for alignment in alignments:
            try:
                # Generate layer name using standards system
                properties = {
                    'alignment_type': alignment.get('alignment_type', 'road'),
                    'phase': alignment.get('phase', 'proposed'),
                    'name': alignment.get('name')
                }
                
                layer_name = self._generate_layer_name('alignment', properties, 'LINE')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Parse WKT and create polyline with vertical alignment support
                coords = self._parse_wkt_coords(alignment['geometry_wkt'])
                if coords:
                    is_3d = len(coords[0]) > 2 if coords else False
                    
                    if is_3d:
                        # Use 3D polyline for alignments with Z dimension
                        msp.add_polyline3d(coords, dxfattribs={'layer': layer_name})
                    else:
                        # Use lightweight polyline only for horizontal-only alignments
                        msp.add_lwpolyline([(c[0], c[1]) for c in coords], dxfattribs={'layer': layer_name})
                    count += 1
                    
            except Exception as e:
                continue
        
        return count
    
    def _export_intelligent_survey_points(self, conn, project_id: str, doc, msp) -> int:
        """Export survey points on layers like 'CONTROL-POINT', 'TOPO'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                point_id,
                point_type,
                phase,
                description,
                ST_X(point_geometry) as x,
                ST_Y(point_geometry) as y,
                ST_Z(point_geometry) as z
            FROM survey_points
            WHERE project_id = %s AND point_geometry IS NOT NULL
        """, (project_id,))
        
        points = cur.fetchall()
        cur.close()
        
        count = 0
        for point in points:
            try:
                # Generate layer name using standards system
                properties = {
                    'point_type': point.get('point_type', 'topo'),
                    'phase': point.get('phase', 'survey')
                }
                
                layer_name = self._generate_layer_name('survey_point', properties, 'POINT')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Create point
                x = point.get('x', 0)
                y = point.get('y', 0)
                z = point.get('z', 0)
                msp.add_point((x, y, z), dxfattribs={'layer': layer_name})
                count += 1
                
            except Exception as e:
                continue
        
        return count
    
    def _export_intelligent_site_trees(self, conn, project_id: str, doc, msp) -> int:
        """Export trees on layers like 'TREE-EXIST', 'TREE-PROPOSED'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                tree_id,
                tree_status,
                species,
                phase,
                ST_X(location) as x,
                ST_Y(location) as y,
                ST_Z(location) as z
            FROM site_trees
            WHERE project_id = %s AND location IS NOT NULL
        """, (project_id,))
        
        trees = cur.fetchall()
        cur.close()
        
        count = 0
        for tree in trees:
            try:
                # Generate layer name using standards system
                properties = {
                    'tree_status': tree.get('tree_status', 'existing'),
                    'species': tree.get('species'),
                    'phase': tree.get('phase', 'existing')
                }
                
                layer_name = self._generate_layer_name('site_tree', properties, 'POINT')
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Create point
                x = tree.get('x', 0)
                y = tree.get('y', 0)
                z = tree.get('z', 0)
                msp.add_point((x, y, z), dxfattribs={'layer': layer_name})
                count += 1
                
            except Exception as e:
                continue
        
        return count
