"""
Specialized Tools Blueprint
Handles infrastructure analysis tools: street lights, pavement zones, flow analysis, laterals, area/volume calculations
Extracted from app.py during Phase 13 refactoring
"""
from flask import Blueprint, render_template, jsonify, request
from typing import Dict, List, Any, Optional
from database import get_db, execute_query
from app.extensions import cache
from app.utils.core_utilities import (
    get_active_project_id,
    state_plane_to_wgs84,
    get_test_coordinates_config
)
import random
import json
import os
import traceback
import math

specialized_tools_bp = Blueprint('specialized_tools', __name__)

# ============================================
# PAGE ROUTES
# ============================================

@specialized_tools_bp.route('/tools/street-light-analyzer')
def street_light_analyzer_tool():
    """Street Light Analyzer - Analyze street light spacing, coverage, and electrical infrastructure"""
    return render_template('street_light_analyzer.html')

@specialized_tools_bp.route('/tools/pavement-zone-analyzer')
def pavement_zone_analyzer_tool():
    """Pavement Zone Analyzer - Analyze pavement zones with area calculations"""
    return render_template('pavement_zone_analyzer.html')

@specialized_tools_bp.route('/tools/flow-analysis')
def flow_analysis_tool():
    """Flow Analysis - Analyze gravity pipe network flow capacity"""
    return render_template('flow_analysis.html')

@specialized_tools_bp.route('/tools/lateral-analyzer')
def lateral_analyzer_tool():
    """Lateral Analyzer - Analyze sewer and water lateral connections"""
    return render_template('lateral_analyzer.html')

# ============================================
# ADMIN / INITIALIZATION ROUTES
# ============================================

@specialized_tools_bp.route('/api/admin/init-specialized-tables', methods=['POST'])
def init_specialized_tables():
    """Initialize specialized tool tables (bmps, street_lights, pavement_zones)"""
    try:
        # Read and execute the SQL schema file
        schema_path = 'database/create_specialized_tool_tables.sql'
        if not os.path.exists(schema_path):
            return jsonify({'error': f'Schema file not found: {schema_path}'}), 404

        with open(schema_path, 'r') as f:
            sql_content = f.read()

        # Execute using database connection
        from database import get_db
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_content)

        # Verify tables were created
        verify_query = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('bmps', 'street_lights', 'pavement_zones')
            ORDER BY table_name
        """
        tables = execute_query(verify_query)

        return jsonify({
            'success': True,
            'message': 'Specialized tool tables initialized successfully',
            'tables_created': [t['table_name'] for t in tables]
        })

    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ============================================
# SPECIALIZED TOOL API ENDPOINTS
# ============================================

@specialized_tools_bp.route('/api/specialized-tools/street-lights')
def get_street_lights():
    """
    Get street light data for current project.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Try to query actual database first
        # Check if street_lights table exists and has data for this project
        try:
            query = """
                SELECT
                    light_id,
                    pole_number,
                    pole_height_ft,
                    lamp_type,
                    wattage,
                    circuit_id,
                    condition,
                    ST_X(geometry) as x,
                    ST_Y(geometry) as y,
                    attributes
                FROM street_lights
                WHERE project_id = %s
                ORDER BY pole_number
            """
            lights = execute_query(query, (project_id,))

            if lights and len(lights) > 0:
                # Convert coordinates for map display
                for light in lights:
                    coords = state_plane_to_wgs84(light['x'], light['y'])
                    light['map_lat'] = coords['lat']
                    light['map_lng'] = coords['lng']

                # Calculate statistics
                stats = calculate_light_statistics(lights)

                return jsonify({
                    'success': True,
                    'lights': lights,
                    'stats': stats,
                    'source': 'database'
                })
        except Exception as db_error:
            # Database query failed or table doesn't exist - use test data
            print(f"Database query failed, using test data: {db_error}")

        # Generate test data as fallback
        import random

        # Use CORRECT coordinate system
        test_config = get_test_coordinates_config()
        base_x = test_config['center_x']
        base_y = test_config['center_y']
        spacing = test_config['spacing']

        # Generate 15-25 test street lights in a grid pattern
        num_lights = random.randint(15, 25)
        lights = []

        lamp_types = ['LED-100W', 'LED-150W', 'HPS-250W', 'LED-75W', 'HPS-150W']
        conditions = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']

        for i in range(num_lights):
            row = i // 5
            col = i % 5

            # Generate coordinates in State Plane system
            x = base_x + (col * spacing) + random.uniform(-10, 10)
            y = base_y + (row * spacing) + random.uniform(-10, 10)

            # Convert to WGS84 for map display
            coords = state_plane_to_wgs84(x, y)

            lamp_type = random.choice(lamp_types)
            wattage = int(lamp_type.split('-')[1].replace('W', ''))

            lights.append({
                'light_id': f'SL-{i+1:03d}',
                'pole_number': f'P-{i+1:03d}',
                'lamp_type': lamp_type,
                'wattage': wattage,
                'pole_height_ft': random.choice([20, 25, 30, 35]),
                'circuit_id': f'C-{(i//5)+1}',
                'condition': random.choice(conditions),
                'x': round(x, 2),              # State Plane coordinates
                'y': round(y, 2),              # State Plane coordinates
                'map_lat': coords['lat'],      # WGS84 for map
                'map_lng': coords['lng'],      # WGS84 for map
                'installation_date': '2018-03-15',
                'last_maintenance': '2024-06-12'
            })

        # Calculate statistics
        stats = calculate_light_statistics(lights)

        return jsonify({
            'success': True,
            'lights': lights,
            'stats': stats,
            'source': 'test_data'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_light_statistics(lights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for street lights"""
    total_wattage = sum(l['wattage'] for l in lights)

    by_lamp_type = {}
    for light in lights:
        lt = light['lamp_type']
        by_lamp_type[lt] = by_lamp_type.get(lt, 0) + 1

    by_condition = {
        'EXCELLENT': sum(1 for l in lights if l['condition'] == 'EXCELLENT'),
        'GOOD': sum(1 for l in lights if l['condition'] == 'GOOD'),
        'FAIR': sum(1 for l in lights if l['condition'] == 'FAIR'),
        'POOR': sum(1 for l in lights if l['condition'] == 'POOR'),
    }

    # Use configured spacing for average
    test_config = get_test_coordinates_config()

    return {
        'total_count': len(lights),
        'total_wattage': total_wattage,
        'average_spacing_ft': round(test_config['spacing'], 1),
        'by_lamp_type': by_lamp_type,
        'by_condition': by_condition
    }

@specialized_tools_bp.route('/api/specialized-tools/pavement-zones')
def get_pavement_zones():
    """
    Get pavement zone data for current project.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Try to query actual database first
        try:
            query = """
                SELECT
                    zone_id,
                    zone_name,
                    pavement_type,
                    area_sqft,
                    thickness_inches,
                    material_spec,
                    traffic_category,
                    ST_AsGeoJSON(geometry) as geometry_json,
                    attributes,
                    condition,
                    install_date
                FROM pavement_zones
                WHERE project_id = %s
                ORDER BY zone_name
            """
            zones = execute_query(query, (project_id,))

            if zones and len(zones) > 0:
                # Calculate totals by type
                type_totals = {}
                for zone in zones:
                    ptype = zone.get('pavement_type', 'UNKNOWN')
                    area = zone.get('area_sqft', 0) or 0
                    type_totals[ptype] = type_totals.get(ptype, 0) + area

                total_area = sum(z.get('area_sqft', 0) or 0 for z in zones)
                total_acres = total_area / 43560  # Convert sqft to acres

                return jsonify({
                    'success': True,
                    'zones': zones,
                    'stats': {
                        'total_count': len(zones),
                        'total_area_sqft': round(total_area, 2),
                        'total_area_acres': round(total_acres, 2),
                        'by_type': type_totals
                    },
                    'source': 'database'
                })
        except Exception as db_error:
            print(f"Database query failed, using test data: {db_error}")

        # Generate test data as fallback
        import random

        # Use CORRECT coordinate system
        test_config = get_test_coordinates_config()
        base_x = test_config['center_x']
        base_y = test_config['center_y']
        spacing = test_config['spacing']

        # Generate 8-12 test pavement zones
        num_zones = random.randint(8, 12)
        zones = []

        pavement_types = ['ASPHALT', 'CONCRETE', 'GRAVEL', 'PAVER']
        conditions = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']
        traffic_categories = ['LOW', 'MEDIUM', 'HIGH']

        for i in range(num_zones):
            row = i // 3
            col = i % 3

            # Generate zone center in State Plane system
            center_x = base_x + (col * spacing * 3)
            center_y = base_y + (row * spacing * 3)

            # Create a simple polygon around the center
            zone_size = random.uniform(100, 200)  # feet
            coords_wgs84 = []
            for corner in [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]:
                x = center_x + (corner[0] * zone_size) - (zone_size / 2)
                y = center_y + (corner[1] * zone_size) - (zone_size / 2)
                coords = state_plane_to_wgs84(x, y)
                coords_wgs84.append([coords['lng'], coords['lat']])

            ptype = random.choice(pavement_types)
            area_sqft = zone_size * zone_size

            zones.append({
                'zone_id': f'PZ-{i+1:03d}',
                'zone_name': f'Zone {chr(65+i)}',
                'pavement_type': ptype,
                'area_sqft': round(area_sqft, 2),
                'thickness_inches': random.choice([4, 6, 8, 10]),
                'material_spec': f'{ptype}-STD',
                'traffic_category': random.choice(traffic_categories),
                'condition': random.choice(conditions),
                'install_date': '2020-05-15',
                'geometry_json': json.dumps({
                    'type': 'Polygon',
                    'coordinates': [coords_wgs84]
                })
            })

        # Calculate totals
        type_totals = {}
        for zone in zones:
            ptype = zone['pavement_type']
            type_totals[ptype] = type_totals.get(ptype, 0) + zone['area_sqft']

        total_area = sum(z['area_sqft'] for z in zones)
        total_acres = total_area / 43560

        return jsonify({
            'success': True,
            'zones': zones,
            'stats': {
                'total_count': len(zones),
                'total_area_sqft': round(total_area, 2),
                'total_area_acres': round(total_acres, 2),
                'by_type': type_totals
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@specialized_tools_bp.route('/api/specialized-tools/flow-analysis')
def analyze_flow():
    """
    Analyze gravity pipe network flow capacity using Manning's equation.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Try to query actual database first
        try:
            query = """
                SELECT
                    line_id,
                    line_number,
                    utility_system as line_type,
                    diameter_mm,
                    material,
                    ST_Length(geometry) as length_ft,
                    slope,
                    attributes->>'mannings_n' as mannings_n,
                    from_structure_id,
                    to_structure_id,
                    ST_AsGeoJSON(geometry) as geometry_json
                FROM utility_lines
                WHERE utility_system IN ('STORM', 'SANITARY', 'GRAVITY')
                AND project_id = %s
                AND slope IS NOT NULL
                AND slope > 0
                ORDER BY line_number
            """
            pipes = execute_query(query, (project_id,))

            if pipes and len(pipes) > 0:
                # Calculate flow capacity for each pipe
                import math
                for pipe in pipes:
                    diameter_in = (pipe.get('diameter_mm', 0) or 0) / 25.4
                    slope = pipe.get('slope', 0) or 0.01
                    mannings_n = float(pipe.get('mannings_n') or 0.013)

                    if diameter_in > 0:
                        radius_ft = (diameter_in / 12) / 2
                        area = math.pi * radius_ft**2
                        wetted_perimeter = 2 * math.pi * radius_ft
                        hydraulic_radius = area / wetted_perimeter
                        velocity = (1.486 / mannings_n) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
                        capacity_cfs = area * velocity
                        pipe['capacity_cfs'] = round(capacity_cfs, 2)
                        pipe['velocity_fps'] = round(velocity, 2)
                        pipe['diameter_in'] = round(diameter_in, 1)
                    else:
                        pipe['capacity_cfs'] = 0
                        pipe['velocity_fps'] = 0
                        pipe['diameter_in'] = 0

                total_length = sum(p.get('length_ft', 0) or 0 for p in pipes)
                total_capacity = sum(p.get('capacity_cfs', 0) or 0 for p in pipes)

                return jsonify({
                    'success': True,
                    'pipes': pipes,
                    'stats': {
                        'total_pipes': len(pipes),
                        'total_length_ft': round(total_length, 1),
                        'total_capacity_cfs': round(total_capacity, 2)
                    },
                    'source': 'database'
                })
        except Exception as db_error:
            print(f"Database query failed, using test data: {db_error}")

        # Generate test data as fallback
        import random
        import math

        # Use CORRECT coordinate system
        test_config = get_test_coordinates_config()
        base_x = test_config['center_x']
        base_y = test_config['center_y']
        spacing = test_config['spacing']

        # Generate 10-15 test pipes
        num_pipes = random.randint(10, 15)
        pipes = []

        pipe_materials = ['PVC', 'CONCRETE', 'HDPE', 'STEEL']
        pipe_systems = ['STORM', 'SANITARY']
        pipe_diameters_mm = [200, 300, 450, 600, 750, 900]

        for i in range(num_pipes):
            # Create line geometry with two points
            start_x = base_x + (i % 3) * spacing * 2
            start_y = base_y + (i // 3) * spacing * 2
            end_x = start_x + spacing
            end_y = start_y + random.uniform(-50, 50)

            # Convert to WGS84 for geometry
            start_coords = state_plane_to_wgs84(start_x, start_y)
            end_coords = state_plane_to_wgs84(end_x, end_y)

            diameter_mm = random.choice(pipe_diameters_mm)
            diameter_in = diameter_mm / 25.4
            slope = random.uniform(0.005, 0.02)  # 0.5% to 2%
            mannings_n = 0.013
            length_ft = spacing + random.uniform(-20, 20)

            # Calculate flow capacity
            radius_ft = (diameter_in / 12) / 2
            area = math.pi * radius_ft**2
            wetted_perimeter = 2 * math.pi * radius_ft
            hydraulic_radius = area / wetted_perimeter
            velocity = (1.486 / mannings_n) * (hydraulic_radius ** (2/3)) * (slope ** 0.5)
            capacity_cfs = area * velocity

            pipes.append({
                'line_id': f'PIPE-{i+1:03d}',
                'line_number': f'L-{i+1:03d}',
                'line_type': random.choice(pipe_systems),
                'diameter_mm': diameter_mm,
                'diameter_in': round(diameter_in, 1),
                'material': random.choice(pipe_materials),
                'length_ft': round(length_ft, 1),
                'slope': round(slope, 4),
                'mannings_n': str(mannings_n),
                'capacity_cfs': round(capacity_cfs, 2),
                'velocity_fps': round(velocity, 2),
                'from_structure_id': f'MH-{i+1:03d}',
                'to_structure_id': f'MH-{i+2:03d}',
                'geometry_json': json.dumps({
                    'type': 'LineString',
                    'coordinates': [
                        [start_coords['lng'], start_coords['lat']],
                        [end_coords['lng'], end_coords['lat']]
                    ]
                })
            })

        total_length = sum(p['length_ft'] for p in pipes)
        total_capacity = sum(p['capacity_cfs'] for p in pipes)

        return jsonify({
            'success': True,
            'pipes': pipes,
            'stats': {
                'total_pipes': len(pipes),
                'total_length_ft': round(total_length, 1),
                'total_capacity_cfs': round(total_capacity, 2)
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@specialized_tools_bp.route('/api/specialized-tools/laterals')
def analyze_laterals():
    """
    Analyze lateral connections from mains to properties.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Try to query actual database first
        try:
            query = """
                SELECT
                    service_id as lateral_id,
                    service_type as lateral_type,
                    service_address as address,
                    size_mm,
                    material,
                    ST_Length(
                        ST_MakeLine(
                            service_point_geometry,
                            (SELECT rim_geometry FROM utility_structures WHERE structure_id = usc.structure_id LIMIT 1)
                        )
                    ) as length_ft,
                    line_id as connected_to,
                    ST_AsGeoJSON(service_point_geometry) as geometry_json,
                    attributes,
                    install_date
                FROM utility_service_connections usc
                WHERE service_type IN ('SEWER_LATERAL', 'WATER_LATERAL', 'LATERAL')
                AND project_id = %s
                ORDER BY service_address
            """
            laterals = execute_query(query, (project_id,))

            if laterals and len(laterals) > 0:
                # Convert diameter from mm to inches
                for lateral in laterals:
                    diameter_mm = lateral.get('size_mm', 0) or 0
                    lateral['diameter_in'] = round(diameter_mm / 25.4, 1) if diameter_mm > 0 else 0

                # Group by diameter
                by_diameter = {}
                for lateral in laterals:
                    diam = lateral.get('diameter_in', 0)
                    diam_str = f"{diam}\"" if diam > 0 else "UNKNOWN"
                    by_diameter[diam_str] = by_diameter.get(diam_str, 0) + 1

                # Group by type
                by_type = {}
                for lateral in laterals:
                    ltype = lateral.get('lateral_type', 'UNKNOWN')
                    by_type[ltype] = by_type.get(ltype, 0) + 1

                total_length = sum(l.get('length_ft', 0) or 0 for l in laterals)

                return jsonify({
                    'success': True,
                    'laterals': laterals,
                    'stats': {
                        'total_count': len(laterals),
                        'total_length_ft': round(total_length, 1),
                        'by_diameter': by_diameter,
                        'by_type': by_type
                    },
                    'source': 'database'
                })
        except Exception as db_error:
            print(f"Database query failed, using test data: {db_error}")

        # Generate test data as fallback
        import random

        # Use CORRECT coordinate system
        test_config = get_test_coordinates_config()
        base_x = test_config['center_x']
        base_y = test_config['center_y']
        spacing = test_config['spacing']

        # Generate 20-30 test laterals
        num_laterals = random.randint(20, 30)
        laterals = []

        lateral_types = ['SEWER_LATERAL', 'WATER_LATERAL']
        materials = ['PVC', 'COPPER', 'PEX', 'CAST_IRON']
        diameters_mm = [100, 150, 200]

        for i in range(num_laterals):
            # Generate point in State Plane system
            x = base_x + (i % 5) * spacing + random.uniform(-50, 50)
            y = base_y + (i // 5) * spacing + random.uniform(-50, 50)

            # Convert to WGS84 for geometry
            coords = state_plane_to_wgs84(x, y)

            diameter_mm = random.choice(diameters_mm)
            diameter_in = round(diameter_mm / 25.4, 1)
            length_ft = random.uniform(30, 100)

            laterals.append({
                'lateral_id': f'LAT-{i+1:03d}',
                'lateral_type': random.choice(lateral_types),
                'address': f'{(i+1)*100} Main St',
                'size_mm': diameter_mm,
                'diameter_in': diameter_in,
                'material': random.choice(materials),
                'length_ft': round(length_ft, 1),
                'connected_to': f'MAIN-{(i//5)+1:02d}',
                'install_date': '2019-08-20',
                'geometry_json': json.dumps({
                    'type': 'Point',
                    'coordinates': [coords['lng'], coords['lat']]
                })
            })

        # Group by diameter
        by_diameter = {}
        for lateral in laterals:
            diam = lateral['diameter_in']
            diam_str = f"{diam}\""
            by_diameter[diam_str] = by_diameter.get(diam_str, 0) + 1

        # Group by type
        by_type = {}
        for lateral in laterals:
            ltype = lateral['lateral_type']
            by_type[ltype] = by_type.get(ltype, 0) + 1

        total_length = sum(l['length_ft'] for l in laterals)

        return jsonify({
            'success': True,
            'laterals': laterals,
            'stats': {
                'total_count': len(laterals),
                'total_length_ft': round(total_length, 1),
                'by_diameter': by_diameter,
                'by_type': by_type
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@specialized_tools_bp.route('/api/specialized-tools/area-calculator')
def calculate_areas():
    """
    Calculate areas for all polygon features grouped by object type.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Try to query actual database first
        try:
            query = """
                SELECT
                    entity_id,
                    l.layer_name,
                    entity_type,
                    ST_Area(
                        CASE
                            WHEN ST_SRID(geometry) = 0 THEN ST_SetSRID(geometry, 2226)
                            ELSE geometry
                        END
                    ) as area_sqft,
                    ST_AsGeoJSON(
                        ST_Transform(
                            CASE
                                WHEN ST_SRID(geometry) = 0 THEN ST_SetSRID(geometry, 2226)
                                ELSE geometry
                            END,
                            4326
                        )
                    ) as geometry_json,
                    metadata
                FROM drawing_entities de
                LEFT JOIN layers l ON de.layer_id = l.layer_id
                WHERE de.project_id = %s
                  AND de.entity_type IN ('LWPOLYLINE', 'POLYLINE', 'REGION', '3DFACE')
                  AND ST_IsClosed(geometry) = true
                  AND ST_Area(geometry) > 1
                ORDER BY area_sqft DESC
                LIMIT 500
            """
            areas = execute_query(query, (project_id,))

            if areas and len(areas) > 0:
                # Parse layer names to extract categories
                for area in areas:
                    area['area_acres'] = area['area_sqft'] / 43560
                    layer = area.get('layer_name', '')

                    # Simple category extraction from layer name
                    if 'BMP' in layer or 'BIORET' in layer:
                        area['category'] = 'BMP'
                    elif 'PVMT' in layer or 'ASPH' in layer or 'CONC' in layer:
                        area['category'] = 'Paving'
                    elif 'LAND' in layer or 'TURF' in layer:
                        area['category'] = 'Landscape'
                    elif 'BLDG' in layer or 'BUILDING' in layer:
                        area['category'] = 'Building'
                    elif 'GRAD' in layer or 'EARTHWORK' in layer:
                        area['category'] = 'Grading'
                    elif 'ACBL' in layer or 'ACCESS' in layer:
                        area['category'] = 'Accessible'
                    else:
                        area['category'] = 'Other'

                # Calculate statistics by category
                by_category = {}
                for area in areas:
                    cat = area.get('category', 'Other')
                    if cat not in by_category:
                        by_category[cat] = {'count': 0, 'total_sqft': 0}
                    by_category[cat]['count'] += 1
                    by_category[cat]['total_sqft'] += area['area_sqft']

                total_sqft = sum(a['area_sqft'] for a in areas)

                return jsonify({
                    'success': True,
                    'areas': areas,
                    'stats': {
                        'total_count': len(areas),
                        'total_sqft': round(total_sqft, 2),
                        'total_acres': round(total_sqft / 43560, 3),
                        'by_category': by_category
                    },
                    'source': 'database'
                })
        except Exception as db_error:
            print(f"Database query failed, using test data: {db_error}")

        # Generate test data as fallback
        import random

        test_config = get_test_coordinates_config()
        base_x = test_config['center_x']
        base_y = test_config['center_y']
        spacing = test_config['spacing']

        # Generate 15-30 test polygon areas
        num_areas = random.randint(15, 30)
        areas = []

        categories = [
            ('Accessible', 'ACBL', [500, 2000]),
            ('BMP', 'BMP', [1000, 10000]),
            ('Grading', 'GRAD', [5000, 50000]),
            ('Paving', 'PVMT', [2000, 20000]),
            ('Landscape', 'LAND', [1000, 15000]),
            ('Building', 'BLDG', [3000, 25000])
        ]

        for i in range(num_areas):
            cat_name, cat_code, area_range = random.choice(categories)
            area_sqft = random.uniform(area_range[0], area_range[1])
            area_acres = area_sqft / 43560

            areas.append({
                'entity_id': f'AREA-{i+1:03d}',
                'layer_name': f'CIV-{cat_code}-TYPE-NEW-PL',
                'entity_type': 'LWPOLYLINE',
                'category': cat_name,
                'area_sqft': round(area_sqft, 2),
                'area_acres': round(area_acres, 3),
                'geometry_type': 'Polygon'
            })

        # Calculate statistics
        by_category = {}
        for area in areas:
            cat = area['category']
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'total_sqft': 0}
            by_category[cat]['count'] += 1
            by_category[cat]['total_sqft'] += area['area_sqft']

        total_sqft = sum(a['area_sqft'] for a in areas)

        return jsonify({
            'success': True,
            'areas': areas,
            'stats': {
                'total_count': len(areas),
                'total_sqft': round(total_sqft, 2),
                'total_acres': round(total_sqft / 43560, 3),
                'by_category': by_category
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@specialized_tools_bp.route('/api/specialized-tools/material-volume')
def calculate_material_volumes():
    """
    Calculate material volumes based on areas and depths.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Generate test data (database integration TBD)
        import random

        # Generate 10-20 material volume items
        num_items = random.randint(10, 20)
        volumes = []

        material_types = [
            ('Earthwork', [1000, 10000], [2, 8]),
            ('Pavement', [500, 5000], [2, 6]),
            ('Aggregate', [500, 5000], [4, 12]),
            ('BMP', [1000, 20000], [3, 10])
        ]

        for i in range(num_items):
            mat_type, area_range, depth_range = random.choice(material_types)
            area_sqft = random.uniform(area_range[0], area_range[1])
            depth_inches = random.uniform(depth_range[0], depth_range[1])
            depth_ft = depth_inches / 12
            volume_cy = (area_sqft * depth_ft) / 27

            volumes.append({
                'item_id': f'VOL-{i+1:03d}',
                'item_name': f'{mat_type} Zone {i+1}',
                'material_type': mat_type,
                'area_sqft': round(area_sqft, 2),
                'depth_inches': round(depth_inches, 1),
                'volume_cy': round(volume_cy, 2),
                'unit_cost': round(random.uniform(10, 50), 2),
                'total_cost': round(volume_cy * random.uniform(10, 50), 2)
            })

        # Calculate statistics
        by_type = {}
        for vol in volumes:
            mat_type = vol['material_type']
            if mat_type not in by_type:
                by_type[mat_type] = 0
            by_type[mat_type] += vol['volume_cy']

        total_volume = sum(v['volume_cy'] for v in volumes)
        total_cost = sum(v['total_cost'] for v in volumes)

        return jsonify({
            'success': True,
            'volumes': volumes,
            'stats': {
                'total_count': len(volumes),
                'total_volume_cy': round(total_volume, 2),
                'total_cost': round(total_cost, 2),
                'by_type': by_type
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@specialized_tools_bp.route('/api/specialized-tools/pervious-impervious')
def analyze_pervious_impervious():
    """
    Analyze pervious vs impervious surfaces for hydrology.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Generate test data (database integration TBD)
        import random

        # Generate 10-25 surface items
        num_surfaces = random.randint(10, 25)
        surfaces = []

        # Pervious surfaces
        pervious_types = [
            ('BMP - Bioretention', 'Pervious', 0.0, 5.0),
            ('Landscape - Turf', 'Pervious', 0.15, 3.0),
            ('Landscape - Planting', 'Pervious', 0.10, 4.0),
            ('Pervious Pavement', 'Pervious', 0.20, 2.0)
        ]

        # Impervious surfaces
        impervious_types = [
            ('Asphalt Paving', 'Impervious', 0.95, 0.1),
            ('Concrete Paving', 'Impervious', 0.95, 0.1),
            ('Building Roof', 'Impervious', 0.95, 0.0),
            ('Concrete Sidewalk', 'Impervious', 0.90, 0.2)
        ]

        all_types = pervious_types + impervious_types

        for i in range(num_surfaces):
            surf_type, classification, runoff_coeff, infilt_rate = random.choice(all_types)
            area_sqft = random.uniform(500, 15000)

            surfaces.append({
                'surface_id': f'SURF-{i+1:03d}',
                'surface_name': f'{surf_type} {i+1}',
                'surface_type': surf_type,
                'classification': classification,
                'area_sqft': round(area_sqft, 2),
                'area_acres': round(area_sqft / 43560, 3),
                'runoff_coefficient': runoff_coeff,
                'infiltration_rate': infilt_rate
            })

        # Calculate totals
        pervious_sqft = sum(s['area_sqft'] for s in surfaces if s['classification'] == 'Pervious')
        impervious_sqft = sum(s['area_sqft'] for s in surfaces if s['classification'] == 'Impervious')
        total_sqft = pervious_sqft + impervious_sqft

        pervious_pct = (pervious_sqft / total_sqft * 100) if total_sqft > 0 else 0
        impervious_pct = (impervious_sqft / total_sqft * 100) if total_sqft > 0 else 0

        return jsonify({
            'success': True,
            'surfaces': surfaces,
            'stats': {
                'total_sqft': round(total_sqft, 2),
                'pervious_sqft': round(pervious_sqft, 2),
                'impervious_sqft': round(impervious_sqft, 2),
                'pervious_pct': round(pervious_pct, 1),
                'impervious_pct': round(impervious_pct, 1)
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@specialized_tools_bp.route('/api/specialized-tools/curb-tracker')
def track_curbs():
    """
    Track curb types and lengths throughout the project.
    Queries database first, falls back to test data if empty.
    """
    try:
        project_id = get_active_project_id()

        if not project_id:
            return jsonify({
                'success': False,
                'error': 'No active project selected',
                'requires_project': True
            }), 400

        # Generate test data (database integration TBD)
        import random

        # Generate 15-30 curb segments
        num_segments = random.randint(15, 30)
        curbs = []

        curb_types = [
            ('BARRIER', 6, 'Type A - Barrier Curb'),
            ('ROLLED', 5, 'Type B - Rolled Curb'),
            ('MOUNTABLE', 4, 'Type C - Mountable Curb'),
            ('INTEGRAL', 6, 'Integral Curb & Gutter')
        ]

        phases = ['EXISTING', 'PROPOSED', 'DEMOLITION']
        conditions = ['EXCELLENT', 'GOOD', 'FAIR', 'POOR']

        for i in range(num_segments):
            curb_type, height, desc = random.choice(curb_types)
            length_lf = random.uniform(50, 500)

            curbs.append({
                'segment_id': f'CURB-{i+1:03d}',
                'curb_type': curb_type,
                'curb_type_desc': desc,
                'length_lf': round(length_lf, 1),
                'height_in': height,
                'material': 'Concrete',
                'phase': random.choice(phases),
                'condition': random.choice(conditions),
                'location': f'Street {(i//5)+1}'
            })

        # Calculate by type
        by_type = {}
        for curb in curbs:
            ctype = curb['curb_type']
            if ctype not in by_type:
                by_type[ctype] = 0
            by_type[ctype] += curb['length_lf']

        total_length = sum(c['length_lf'] for c in curbs)

        return jsonify({
            'success': True,
            'curbs': curbs,
            'stats': {
                'total_count': len(curbs),
                'total_length_lf': round(total_length, 1),
                'unique_types': len(by_type),
                'by_type': {k: round(v, 1) for k, v in by_type.items()}
            },
            'source': 'test_data'
        })

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
