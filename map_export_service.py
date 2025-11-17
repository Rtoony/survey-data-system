"""
Map Export Service
Handles geospatial data export in multiple formats (DXF, SHP, PNG)
"""

import os
import uuid
import zipfile
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from io import BytesIO
import tempfile

from pyproj import Transformer
from shapely.geometry import box, shape, mapping
from shapely.ops import transform
import fiona
from fiona.crs import from_epsg
import ezdxf
from owslib.wfs import WebFeatureService
from PIL import Image, ImageDraw, ImageFont
import psycopg2
from psycopg2.extras import RealDictCursor

# Import coordinate system service for dynamic CRS support
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.coordinate_system_service import CoordinateSystemService


class MapExportService:
    """Service for exporting map data in various formats with dynamic coordinate system support"""

    def __init__(self, export_dir: str = "/tmp/exports", db_conn=None, db_config=None):
        """
        Initialize map export service.

        Args:
            export_dir: Directory for export files
            db_conn: Database connection (optional)
            db_config: Database config dict for coordinate system service (required for dynamic CRS)
        """
        self.export_dir = export_dir
        self.db_conn = db_conn
        os.makedirs(export_dir, exist_ok=True)

        # Initialize coordinate system service for dynamic CRS support
        if db_config:
            self.crs_service = CoordinateSystemService(db_config)
        else:
            self.crs_service = None
            print("Warning: Map export service initialized without db_config - dynamic CRS not available")
    
    def transform_bbox(self, bbox: Dict, source_crs: str, target_crs: str) -> Tuple[float, float, float, float]:
        """
        Transform bounding box between any two coordinate systems.

        Args:
            bbox: Dict with minx, miny, maxx, maxy keys
            source_crs: Source EPSG code (e.g., 'EPSG:3857')
            target_crs: Target EPSG code (e.g., 'EPSG:2226')

        Returns:
            Tuple of (minx, miny, maxx, maxy) in target CRS
        """
        minx, miny, maxx, maxy = bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy']

        if not self.crs_service:
            raise ValueError("Coordinate system service not initialized - cannot transform coordinates")

        transformer = self.crs_service.get_transformer(source_crs, target_crs)
        minx_transformed, miny_transformed = transformer.transform(minx, miny)
        maxx_transformed, maxy_transformed = transformer.transform(maxx, maxy)

        return (minx_transformed, miny_transformed, maxx_transformed, maxy_transformed)
    
    def fetch_drawing_entities_by_layer(self, bbox: Tuple, project_id: Optional[str] = None, srid: int = 2226) -> Dict[str, List[Dict]]:
        """
        Fetch all drawing entities within bounding box, grouped by layer name.
        Optionally filter by project_id.

        Args:
            bbox: Bounding box coordinates (minx, miny, maxx, maxy) in the specified SRID
            project_id: Optional UUID of the project to filter entities
            srid: SRID of the bounding box coordinates (default: 2226 for backward compatibility)

        Returns:
            Dict with layer names as keys, lists of GeoJSON features as values
        """
        if not self.db_conn:
            print("No database connection provided, skipping drawing entities")
            return {}

        minx, miny, maxx, maxy = bbox
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query all drawing entities within bbox, grouped by layer
                # Filter by project_id if provided
                if project_id:
                    query = """
                        SELECT 
                            l.layer_name,
                            e.entity_id,
                            e.entity_type,
                            e.color_aci,
                            e.linetype,
                            e.lineweight,
                            ST_AsGeoJSON(e.geometry) as geometry_json,
                            ST_SRID(e.geometry) as srid
                        FROM drawing_entities e
                        LEFT JOIN layers l ON e.layer_id = l.layer_id
                        WHERE e.project_id = %s
                        AND ST_Intersects(
                            e.geometry,
                            ST_MakeEnvelope(%s, %s, %s, %s, %s)
                        )
                        AND e.entity_type NOT IN ('TEXT', 'MTEXT', 'HATCH', 'ATTDEF', 'ATTRIB')
                        ORDER BY l.layer_name, e.entity_type
                    """
                    cur.execute(query, (project_id, minx, miny, maxx, maxy, srid))
                else:
                    # No project filter - get all entities in bbox
                    query = """
                        SELECT 
                            l.layer_name,
                            e.entity_id,
                            e.entity_type,
                            e.color_aci,
                            e.linetype,
                            e.lineweight,
                            ST_AsGeoJSON(e.geometry) as geometry_json,
                            ST_SRID(e.geometry) as srid
                        FROM drawing_entities e
                        LEFT JOIN layers l ON e.layer_id = l.layer_id
                        WHERE ST_Intersects(
                            e.geometry,
                            ST_MakeEnvelope(%s, %s, %s, %s, %s)
                        )
                        AND e.entity_type NOT IN ('TEXT', 'MTEXT', 'HATCH', 'ATTDEF', 'ATTRIB')
                        ORDER BY l.layer_name, e.entity_type
                    """
                    cur.execute(query, (minx, miny, maxx, maxy, srid))
                
                entities = cur.fetchall()
                
                print(f"Found {len(entities)} drawing entities in bbox" + 
                      (f" for project {project_id}" if project_id else ""))
                
                # Group by layer name
                layers_data = {}
                for entity in entities:
                    layer_name = entity['layer_name'] or 'Default'
                    
                    if layer_name not in layers_data:
                        layers_data[layer_name] = []
                    
                    # Convert to GeoJSON feature
                    geom_json = json.loads(entity['geometry_json'])
                    
                    feature = {
                        'type': 'Feature',
                        'geometry': geom_json,
                        'properties': {
                            'entity_id': str(entity['entity_id']),
                            'entity_type': entity['entity_type'],
                            'layer_name': layer_name,
                            'color_aci': entity['color_aci'],
                            'linetype': entity['linetype'],
                            'lineweight': entity['lineweight'],
                            'srid': entity['srid']
                        }
                    }
                    
                    layers_data[layer_name].append(feature)
                
                print(f"Grouped entities into {len(layers_data)} layers: {list(layers_data.keys())}")
                return layers_data
                
        except Exception as e:
            print(f"Error fetching drawing entities: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def fetch_wfs_data(self, layer_config: Dict, bbox: Tuple, epsg_code: str = 'EPSG:2226') -> Dict:
        """
        Fetch data from WFS service.

        Args:
            layer_config: WFS layer configuration
            bbox: Bounding box tuple (minx, miny, maxx, maxy)
            epsg_code: EPSG code for the WFS request (default: EPSG:2226 for backward compatibility)

        Returns:
            GeoJSON dict
        """
        try:
            wfs = WebFeatureService(url=layer_config['url'], version='2.0.0', timeout=30)

            response = wfs.getfeature(
                typename=layer_config['layer_name'],
                bbox=bbox,
                srsname=epsg_code,
                outputFormat='application/json'
            )

            if response is None:
                print(f"WFS getfeature returned None for {layer_config.get('name', 'unknown')}")
                return {"type": "FeatureCollection", "features": []}

            geojson_data = json.loads(response.read())
            return geojson_data
            
        except Exception as e:
            print(f"Error fetching WFS data for {layer_config['name']}: {e}")
            return {"type": "FeatureCollection", "features": []}
    
    def clip_features(self, geojson: Dict, bbox: Tuple) -> List[Dict]:
        """
        Clip features to bounding box.

        Args:
            geojson: GeoJSON feature collection
            bbox: Bounding box tuple (minx, miny, maxx, maxy)

        Returns:
            List of clipped features
        """
        bbox_poly = box(*bbox)
        clipped_features = []
        
        for feature in geojson.get('features', []):
            try:
                geom = shape(feature['geometry'])
                
                if geom.intersects(bbox_poly):
                    clipped_geom = geom.intersection(bbox_poly)
                    feature['geometry'] = mapping(clipped_geom)
                    clipped_features.append(feature)
            except Exception as e:
                print(f"Error clipping feature: {e}")
                continue
        
        return clipped_features
    
    def export_to_shapefile(self, features: List[Dict], layer_name: str, output_path: str, epsg_code: int = 2226) -> bool:
        """
        Export features to Shapefile format.

        Args:
            features: List of GeoJSON features
            layer_name: Name of the layer
            output_path: Path to save shapefile
            epsg_code: EPSG code as integer (default: 2226 for backward compatibility)

        Returns:
            True if successful, False otherwise
        """
        if not features:
            print(f"No features to export for {layer_name}")
            return False

        try:
            # Determine geometry type from first feature
            first_geom = shape(features[0]['geometry'])
            geom_type = first_geom.geom_type

            # Build schema from first feature properties
            properties = features[0].get('properties', {})
            schema_props = {}
            for key, value in properties.items():
                if isinstance(value, int):
                    schema_props[key] = 'int'
                elif isinstance(value, float):
                    schema_props[key] = 'float'
                else:
                    schema_props[key] = 'str'

            schema = {
                'geometry': geom_type,
                'properties': schema_props if schema_props else {'id': 'str'}
            }

            # Write shapefile
            with fiona.open(
                output_path,
                'w',
                driver='ESRI Shapefile',
                crs=from_epsg(epsg_code),
                schema=schema
            ) as shp:
                for feature in features:
                    shp.write(feature)

            # Note: Fiona automatically writes the .prj file with the CRS from the from_epsg() call
            # No need to manually write .prj file anymore as fiona handles it correctly
            
            return True
            
        except Exception as e:
            print(f"Error exporting shapefile: {e}")
            return False
    
    def export_to_dxf(self, layers_data: Dict[str, List[Dict]], output_path: str) -> bool:
        """Export features to DXF format with 3D support"""
        try:
            doc = ezdxf.new('R2010')
            if doc is None:
                print("Error: ezdxf.new() returned None")
                return False
            msp = doc.modelspace()
            
            for layer_name, features in layers_data.items():
                # Create layer
                doc.layers.new(name=layer_name)
                
                for feature in features:
                    geom = shape(feature['geometry'])
                    
                    if geom.geom_type == 'Polygon':
                        points = list(geom.exterior.coords)
                        # Check if geometry has Z dimension (preserve even if Z=0)
                        is_3d = len(points[0]) > 2 if points else False
                        
                        if is_3d:
                            # Use 3D polyline for polygons with Z dimension
                            msp.add_polyline3d(points + [points[0]], dxfattribs={'layer': layer_name})
                        else:
                            # Use lightweight polyline only for true 2D polygons
                            msp.add_lwpolyline(
                                [(p[0], p[1]) for p in points],
                                dxfattribs={'layer': layer_name, 'closed': True}
                            )
                    elif geom.geom_type == 'MultiPolygon':
                        for poly in geom.geoms:
                            points = list(poly.exterior.coords)
                            is_3d = len(points[0]) > 2 if points else False
                            
                            if is_3d:
                                msp.add_polyline3d(points + [points[0]], dxfattribs={'layer': layer_name})
                            else:
                                msp.add_lwpolyline(
                                    [(p[0], p[1]) for p in points],
                                    dxfattribs={'layer': layer_name, 'closed': True}
                                )
                    elif geom.geom_type == 'LineString':
                        points = list(geom.coords)
                        is_3d = len(points[0]) > 2 if points else False
                        
                        if is_3d:
                            # Use 3D polyline to preserve Z dimension
                            msp.add_polyline3d(points, dxfattribs={'layer': layer_name})
                        else:
                            msp.add_lwpolyline(
                                [(p[0], p[1]) for p in points],
                                dxfattribs={'layer': layer_name}
                            )
                    elif geom.geom_type == 'MultiLineString':
                        for line in geom.geoms:
                            points = list(line.coords)
                            is_3d = len(points[0]) > 2 if points else False
                            
                            if is_3d:
                                msp.add_polyline3d(points, dxfattribs={'layer': layer_name})
                            else:
                                msp.add_lwpolyline(
                                    [(p[0], p[1]) for p in points],
                                    dxfattribs={'layer': layer_name}
                                )
                    elif geom.geom_type == 'Point':
                        # Support 3D points
                        if geom.has_z:
                            msp.add_point((geom.x, geom.y, geom.z), dxfattribs={'layer': layer_name})
                        else:
                            msp.add_point((geom.x, geom.y), dxfattribs={'layer': layer_name})
                    elif geom.geom_type == 'MultiPoint':
                        for point in geom.geoms:
                            if point.has_z:
                                msp.add_point((point.x, point.y, point.z), dxfattribs={'layer': layer_name})
                            else:
                                msp.add_point((point.x, point.y), dxfattribs={'layer': layer_name})
            
            doc.saveas(output_path)
            return True
            
        except Exception as e:
            print(f"Error exporting DXF: {e}")
            return False
    
    def export_to_kml(self, layers_data: Dict[str, List[Dict]], output_path: str, source_epsg: str = 'EPSG:2226') -> bool:
        """
        Export features to KML format (Google Earth/Maps compatible).

        Args:
            layers_data: Dict of layer names to feature lists
            output_path: Path to save KML file
            source_epsg: Source EPSG code of the data (default: EPSG:2226 for backward compatibility)

        Returns:
            True if successful, False otherwise
        """
        try:
            import xml.etree.ElementTree as ET

            # Create KML root
            kml = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
            document = ET.SubElement(kml, 'Document')
            ET.SubElement(document, 'name').text = 'Map Export'

            # Get transformer from source CRS to WGS84 (EPSG:4326) for KML
            if self.crs_service:
                transformer = self.crs_service.get_transformer(source_epsg, 'EPSG:4326')
            else:
                # Fallback if CRS service not available
                transformer = Transformer.from_crs(source_epsg, 'EPSG:4326', always_xy=True)

            feature_count = 0

            for layer_name, features in layers_data.items():
                # Create a folder for each layer
                folder = ET.SubElement(document, 'Folder')
                ET.SubElement(folder, 'name').text = layer_name

                for feature in features:
                    try:
                        # Transform geometry to WGS84
                        geom = shape(feature['geometry'])

                        def transform_coords(x, y, z=None):
                            lon, lat = transformer.transform(x, y)
                            return (lon, lat) if z is None else (lon, lat, z)

                        transformed_geom = transform(transform_coords, geom)
                        
                        # Create placemark
                        placemark = ET.SubElement(folder, 'Placemark')
                        
                        # Add properties as description
                        props = feature.get('properties', {})
                        if props:
                            desc = '<![CDATA[<table>'
                            for key, value in props.items():
                                desc += f'<tr><td><b>{key}:</b></td><td>{value}</td></tr>'
                            desc += '</table>]]>'
                            ET.SubElement(placemark, 'description').text = desc
                        
                        # Add geometry
                        self._add_kml_geometry(placemark, transformed_geom)
                        feature_count += 1
                    
                    except Exception as e:
                        print(f"Error transforming feature for KML: {e}")
                        continue
            
            if feature_count == 0:
                print("No features to export to KML")
                return False
            
            # Write to file with pretty formatting
            tree = ET.ElementTree(kml)
            ET.indent(tree, space='  ')
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            print(f"KML export complete: {feature_count} features")
            return True
            
        except Exception as e:
            print(f"Error exporting KML: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_kml_geometry(self, placemark, geom):
        """Add geometry to KML placemark"""
        import xml.etree.ElementTree as ET
        
        if geom.geom_type == 'Point':
            point = ET.SubElement(placemark, 'Point')
            ET.SubElement(point, 'coordinates').text = f'{geom.x},{geom.y},0'
        
        elif geom.geom_type == 'MultiPoint':
            for pt in geom.geoms:
                point = ET.SubElement(placemark, 'Point')
                ET.SubElement(point, 'coordinates').text = f'{pt.x},{pt.y},0'
        
        elif geom.geom_type == 'LineString':
            linestring = ET.SubElement(placemark, 'LineString')
            coords = ' '.join([f'{x},{y},0' for x, y in geom.coords])
            ET.SubElement(linestring, 'coordinates').text = coords
        
        elif geom.geom_type == 'MultiLineString':
            multigeom = ET.SubElement(placemark, 'MultiGeometry')
            for line in geom.geoms:
                linestring = ET.SubElement(multigeom, 'LineString')
                coords = ' '.join([f'{x},{y},0' for x, y in line.coords])
                ET.SubElement(linestring, 'coordinates').text = coords
        
        elif geom.geom_type == 'Polygon':
            polygon = ET.SubElement(placemark, 'Polygon')
            outer = ET.SubElement(polygon, 'outerBoundaryIs')
            linear_ring = ET.SubElement(outer, 'LinearRing')
            coords = ' '.join([f'{x},{y},0' for x, y in geom.exterior.coords])
            ET.SubElement(linear_ring, 'coordinates').text = coords
        
        elif geom.geom_type == 'MultiPolygon':
            multigeom = ET.SubElement(placemark, 'MultiGeometry')
            for poly in geom.geoms:
                polygon = ET.SubElement(multigeom, 'Polygon')
                outer = ET.SubElement(polygon, 'outerBoundaryIs')
                linear_ring = ET.SubElement(outer, 'LinearRing')
                coords = ' '.join([f'{x},{y},0' for x, y in poly.exterior.coords])
                ET.SubElement(linear_ring, 'coordinates').text = coords
    
    def create_map_image(self, bbox: Dict, width: int = 1200, height: int = 900,
                        north_arrow: bool = True, scale_bar: bool = True) -> Optional[str]:
        """Create a simple map placeholder image with annotations"""
        try:
            # Create blank image
            img = Image.new('RGB', (width, height), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # Draw border
            draw.rectangle([(10, 10), (width-10, height-10)], outline='#333333', width=3)
            
            # Add title
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            draw.text((width//2, 40), "Map Export", fill='#333333', font=font, anchor='mm')
            
            # Add coordinates
            coord_text = f"Bounds: {bbox['minx']:.2f}, {bbox['miny']:.2f} to {bbox['maxx']:.2f}, {bbox['maxy']:.2f}"
            draw.text((width//2, 80), coord_text, fill='#666666', font=small_font, anchor='mm')
            
            # Add north arrow if requested
            if north_arrow:
                self._draw_north_arrow(draw, width - 80, 120)
            
            # Add scale bar if requested
            if scale_bar:
                self._draw_scale_bar(draw, 80, height - 80, bbox, width)
            
            # Add watermark
            draw.text((width - 20, height - 20), "ACAD-GIS Map Viewer", 
                     fill='#999999', font=small_font, anchor='rb')
            
            # Save to temp file
            temp_path = os.path.join(self.export_dir, f"map_{uuid.uuid4().hex}.png")
            img.save(temp_path, 'PNG')
            return temp_path
            
        except Exception as e:
            print(f"Error creating map image: {e}")
            return None
    
    def _draw_north_arrow(self, draw, x: int, y: int):
        """Draw a professional compass rose north arrow"""
        import math
        
        # Outer circle
        radius = 35
        draw.ellipse([(x-radius, y-radius), (x+radius, y+radius)], 
                     outline='#000000', width=2)
        
        # Cardinal points - North (filled black)
        north_points = [
            (x, y-radius+5),           # Top point
            (x-8, y-3),                # Left base
            (x, y-8),                  # Center indent
            (x+8, y-3),                # Right base
        ]
        draw.polygon(north_points, fill='#000000', outline='#000000')
        
        # South (white with black outline)
        south_points = [
            (x, y+radius-5),           # Bottom point
            (x-8, y+3),                # Left base
            (x, y+8),                  # Center indent
            (x+8, y+3),                # Right base
        ]
        draw.polygon(south_points, fill='#FFFFFF', outline='#000000')
        
        # East (white with black outline)
        east_points = [
            (x+radius-5, y),           # Right point
            (x+3, y-8),                # Top base
            (x+8, y),                  # Center indent
            (x+3, y+8),                # Bottom base
        ]
        draw.polygon(east_points, fill='#FFFFFF', outline='#000000')
        
        # West (white with black outline)
        west_points = [
            (x-radius+5, y),           # Left point
            (x-3, y-8),                # Top base
            (x-8, y),                  # Center indent
            (x-3, y+8),                # Bottom base
        ]
        draw.polygon(west_points, fill='#FFFFFF', outline='#000000')
        
        # Add small "N" label
        try:
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        except:
            label_font = ImageFont.load_default()
        
        draw.text((x, y-radius-15), "N", fill='#000000', font=label_font, anchor='mm')
    
    def _draw_scale_bar(self, draw, x: int, y: int, bbox: Dict, image_width: int):
        """Draw a professional scale bar with proper measurements in feet"""
        # Calculate real-world distance in feet (bbox is in EPSG:2226 - US Survey Feet)
        map_width_ft = abs(bbox['maxx'] - bbox['minx'])
        
        # Determine nice round number for scale bar
        # Target: 1/5 of map width for the scale bar
        target_distance = map_width_ft / 5
        
        # Round to nice numbers
        if target_distance >= 5280:  # More than a mile
            # Use miles
            miles = target_distance / 5280
            if miles >= 10:
                nice_distance = round(miles / 10) * 10
                label = f"{int(nice_distance)} mi"
                real_distance_ft = nice_distance * 5280
            elif miles >= 5:
                nice_distance = 5
                label = "5 mi"
                real_distance_ft = 26400
            elif miles >= 2:
                nice_distance = 2
                label = "2 mi"
                real_distance_ft = 10560
            else:
                nice_distance = 1
                label = "1 mi"
                real_distance_ft = 5280
        else:
            # Use feet
            if target_distance >= 1000:
                nice_distance = round(target_distance / 1000) * 1000
            elif target_distance >= 500:
                nice_distance = 500
            elif target_distance >= 200:
                nice_distance = 200
            elif target_distance >= 100:
                nice_distance = 100
            else:
                nice_distance = max(50, round(target_distance / 50) * 50)
            label = f"{int(nice_distance)} ft"
            real_distance_ft = nice_distance
        
        # Calculate bar length in pixels using actual image width (minus margins)
        usable_width = image_width - 40  # Account for 20px margins on each side
        bar_length_px = int((real_distance_ft / map_width_ft) * usable_width * 0.8)
        bar_length_px = min(bar_length_px, 250)  # Max 250px
        
        # Draw scale bar background (white with black border)
        padding = 10
        bar_height = 15
        bg_width = bar_length_px + 2*padding
        bg_height = 50
        
        # Background rectangle
        draw.rectangle([(x-padding, y-bg_height//2), (x+bg_width, y+bg_height//2)],
                      fill='#FFFFFF', outline='#000000', width=2)
        
        # Checkered scale bar (black and white segments)
        num_segments = 4
        segment_length = bar_length_px // num_segments
        
        for i in range(num_segments):
            seg_x = x + i * segment_length
            fill_color = '#000000' if i % 2 == 0 else '#FFFFFF'
            draw.rectangle([(seg_x, y-bar_height//2+5), (seg_x+segment_length, y+bar_height//2-5)],
                          fill=fill_color, outline='#000000', width=1)
        
        # Add scale label
        try:
            scale_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        except:
            scale_font = ImageFont.load_default()
        
        draw.text((x + bar_length_px//2, y+bar_height//2+12), label, 
                 fill='#000000', font=scale_font, anchor='mm')
    
    def create_export_package(self, job_id: str, params: Dict, project_id: Optional[str] = None) -> Dict:
        """
        Main export function - creates export package with selected formats.

        Args:
            job_id: Unique job identifier
            params: Export parameters including bbox, layers, formats, etc.
            project_id: Optional project ID to determine target CRS (if None, defaults to EPSG:2226)

        Returns:
            dict with status, download_url, file_size_mb, or error
        """
        try:
            # Create job directory
            job_dir = os.path.join(self.export_dir, str(job_id))
            os.makedirs(job_dir, exist_ok=True)

            # Determine target CRS from project or use default
            if project_id and self.crs_service:
                try:
                    project_crs = self.crs_service.get_project_crs(project_id, self.db_conn)
                    target_epsg = project_crs['epsg_code']
                    target_srid = int(target_epsg.split(':')[1])  # Extract numeric SRID
                    print(f"Using project CRS: {target_epsg} ({project_crs['system_name']})")
                except Exception as e:
                    print(f"Warning: Could not get project CRS: {e}. Defaulting to EPSG:2226")
                    target_epsg = 'EPSG:2226'
                    target_srid = 2226
            else:
                # Default to EPSG:2226 for backward compatibility
                target_epsg = 'EPSG:2226'
                target_srid = 2226
                print("No project_id provided or CRS service unavailable, defaulting to EPSG:2226")

            # Transform bounding box to target CRS
            source_crs = params['bbox'].get('crs', 'EPSG:3857')
            bbox_transformed = self.transform_bbox(params['bbox'], source_crs, target_epsg)

            # Storage for all layer data
            all_layers_data = {}

            # PRIORITY 1: Fetch drawing entities from database (DXF-imported layers)
            print("Fetching drawing entities from database...")
            drawing_layers = self.fetch_drawing_entities_by_layer(
                bbox_transformed,
                project_id=project_id,
                srid=target_srid
            )
            if drawing_layers:
                print(f"Found {len(drawing_layers)} drawing layers: {list(drawing_layers.keys())}")
                all_layers_data.update(drawing_layers)

            # PRIORITY 2: Fetch external WFS layers if requested
            for layer_id in params.get('layers', []):
                if layer_id not in all_layers_data:  # Don't override drawing layers
                    # External WFS layer - use placeholder for now
                    layer_config = {
                        'name': layer_id.title(),
                        'url': 'https://gis.sonomacounty.ca.gov/geoserver/wfs',
                        'layer_name': layer_id
                    }

                    # For MVP, create sample data for external layers
                    all_layers_data[layer_id] = self._create_sample_features(bbox_transformed, layer_id)

            # Export to requested formats
            exported_files = []

            if 'shp' in params.get('formats', []):
                for layer_id, features in all_layers_data.items():
                    shp_path = os.path.join(job_dir, f"{layer_id}.shp")
                    if self.export_to_shapefile(features, layer_id, shp_path, epsg_code=target_srid):
                        exported_files.extend([
                            f"{layer_id}.shp",
                            f"{layer_id}.shx",
                            f"{layer_id}.dbf",
                            f"{layer_id}.prj"
                        ])
            
            if 'dxf' in params.get('formats', []):
                dxf_path = os.path.join(job_dir, "export.dxf")
                if self.export_to_dxf(all_layers_data, dxf_path):
                    exported_files.append("export.dxf")

            if 'kml' in params.get('formats', []):
                kml_path = os.path.join(job_dir, "export.kml")
                if self.export_to_kml(all_layers_data, kml_path, source_epsg=target_epsg):
                    exported_files.append("export.kml")

            if 'png' in params.get('formats', []):
                png_opts = params.get('png_options', {})
                png_path = self.create_map_image(
                    params['bbox'],
                    north_arrow=png_opts.get('north_arrow', True),
                    scale_bar=png_opts.get('scale_bar', True)
                )
                if png_path:
                    # Move to job dir
                    import shutil
                    dest = os.path.join(job_dir, "map.png")
                    shutil.move(png_path, dest)
                    exported_files.append("map.png")
            
            # Create zip archive
            zip_path = os.path.join(job_dir, "export.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in exported_files:
                    file_path = os.path.join(job_dir, filename)
                    if os.path.exists(file_path):
                        zipf.write(file_path, filename)
            
            # Calculate file size
            file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
            
            return {
                'status': 'complete',
                'download_url': f'/api/map-export/download/{job_id}/export.zip',
                'file_size_mb': round(file_size_mb, 2),
                'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e)
            }
    
    def _create_sample_features(self, bbox: Tuple, layer_type: str) -> List[Dict]:
        """
        Create sample features for MVP demonstration.

        Args:
            bbox: Bounding box tuple (minx, miny, maxx, maxy)
            layer_type: Type of layer to create sample features for

        Returns:
            List of sample GeoJSON features
        """
        minx, miny, maxx, maxy = bbox
        
        features = []
        
        if layer_type == 'parcels':
            # Create a sample parcel polygon
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [minx + (maxx-minx)*0.1, miny + (maxy-miny)*0.1],
                        [maxx - (maxx-minx)*0.1, miny + (maxy-miny)*0.1],
                        [maxx - (maxx-minx)*0.1, maxy - (maxy-miny)*0.1],
                        [minx + (maxx-minx)*0.1, maxy - (maxy-miny)*0.1],
                        [minx + (maxx-minx)*0.1, miny + (maxy-miny)*0.1],
                    ]]
                },
                'properties': {'id': 1, 'name': 'Sample Parcel'}
            })
        
        return features
    
    def cleanup_expired_jobs(self):
        """Remove expired export files"""
        try:
            for job_folder in os.listdir(self.export_dir):
                job_path = os.path.join(self.export_dir, job_folder)
                if os.path.isdir(job_path):
                    # Check if older than 2 hours
                    created_time = os.path.getctime(job_path)
                    if (datetime.now().timestamp() - created_time) > 7200:  # 2 hours
                        import shutil
                        shutil.rmtree(job_path)
                        print(f"Cleaned up expired job: {job_folder}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
