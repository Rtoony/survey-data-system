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
    
    def export_dxf(self, drawing_id: int, output_path: str,
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
    
    def _get_drawing_info(self, drawing_id: int, cur) -> Optional[Dict]:
        """Get drawing information."""
        cur.execute("""
            SELECT drawing_name, cad_units, scale_factor
            FROM drawings
            WHERE drawing_id = %s
        """, (drawing_id,))
        return cur.fetchone()
    
    def _setup_layers(self, drawing_id: int, doc: ezdxf.document.Drawing,
                      cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Create layers in DXF document."""
        # Get layers used in this drawing
        query = """
            SELECT DISTINCT dlu.layer_name, ls.color_rgb, ls.linetype, ls.lineweight
            FROM drawing_layer_usage dlu
            LEFT JOIN layer_standards ls ON dlu.layer_name = ls.layer_name
            WHERE dlu.drawing_id = %s
        """
        
        if layer_filter:
            query += " AND dlu.layer_name = ANY(%s)"
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
                
                # Set layer properties from standards if available
                if layer['color_rgb']:
                    # Convert RGB to ACI color (simplified)
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
    
    def _setup_linetypes(self, drawing_id: int, doc: ezdxf.document.Drawing,
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
    
    def _export_entities(self, drawing_id: int, space: str, layout,
                         cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export generic entities to DXF layout."""
        query = """
            SELECT entity_type, layer_name, 
                   ST_AsText(geometry) as geom_wkt,
                   color_aci, lineweight, metadata
            FROM drawing_entities
            WHERE drawing_id = %s AND space_type = %s
        """
        
        if layer_filter:
            query += " AND layer_name = ANY(%s)"
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
    
    def _export_text(self, drawing_id: int, space: str, layout,
                     cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export text entities to DXF layout."""
        query = """
            SELECT layer_name, text_content,
                   ST_AsText(insertion_point) as insert_wkt,
                   text_height, rotation_angle, text_style, justification
            FROM drawing_text
            WHERE drawing_id = %s AND space_type = %s
        """
        
        if layer_filter:
            query += " AND layer_name = ANY(%s)"
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
    
    def _export_dimensions(self, drawing_id: int, space: str, layout,
                           cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export dimension entities to DXF layout."""
        query = """
            SELECT layer_name, dimension_type,
                   ST_AsText(geometry) as geom_wkt,
                   measurement_override, dimension_style
            FROM drawing_dimensions
            WHERE drawing_id = %s AND space_type = %s
        """
        
        if layer_filter:
            query += " AND layer_name = ANY(%s)"
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
                        override={'dimtxt': dim['measurement_override']} if dim['measurement_override'] else None,
                        dxfattribs={'layer': dim['layer_name']}
                    )
                    stats['dimensions'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export dimension: {str(e)}")
    
    def _export_hatches(self, drawing_id: int, space: str, layout,
                        cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export hatch entities to DXF layout."""
        query = """
            SELECT layer_name, pattern_name,
                   ST_AsText(boundary_geometry) as boundary_wkt,
                   pattern_scale, pattern_angle
            FROM drawing_hatches
            WHERE drawing_id = %s AND space_type = %s
        """
        
        if layer_filter:
            query += " AND layer_name = ANY(%s)"
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
    
    def _export_block_inserts(self, drawing_id: int, space: str, layout,
                              cur, stats: Dict, layer_filter: Optional[List[str]]):
        """Export block inserts to DXF layout."""
        query = """
            SELECT block_name, ST_AsText(insertion_point) as insert_wkt,
                   scale_x, scale_y, scale_z, rotation
            FROM block_inserts
            WHERE drawing_id = %s
        """
        
        cur.execute(query, (drawing_id,))
        blocks = cur.fetchall()
        
        for block in blocks:
            try:
                coords = self._parse_wkt_coords(block['insert_wkt'])
                if coords:
                    # Insert block reference
                    layout.add_blockref(
                        block['block_name'],
                        insert=coords[0],
                        dxfattribs={
                            'xscale': block['scale_x'],
                            'yscale': block['scale_y'],
                            'zscale': block['scale_z'],
                            'rotation': block['rotation']
                        }
                    )
                    stats['blocks'] += 1
            except Exception as e:
                stats['errors'].append(f"Failed to export block insert: {str(e)}")
    
    def _export_layouts(self, drawing_id: int, doc: ezdxf.document.Drawing,
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
    
    def _record_export_job(self, drawing_id: int, output_path: str,
                           dxf_version: str, stats: Dict, cur, conn):
        """Record export job in database."""
        try:
            export_config = {
                'dxf_version': dxf_version,
                'include_modelspace': True,
                'include_paperspace': True
            }
            
            metrics = {
                'entities': stats['entities'],
                'text': stats['text'],
                'dimensions': stats['dimensions'],
                'hatches': stats['hatches'],
                'blocks': stats['blocks'],
                'viewports': stats['viewports'],
                'layers': stats['layers']
            }
            
            status = 'completed' if not stats['errors'] else 'failed'
            error_log = '\n'.join(stats['errors']) if stats['errors'] else None
            
            cur.execute("""
                INSERT INTO export_jobs (
                    drawing_id, export_format, dxf_version, status,
                    export_config, output_file_path, metrics, error_log,
                    started_at, completed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                drawing_id, 'DXF', dxf_version, status,
                json.dumps(export_config), output_path,
                json.dumps(metrics), error_log,
                datetime.now(), datetime.now()
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Failed to record export job: {e}")
