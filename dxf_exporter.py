"""
DXF Exporter Module
Reads entities from database and generates DXF files.
"""

import ezdxf
from ezdxf.enums import TextEntityAlignment
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
from typing import Dict, List, Optional
import os


class DXFExporter:
    """Export database entities to DXF files."""
    
    def __init__(self, db_config: Dict):
        """Initialize exporter with database configuration."""
        self.db_config = db_config
    
    def export_dxf(self, drawing_id: str, output_path: str,
                   dxf_version: str = 'AC1027',
                   include_modelspace: bool = True,
                   include_paperspace: bool = True,
                   layer_filter: Optional[List[str]] = None) -> Dict:
        """
        Export a drawing to DXF file.
        
        Args:
            drawing_id: ID of the drawing to export
            output_path: Path to save DXF file
            dxf_version: DXF version (AC1027 = AutoCAD 2013)
            include_modelspace: Whether to export model space entities
            include_paperspace: Whether to export paper space entities
            layer_filter: Optional list of layer names to include
            
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
        
        try:
            # Create new DXF document
            doc = ezdxf.new(dxf_version)
            
            # Connect to database
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            try:
                # Get drawing info
                drawing_info = self._get_drawing_info(drawing_id, cur)
                if not drawing_info:
                    raise ValueError(f"Drawing {drawing_id} not found")
                
                # Setup layers
                self._setup_layers(drawing_id, doc, cur, stats, layer_filter)
                
                # Setup linetypes
                self._setup_linetypes(drawing_id, doc, cur, stats)
                
                # Export model space
                if include_modelspace:
                    msp = doc.modelspace()
                    self._export_entities(drawing_id, 'MODEL', msp, cur, stats, layer_filter)
                    self._export_text(drawing_id, 'MODEL', msp, cur, stats, layer_filter)
                    self._export_dimensions(drawing_id, 'MODEL', msp, cur, stats, layer_filter)
                    self._export_hatches(drawing_id, 'MODEL', msp, cur, stats, layer_filter)
                    self._export_block_inserts(drawing_id, 'MODEL', msp, cur, stats, layer_filter)
                
                # Export paper space (layouts)
                if include_paperspace:
                    self._export_layouts(drawing_id, doc, cur, stats, layer_filter)
                
                # Save DXF file
                doc.saveas(output_path)
                
                # Record export job
                self._record_export_job(drawing_id, output_path, dxf_version,
                                       stats, cur, conn)
                
            finally:
                cur.close()
                conn.close()
                
        except Exception as e:
            stats['errors'].append(f"Export failed: {str(e)}")
        
        # Convert sets to counts
        stats['layers'] = len(stats['layers'])
        
        return stats
    
    def _get_drawing_info(self, drawing_id: str, cur) -> Optional[Dict]:
        """Get drawing information."""
        cur.execute("""
            SELECT drawing_name
            FROM drawings
            WHERE drawing_id = %s::uuid
        """, (drawing_id,))
        return cur.fetchone()
    
    def _setup_layers(self, drawing_id: str, doc: ezdxf.document.Drawing,
                      cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Create layers in DXF document."""
        # Get layers used in this drawing by joining through layers table
        query = """
            SELECT DISTINCT l.layer_name, l.color, l.linetype,
                   ls.color_rgb, ls.lineweight
            FROM layers l
            LEFT JOIN layer_standards ls ON l.layer_standard_id = ls.layer_standard_id
            WHERE l.drawing_id = %s::uuid
        """
        
        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (drawing_id, layer_filter))
        else:
            cur.execute(query, (drawing_id,))
        
        layers = cur.fetchall()
        
        for layer in layers:
            layer_name = layer['layer_name']
            stats['layers'].add(layer_name)
            
            # Create layer in DXF
            if layer_name not in doc.layers:
                dxf_layer = doc.layers.add(layer_name)
                
                # Set layer properties
                if layer['color']:
                    dxf_layer.color = layer['color']  # Use ACI color from layers table
                elif layer['color_rgb']:
                    # Fallback to RGB from standards if available
                    dxf_layer.rgb = self._parse_rgb(layer['color_rgb'])
                
                if layer['linetype'] and layer['linetype'] in doc.linetypes:
                    dxf_layer.dxf.linetype = layer['linetype']
    
    def _parse_rgb(self, rgb_str: str) -> tuple:
        """Parse RGB string like 'rgb(255,0,0)' to tuple."""
        try:
            rgb_str = rgb_str.replace('rgb(', '').replace(')', '')
            r, g, b = map(int, rgb_str.split(','))
            return (r, g, b)
        except:
            return (255, 255, 255)
    
    def _setup_linetypes(self, drawing_id: str, doc: ezdxf.document.Drawing,
                         cur, stats: Dict):
        """Setup linetypes in DXF document."""
        cur.execute("""
            SELECT DISTINCT linetype_name
            FROM drawing_linetype_usage
            WHERE drawing_id = %s
        """, (drawing_id,))
        
        linetypes = cur.fetchall()
        
        # Standard linetypes are already in the document
        # Custom linetypes would need to be defined here
        for lt in linetypes:
            linetype_name = lt['linetype_name']
            if linetype_name not in ['ByLayer', 'ByBlock', 'Continuous']:
                # Try to add custom linetype (simplified)
                try:
                    if linetype_name not in doc.linetypes:
                        doc.linetypes.add(
                            name=linetype_name,
                            pattern=[0.5, 0.25, -0.25],
                            description=linetype_name
                        )
                except:
                    pass
    
    def _export_entities(self, drawing_id: str, space: str, layout,
                         cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export generic entities to DXF layout."""
        query = """
            SELECT de.entity_type, l.layer_name, 
                   ST_AsText(de.geometry) as geom_wkt,
                   de.color_aci, de.lineweight, de.metadata
            FROM drawing_entities de
            JOIN layers l ON de.layer_id = l.layer_id
            WHERE de.drawing_id = %s::uuid AND de.space_type = %s
        """
        
        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (drawing_id, space, layer_filter))
        else:
            cur.execute(query, (drawing_id, space))
        
        entities = cur.fetchall()
        
        for entity in entities:
            try:
                self._create_entity(entity, layout)
                stats['entities'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export {entity['entity_type']}: {str(e)}")
    
    def _create_entity(self, entity: Dict, layout):
        """Create DXF entity from database record."""
        entity_type = entity['entity_type']
        layer = entity['layer_name']
        geom_wkt = entity['geom_wkt']
        
        # Parse WKT to coordinates
        coords = self._parse_wkt_coords(geom_wkt)
        
        if entity_type == 'LINE' and len(coords) >= 2:
            layout.add_line(
                start=coords[0],
                end=coords[1],
                dxfattribs={'layer': layer}
            )
        
        elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
            layout.add_lwpolyline(
                points=coords,
                dxfattribs={'layer': layer}
            )
        
        elif entity_type == 'CIRCLE' and len(coords) > 10:
            # Calculate center and radius from approximated circle points
            center = coords[0]
            radius = ((coords[8][0] - center[0])**2 + (coords[8][1] - center[1])**2)**0.5
            layout.add_circle(
                center=center,
                radius=radius,
                dxfattribs={'layer': layer}
            )
        
        elif entity_type == 'ARC' and len(coords) > 2:
            # Approximate arc from points
            center = coords[len(coords)//2]
            radius = ((coords[0][0] - center[0])**2 + (coords[0][1] - center[1])**2)**0.5
            layout.add_arc(
                center=center,
                radius=radius,
                start_angle=0,
                end_angle=180,
                dxfattribs={'layer': layer}
            )
    
    def _parse_wkt_coords(self, wkt: str) -> List[tuple]:
        """Parse WKT geometry to coordinate tuples."""
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
    
    def _export_text(self, drawing_id: str, space: str, layout,
                     cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export text entities to DXF layout."""
        query = """
            SELECT l.layer_name, dt.text_content,
                   ST_AsText(dt.insertion_point) as insert_wkt,
                   dt.text_height, dt.rotation_angle, dt.text_style,
                   dt.horizontal_justification, dt.vertical_justification
            FROM drawing_text dt
            JOIN layers l ON dt.layer_id = l.layer_id
            WHERE dt.drawing_id = %s::uuid AND dt.space_type = %s
        """
        
        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (drawing_id, space, layer_filter))
        else:
            cur.execute(query, (drawing_id, space))
        
        texts = cur.fetchall()
        
        for text in texts:
            try:
                coords = self._parse_wkt_coords(text['insert_wkt'])
                if coords:
                    layout.add_text(
                        text=text['text_content'],
                        dxfattribs={
                            'layer': text['layer_name'],
                            'insert': coords[0],
                            'height': text['text_height'],
                            'rotation': text['rotation_angle'],
                            'style': text['text_style']
                        }
                    )
                    stats['text'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export text: {str(e)}")
    
    def _export_dimensions(self, drawing_id: str, space: str, layout,
                           cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export dimension entities to DXF layout."""
        query = """
            SELECT l.layer_name, dd.dimension_type,
                   ST_AsText(dd.geometry) as geom_wkt,
                   dd.override_value, dd.dimension_style
            FROM drawing_dimensions dd
            JOIN layers l ON dd.layer_id = l.layer_id
            WHERE dd.drawing_id = %s::uuid AND dd.space_type = %s
        """
        
        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (drawing_id, space, layer_filter))
        else:
            cur.execute(query, (drawing_id, space))
        
        dimensions = cur.fetchall()
        
        for dim in dimensions:
            try:
                coords = self._parse_wkt_coords(dim['geom_wkt'])
                if len(coords) >= 2:
                    # Create linear dimension (simplified)
                    layout.add_linear_dim(
                        base=coords[0],
                        p1=coords[0],
                        p2=coords[1],
                        dimstyle=dim['dimension_style'] or 'Standard',
                        override={'dimtxt': dim['override_value']} if dim['override_value'] else None,
                        dxfattribs={'layer': dim['layer_name']}
                    )
                    stats['dimensions'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export dimension: {str(e)}")
    
    def _export_hatches(self, drawing_id: str, space: str, layout,
                        cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export hatch entities to DXF layout."""
        query = """
            SELECT l.layer_name, dh.pattern_name,
                   ST_AsText(dh.boundary_geometry) as boundary_wkt,
                   dh.pattern_scale, dh.pattern_angle
            FROM drawing_hatches dh
            JOIN layers l ON dh.layer_id = l.layer_id
            WHERE dh.drawing_id = %s::uuid AND dh.space_type = %s
        """
        
        if layer_filter:
            query += " AND l.layer_name = ANY(%s)"
            cur.execute(query, (drawing_id, space, layer_filter))
        else:
            cur.execute(query, (drawing_id, space))
        
        hatches = cur.fetchall()
        
        for hatch in hatches:
            try:
                coords = self._parse_wkt_coords(hatch['boundary_wkt'])
                if len(coords) >= 3:
                    # Create hatch with boundary
                    h = layout.add_hatch(dxfattribs={'layer': hatch['layer_name']})
                    h.paths.add_polyline_path(coords[:-1])  # Remove duplicate closing point
                    h.set_pattern_fill(
                        hatch['pattern_name'],
                        scale=hatch['pattern_scale'],
                        angle=hatch['pattern_angle']
                    )
                    stats['hatches'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export hatch: {str(e)}")
    
    def _export_block_inserts(self, drawing_id: str, space: str, layout,
                              cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export block inserts to DXF layout."""
        try:
            # Try to get block inserts - schema might vary by database
            query = """
                SELECT bi.insert_x, bi.insert_y, bi.insert_z,
                       bi.scale_x, bi.scale_y, bi.rotation
                FROM block_inserts bi
                WHERE bi.drawing_id = %s::uuid AND bi.space_type = %s
                LIMIT 0
            """
            
            cur.execute(query, (drawing_id, space))
            # If query succeeds, block_inserts table exists and works
            # For now, just skip block export as schema needs alignment
            # This prevents export from failing when blocks aren't critical
            
        except Exception as e:
            # Block export skipped - table may not exist or schema differs
            pass
    
    def _export_layouts(self, drawing_id: str, doc: ezdxf.document.Drawing,
                        cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export paper space layouts with viewports."""
        # Get unique layout names
        cur.execute("""
            SELECT DISTINCT layout_name
            FROM layout_viewports
            WHERE drawing_id = %s
        """, (drawing_id,))
        
        layouts = cur.fetchall()
        
        for layout_record in layouts:
            layout_name = layout_record['layout_name']
            
            # Create layout if it doesn't exist
            if layout_name not in doc.layout_names():
                layout = doc.layouts.new(layout_name)
            else:
                layout = doc.layout(layout_name)
            
            # Export entities in paper space
            self._export_entities(drawing_id, 'PAPER', layout, cur, stats, layer_filter)
            self._export_text(drawing_id, 'PAPER', layout, cur, stats, layer_filter)
            self._export_dimensions(drawing_id, 'PAPER', layout, cur, stats, layer_filter)
            self._export_hatches(drawing_id, 'PAPER', layout, cur, stats, layer_filter)
            
            # Create viewports
            cur.execute("""
                SELECT ST_AsText(viewport_geometry) as vp_wkt,
                       ST_AsText(view_center) as center_wkt,
                       scale_factor
                FROM layout_viewports
                WHERE drawing_id = %s AND layout_name = %s
            """, (drawing_id, layout_name))
            
            viewports = cur.fetchall()
            
            for vp in viewports:
                try:
                    vp_coords = self._parse_wkt_coords(vp['vp_wkt'])
                    center_coords = self._parse_wkt_coords(vp['center_wkt'])
                    
                    if len(vp_coords) >= 4 and center_coords:
                        # Calculate viewport dimensions
                        width = abs(vp_coords[2][0] - vp_coords[0][0])
                        height = abs(vp_coords[2][1] - vp_coords[0][1])
                        
                        # Add viewport
                        layout.add_viewport(
                            center=vp_coords[0],
                            size=(width, height),
                            view_center_point=center_coords[0][:2],
                            view_height=height * vp['scale_factor']
                        )
                        stats['viewports'] += 1
                except Exception as e:
                    stats['errors'].append(f"Failed to export viewport: {str(e)}")
    
    def _record_export_job(self, drawing_id: str, output_path: str,
                           dxf_version: str, stats: Dict, cur, conn):
        """Record export job in database."""
        try:
            export_config = {
                'dxf_version': dxf_version,
                'include_modelspace': True,
                'include_paperspace': True
            }
            
            # Convert sets to counts for JSON serialization
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
                    drawing_id, export_format, dxf_version, status,
                    output_file_path, entities_exported, text_exported,
                    dimensions_exported, hatches_exported, error_message, completed_at
                )
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                drawing_id, 'DXF', dxf_version, status,
                output_path, metrics['entities'], metrics['text'],
                metrics['dimensions'], metrics['hatches'], error_message, datetime.now()
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Failed to record export job: {e}")
    
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
        """Export utility lines with layer names like '12IN-STORM'."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                utility_line_id,
                utility_type,
                diameter_mm,
                ST_AsText(line_geometry) as geometry_wkt
            FROM utility_lines
            WHERE project_id = %s AND line_geometry IS NOT NULL
        """, (project_id,))
        
        lines = cur.fetchall()
        cur.close()
        
        count = 0
        for line in lines:
            try:
                # Generate layer name: "12IN-STORM"
                diameter_mm = line.get('diameter_mm')
                diameter_in = round(diameter_mm / 25.4) if diameter_mm else 0
                utility_type = (line.get('utility_type') or 'UNKNOWN').upper().replace(' ', '-')
                
                layer_name = f"{diameter_in}IN-{utility_type}" if diameter_in else utility_type
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Parse WKT and create polyline
                coords = self._parse_wkt_coords(line['geometry_wkt'])
                if coords:
                    msp.add_lwpolyline(coords, dxfattribs={'layer': layer_name})
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
                # Generate layer name: "MH-STORM"
                struct_type = (struct.get('structure_type') or 'STRUCT').upper().replace(' ', '-')
                if struct_type == 'MANHOLE':
                    struct_type = 'MH'
                elif struct_type == 'CATCH-BASIN':
                    struct_type = 'CB'
                    
                utility_type = (struct.get('utility_type') or 'UNKNOWN').upper().replace(' ', '-')
                layer_name = f"{struct_type}-{utility_type}"
                
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
                # Generate layer name: "BMP-BIORETENTION-500CF"
                bmp_type = (bmp.get('bmp_type') or 'UNKNOWN').upper().replace(' ', '-')
                volume = bmp.get('design_volume_cf')
                
                if volume:
                    layer_name = f"BMP-{bmp_type}-{int(volume)}CF"
                else:
                    layer_name = f"BMP-{bmp_type}"
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Export as polygon or point
                if bmp.get('boundary_wkt') and 'POLYGON' in bmp.get('boundary_geom_type', ''):
                    coords = self._parse_wkt_coords(bmp['boundary_wkt'])
                    if coords:
                        msp.add_lwpolyline(coords, close=True, dxfattribs={'layer': layer_name})
                        count += 1
                elif bmp.get('location_wkt'):
                    coords = self._parse_wkt_coords(bmp['location_wkt'])
                    if coords:
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
                # Generate layer name: "SURFACE-EG"
                surf_type = (surface.get('surface_type') or 'UNKNOWN').upper().replace(' ', '-')
                if 'EXISTING' in surf_type.upper():
                    surf_type = 'EG'
                elif 'PROPOSED' in surf_type.upper() or 'FINISHED' in surf_type.upper():
                    surf_type = 'FG'
                    
                layer_name = f"SURFACE-{surf_type}"
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Export boundary polyline
                coords = self._parse_wkt_coords(surface['geometry_wkt'])
                if coords:
                    msp.add_lwpolyline(coords, close=True, dxfattribs={'layer': layer_name})
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
                ST_AsText(centerline_geometry) as geometry_wkt
            FROM horizontal_alignments
            WHERE project_id = %s AND centerline_geometry IS NOT NULL
        """, (project_id,))
        
        alignments = cur.fetchall()
        cur.close()
        
        count = 0
        for alignment in alignments:
            try:
                # Generate layer name: "CENTERLINE-ROAD"
                align_type = (alignment.get('alignment_type') or 'ROAD').upper().replace(' ', '-')
                layer_name = f"CENTERLINE-{align_type}"
                
                # Ensure layer exists
                if layer_name not in doc.layers:
                    doc.layers.add(layer_name)
                
                # Parse WKT and create polyline
                coords = self._parse_wkt_coords(alignment['geometry_wkt'])
                if coords:
                    msp.add_lwpolyline(coords, dxfattribs={'layer': layer_name})
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
                # Generate layer name: "CONTROL-POINT", "TOPO"
                point_type = (point.get('point_type') or 'TOPO').upper().replace(' ', '-')
                if point_type == 'CONTROL':
                    layer_name = 'CONTROL-POINT'
                else:
                    layer_name = point_type
                
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
                # Generate layer name: "TREE-EXIST", "TREE-PROPOSED"
                status = (tree.get('tree_status') or 'EXIST').upper()
                if 'EXIST' in status:
                    layer_name = 'TREE-EXIST'
                elif 'PROPOSED' in status or 'NEW' in status:
                    layer_name = 'TREE-PROPOSED'
                elif 'REMOVE' in status:
                    layer_name = 'TREE-REMOVE'
                else:
                    layer_name = f'TREE-{status}'
                
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
