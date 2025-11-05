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


class MapExportService:
    """Service for exporting map data in various formats"""
    
    def __init__(self, export_dir: str = "/tmp/exports"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        
        # Transformer from Web Mercator (EPSG:3857) to CA State Plane Zone 2 (EPSG:2226)
        self.transformer_3857_to_2226 = Transformer.from_crs(
            "EPSG:3857", "EPSG:2226", always_xy=True
        )
        
        # Transformer from WGS84 (EPSG:4326) to CA State Plane Zone 2 (EPSG:2226)
        self.transformer_4326_to_2226 = Transformer.from_crs(
            "EPSG:4326", "EPSG:2226", always_xy=True
        )
        
        # Transformer from CA State Plane Zone 2 (EPSG:2226) to WGS84 (EPSG:4326) for KML export
        self.transformer_2226_to_4326 = Transformer.from_crs(
            "EPSG:2226", "EPSG:4326", always_xy=True
        )
    
    def transform_bbox(self, bbox: Dict, source_crs: str = "EPSG:3857") -> Tuple[float, float, float, float]:
        """Transform bounding box to EPSG:2226"""
        minx, miny, maxx, maxy = bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy']
        
        if source_crs == "EPSG:3857":
            transformer = self.transformer_3857_to_2226
        elif source_crs == "EPSG:4326":
            transformer = self.transformer_4326_to_2226
        else:
            raise ValueError(f"Unsupported source CRS: {source_crs}")
        
        minx_ft, miny_ft = transformer.transform(minx, miny)
        maxx_ft, maxy_ft = transformer.transform(maxx, maxy)
        
        return (minx_ft, miny_ft, maxx_ft, maxy_ft)
    
    def fetch_wfs_data(self, layer_config: Dict, bbox_2226: Tuple) -> Dict:
        """Fetch data from WFS service"""
        try:
            wfs = WebFeatureService(url=layer_config['url'], version='2.0.0', timeout=30)
            
            response = wfs.getfeature(
                typename=layer_config['layer_name'],
                bbox=bbox_2226,
                srsname='EPSG:2226',
                outputFormat='application/json'
            )
            
            geojson_data = json.loads(response.read())
            return geojson_data
            
        except Exception as e:
            print(f"Error fetching WFS data for {layer_config['name']}: {e}")
            return {"type": "FeatureCollection", "features": []}
    
    def clip_features(self, geojson: Dict, bbox_2226: Tuple) -> List[Dict]:
        """Clip features to bounding box"""
        bbox_poly = box(*bbox_2226)
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
    
    def export_to_shapefile(self, features: List[Dict], layer_name: str, output_path: str) -> bool:
        """Export features to Shapefile format"""
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
                crs=from_epsg(2226),
                schema=schema
            ) as shp:
                for feature in features:
                    shp.write(feature)
            
            # Write .prj file manually for better compatibility
            prj_path = output_path.replace('.shp', '.prj')
            with open(prj_path, 'w') as prj:
                # WKT for EPSG:2226
                prj.write('PROJCS["NAD83 / California zone 2 (ftUS)",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","6269"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4269"]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",39.83333333333334],PARAMETER["standard_parallel_2",38.33333333333334],PARAMETER["latitude_of_origin",37.66666666666666],PARAMETER["central_meridian",-122],PARAMETER["false_easting",6561666.667],PARAMETER["false_northing",1640416.667],UNIT["US survey foot",0.3048006096012192,AUTHORITY["EPSG","9003"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","2226"]]')
            
            return True
            
        except Exception as e:
            print(f"Error exporting shapefile: {e}")
            return False
    
    def export_to_dxf(self, layers_data: Dict[str, List[Dict]], output_path: str) -> bool:
        """Export features to DXF format"""
        try:
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            for layer_name, features in layers_data.items():
                # Create layer
                doc.layers.new(name=layer_name)
                
                for feature in features:
                    geom = shape(feature['geometry'])
                    
                    if geom.geom_type == 'Polygon':
                        points = list(geom.exterior.coords)
                        msp.add_lwpolyline(
                            points,
                            dxfattribs={'layer': layer_name, 'closed': True}
                        )
                    elif geom.geom_type == 'MultiPolygon':
                        for poly in geom.geoms:
                            points = list(poly.exterior.coords)
                            msp.add_lwpolyline(
                                points,
                                dxfattribs={'layer': layer_name, 'closed': True}
                            )
                    elif geom.geom_type == 'LineString':
                        points = list(geom.coords)
                        msp.add_lwpolyline(
                            points,
                            dxfattribs={'layer': layer_name}
                        )
                    elif geom.geom_type == 'MultiLineString':
                        for line in geom.geoms:
                            points = list(line.coords)
                            msp.add_lwpolyline(
                                points,
                                dxfattribs={'layer': layer_name}
                            )
                    elif geom.geom_type == 'Point':
                        msp.add_point(
                            (geom.x, geom.y),
                            dxfattribs={'layer': layer_name}
                        )
                    elif geom.geom_type == 'MultiPoint':
                        for point in geom.geoms:
                            msp.add_point(
                                (point.x, point.y),
                                dxfattribs={'layer': layer_name}
                            )
            
            doc.saveas(output_path)
            return True
            
        except Exception as e:
            print(f"Error exporting DXF: {e}")
            return False
    
    def export_to_kml(self, layers_data: Dict[str, List[Dict]], output_path: str) -> bool:
        """Export features to KML format (Google Earth/Maps compatible)"""
        try:
            # Transform features from EPSG:2226 to WGS84 (EPSG:4326) for KML
            layers_wgs84 = {}
            
            for layer_name, features in layers_data.items():
                transformed_features = []
                
                for feature in features:
                    try:
                        # Transform geometry to WGS84
                        geom = shape(feature['geometry'])
                        
                        def transform_coords(x, y, z=None):
                            lon, lat = self.transformer_2226_to_4326.transform(x, y)
                            return (lon, lat) if z is None else (lon, lat, z)
                        
                        transformed_geom = transform(transform_coords, geom)
                        
                        # Create new feature with transformed geometry
                        transformed_feature = {
                            'type': 'Feature',
                            'geometry': mapping(transformed_geom),
                            'properties': feature.get('properties', {})
                        }
                        transformed_features.append(transformed_feature)
                    
                    except Exception as e:
                        print(f"Error transforming feature for KML: {e}")
                        continue
                
                if transformed_features:
                    layers_wgs84[layer_name] = transformed_features
            
            # Determine geometry type from first feature
            all_features = []
            for features in layers_wgs84.values():
                all_features.extend(features)
            
            if not all_features:
                print("No features to export to KML")
                return False
            
            first_geom = shape(all_features[0]['geometry'])
            geom_type = first_geom.geom_type
            
            # Map geometry types to KML-compatible types
            kml_geom_type = geom_type
            if geom_type == 'MultiPolygon':
                kml_geom_type = 'Polygon'
            elif geom_type == 'MultiLineString':
                kml_geom_type = 'LineString'
            elif geom_type == 'MultiPoint':
                kml_geom_type = 'Point'
            
            # Build schema
            properties = all_features[0].get('properties', {})
            schema_props = {}
            for key, value in properties.items():
                if isinstance(value, int):
                    schema_props[key] = 'int'
                elif isinstance(value, float):
                    schema_props[key] = 'float'
                else:
                    schema_props[key] = 'str'
            
            schema = {
                'geometry': kml_geom_type,
                'properties': schema_props if schema_props else {'id': 'str'}
            }
            
            # Write KML file using fiona
            with fiona.open(
                output_path,
                'w',
                driver='KML',
                crs=from_epsg(4326),
                schema=schema
            ) as kml:
                for feature in all_features:
                    try:
                        geom = shape(feature['geometry'])
                        
                        # Handle Multi* geometries by writing individual parts
                        if geom.geom_type.startswith('Multi'):
                            for sub_geom in geom.geoms:
                                kml.write({
                                    'type': 'Feature',
                                    'geometry': mapping(sub_geom),
                                    'properties': feature.get('properties', {})
                                })
                        else:
                            kml.write(feature)
                    except Exception as e:
                        print(f"Error writing KML feature: {e}")
                        continue
            
            return True
            
        except Exception as e:
            print(f"Error exporting KML: {e}")
            return False
    
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
    
    def create_export_package(self, job_id: str, params: Dict) -> Dict:
        """
        Main export function - creates export package with selected formats
        Returns: dict with status, download_url, file_size_mb, or error
        """
        try:
            # Create job directory
            job_dir = os.path.join(self.export_dir, str(job_id))
            os.makedirs(job_dir, exist_ok=True)
            
            # Transform bounding box to EPSG:2226
            source_crs = params['bbox'].get('crs', 'EPSG:3857')
            bbox_2226 = self.transform_bbox(params['bbox'], source_crs)
            
            # Storage for all layer data
            all_layers_data = {}
            
            # Fetch and clip data for each requested layer
            for layer_id in params.get('layers', []):
                # In MVP, we'll use placeholder data
                # In production, this would fetch from WFS
                layer_config = {
                    'name': layer_id.title(),
                    'url': 'https://gis.sonomacounty.ca.gov/geoserver/wfs',
                    'layer_name': layer_id
                }
                
                # For MVP, create sample data
                all_layers_data[layer_id] = self._create_sample_features(bbox_2226, layer_id)
            
            # Export to requested formats
            exported_files = []
            
            if 'shp' in params.get('formats', []):
                for layer_id, features in all_layers_data.items():
                    shp_path = os.path.join(job_dir, f"{layer_id}.shp")
                    if self.export_to_shapefile(features, layer_id, shp_path):
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
    
    def _create_sample_features(self, bbox_2226: Tuple, layer_type: str) -> List[Dict]:
        """Create sample features for MVP demonstration"""
        minx, miny, maxx, maxy = bbox_2226
        
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
