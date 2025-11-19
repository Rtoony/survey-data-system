"""
GIS Engine Blueprint
Handles all DXF/CAD operations, Map Export, Coordinate Systems, and Spatial Utilities
"""
from flask import Blueprint, render_template, jsonify, request, send_file, make_response, redirect
from werkzeug.utils import secure_filename
import os
import uuid
import json
from psycopg2.extras import RealDictCursor

from database import get_db, execute_query
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter
from map_export_service import MapExportService


# Create Blueprint
gis_bp = Blueprint('gis', __name__)

# Initialize MapExportService at module level
map_export = MapExportService()


# ============================================
# DXF IMPORT/EXPORT
# ============================================

@gis_bp.route('/dxf-tools')
def dxf_tools_page():
    """DXF Import/Export tools page"""
    return render_template('dxf_tools.html')


@gis_bp.route('/api/dxf/import', methods=['POST'])
def import_dxf():
    """Import DXF file into database - with optional pattern-based classification"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'No file uploaded'}), 400

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400

        # Get parameters
        project_id = request.form.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        import_modelspace = request.form.get('import_modelspace', 'true') == 'true'
        pattern_id = request.form.get('pattern_id')  # Optional import pattern

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)

        try:
            # Enable intelligent object creation when pattern_id is provided
            # or by default to enable automatic layer-based classification
            use_intelligent = True  # Enable by default for automatic classification

            # Import DXF with intelligent object creation enabled
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=use_intelligent)
            stats = importer.import_dxf(
                temp_path,
                project_id,
                import_modelspace=import_modelspace
            )

            # Add pattern matching info if pattern was selected
            pattern_info = None
            if pattern_id and use_intelligent:
                # Get selected pattern details
                pattern_query = "SELECT client_name, source_pattern, confidence_score FROM import_mapping_patterns WHERE mapping_id = %s"
                pattern_result = execute_query(pattern_query, (pattern_id,))

                if pattern_result:
                    pattern = pattern_result[0]
                    # Get actual stats from import
                    total_layers = len(stats.get('layers', set()))
                    matched = stats.get('intelligent_objects_created', 0)

                    pattern_info = {
                        'pattern_name': f"{pattern['client_name']} - {pattern['source_pattern']}",
                        'matched_count': matched,
                        'unmatched_count': max(0, total_layers - (1 if matched > 0 else 0)),
                        'avg_confidence': pattern['confidence_score'],
                        'note': 'Using automatic pattern detection with intelligent object creation'
                    }

            response_data = {
                'success': len(stats['errors']) == 0,
                'stats': stats
            }

            if pattern_info:
                response_data['pattern_info'] = pattern_info

            return jsonify(response_data)

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/dxf/export', methods=['POST'])
def export_dxf():
    """Export project to DXF file"""
    try:
        data = request.get_json()

        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        dxf_version = data.get('dxf_version', 'AC1027')
        include_modelspace = data.get('include_modelspace', True)
        layer_filter = data.get('layer_filter')

        # Generate output file
        output_filename = f'project_{project_id}_{uuid.uuid4().hex[:8]}.dxf'
        output_path = os.path.join('/tmp', output_filename)

        # Export DXF
        exporter = DXFExporter(DB_CONFIG)
        stats = exporter.export_dxf(
            project_id,
            output_path,
            dxf_version=dxf_version,
            include_modelspace=include_modelspace,
            layer_filter=layer_filter
        )

        if not os.path.exists(output_path):
            return jsonify({'error': 'Export failed - file not created'}), 500

        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/dxf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/dxf/export-jobs', methods=['GET'])
def get_export_jobs():
    """Get export job history from map export jobs table"""
    try:
        query = """
            SELECT
                ej.id as export_job_id,
                ej.params->>'project_id' as project_id,
                p.project_name,
                ej.params->>'export_format' as export_format,
                ej.params->>'dxf_version' as dxf_version,
                ej.status,
                ej.params->>'metrics' as metrics,
                ej.created_at as started_at,
                ej.expires_at as completed_at,
                ej.download_url,
                ej.file_size_mb,
                ej.error_message
            FROM export_jobs ej
            LEFT JOIN projects p ON (ej.params->>'project_id')::uuid = p.project_id
            ORDER BY ej.created_at DESC
            LIMIT 50
        """

        jobs = execute_query(query)
        return jsonify({'jobs': jobs})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# INTELLIGENT DXF WORKFLOW API
# ============================================

@gis_bp.route('/api/dxf/import-intelligent', methods=['POST'])
def import_intelligent_dxf():
    """Import DXF file with intelligent object creation from layer patterns"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'No file uploaded'}), 400

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400

        # Get parameters
        project_id = request.form.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        import_modelspace = request.form.get('import_modelspace', 'true') == 'true'

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)

        try:
            # Import DXF with intelligent object creation enabled
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=True)
            stats = importer.import_dxf(
                temp_path,
                project_id,
                import_modelspace=import_modelspace
            )

            return jsonify({
                'success': len(stats['errors']) == 0,
                'stats': stats,
                'message': f"Imported {stats.get('entities', 0)} entities and created {stats.get('intelligent_objects_created', 0)} intelligent objects"
            })

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/dxf/export-intelligent', methods=['POST'])
def export_intelligent_dxf():
    """Export intelligent objects from a project to DXF file with proper layer names"""
    try:
        data = request.get_json()

        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        include_types = data.get('include_types')  # Optional filter

        # Generate output file
        output_filename = f'project_{project_id}_{uuid.uuid4().hex[:8]}.dxf'
        output_path = os.path.join('/tmp', output_filename)

        # Export intelligent objects
        exporter = DXFExporter(DB_CONFIG)
        stats = exporter.export_intelligent_objects_to_dxf(
            project_id,
            output_path,
            include_types=include_types
        )

        if not os.path.exists(output_path):
            return jsonify({'error': 'Export failed - file not created'}), 500

        # Send file for download
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/dxf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/dxf/reimport', methods=['POST'])
def reimport_dxf_with_changes():
    """Re-import a DXF file and detect/merge changes to intelligent objects"""
    try:
        from dxf_change_detector import DXFChangeDetector

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'No file uploaded'}), 400

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.dxf'):
            return jsonify({'error': 'File must be a DXF file'}), 400

        # Get parameters
        project_id = request.form.get('project_id')
        if not project_id:
            return jsonify({'error': 'project_id is required'}), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('/tmp', f'{uuid.uuid4()}_{filename}')
        file.save(temp_path)

        try:
            # Step 1: Import DXF entities (without creating new intelligent objects yet)
            importer = DXFImporter(DB_CONFIG, create_intelligent_objects=False)
            import_stats = importer.import_dxf(
                temp_path,
                project_id,
                import_modelspace=True
            )

            # Step 2: Get the reimported entities from database (recent imports only)
            # Use a 10-minute window to capture just the entities from this import
            with get_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT entity_id, layer_name, entity_type,
                               ST_AsText(geometry) as wkt_geom,
                               attributes
                        FROM drawing_entities
                        WHERE project_id = %s
                        AND created_at >= NOW() - INTERVAL '10 minutes'
                    """, (project_id,))
                    new_entities = cur.fetchall()

            # Step 3: Run change detection
            detector = DXFChangeDetector(DB_CONFIG)
            change_report = detector.detect_changes(project_id, new_entities)

            return jsonify({
                'success': True,
                'import_stats': import_stats,
                'changes': change_report,
                'message': f"Detected {len(change_report.get('added', []))} new, {len(change_report.get('modified', []))} modified, {len(change_report.get('deleted', []))} deleted"
            })

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# MAP VIEWER PAGES & API
# ============================================

@gis_bp.route('/map-viewer')
def map_viewer_page():
    """Redirect to uncached map viewer"""
    return redirect('/map-viewer-v2', code=302)


@gis_bp.route('/map-viewer-v2')
def map_viewer_v2_page():
    """Map Viewer Page V2 - Enhanced Version"""
    import time
    response = make_response(render_template('map_viewer.html', cache_bust=int(time.time())))
    response.headers['Cache-Control'] = 'private, no-cache, no-store, must-revalidate, max-age=0, s-maxage=0'
    response.headers['Surrogate-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Accel-Expires'] = '0'
    return response


@gis_bp.route('/map-test')
def map_test_page():
    """Simple Map Test Page (no base template)"""
    return render_template('map_viewer_simple.html')


@gis_bp.route('/api/map-viewer/layers')
def get_gis_layers():
    """Get available GIS layers (external Sonoma County layers)"""
    try:
        query = "SELECT * FROM gis_layers WHERE enabled = true ORDER BY name"
        layers = execute_query(query)
        return jsonify({'layers': layers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/database-layers')
def get_database_layers():
    """Get available database layers (user's PostGIS data) - optionally filtered by CAD standards"""
    try:
        # Get filter parameters from query string
        disciplines = request.args.getlist('disciplines')
        categories = request.args.getlist('categories')
        phases = request.args.getlist('phases')

        has_filters = len(disciplines) > 0 or len(categories) > 0 or len(phases) > 0

        # Define the database layers that contain geospatial data
        db_layers = [
            {
                'id': 'survey_points',
                'name': 'Survey Points',
                'table': 'survey_points',
                'geom_column': 'geometry',
                'geom_type': 'Point',
                'enabled': True,
                'description': 'Survey control points and topo shots',
                'has_layer_name': True
            },
            {
                'id': 'utility_lines',
                'name': 'Utility Lines',
                'table': 'utility_lines',
                'geom_column': 'geometry',
                'geom_type': 'LineString',
                'enabled': True,
                'description': 'Water, sewer, storm, electric, gas lines',
                'has_layer_name': True
            },
            {
                'id': 'utility_structures',
                'name': 'Utility Structures',
                'table': 'utility_structures',
                'geom_column': 'geometry',
                'geom_type': 'Point',
                'enabled': True,
                'description': 'Manholes, valves, meters, structures',
                'has_layer_name': True
            },
            {
                'id': 'parcels',
                'name': 'Parcels',
                'table': 'parcels',
                'geom_column': 'geometry',
                'geom_type': 'Polygon',
                'enabled': True,
                'description': 'Property parcel boundaries',
                'has_layer_name': False
            },
            {
                'id': 'horizontal_alignments',
                'name': 'Alignments',
                'table': 'horizontal_alignments',
                'geom_column': 'geometry',
                'geom_type': 'LineString',
                'enabled': True,
                'description': 'Horizontal centerline alignments',
                'has_layer_name': True
            },
            {
                'id': 'surface_features',
                'name': 'Surface Features',
                'table': 'surface_features',
                'geom_column': 'geometry',
                'geom_type': 'Mixed',
                'enabled': True,
                'description': 'General site features (points, lines, polygons)',
                'has_layer_name': True
            },
            {
                'id': 'drawing_entities',
                'name': 'CAD Entities',
                'table': 'drawing_entities',
                'geom_column': 'geometry',
                'geom_type': 'Mixed',
                'enabled': True,
                'description': 'Lines, polylines, arcs, circles from CAD drawings',
                'has_layer_name': True
            }
        ]

        # Check which tables actually exist and have data
        available_layers = []
        for layer in db_layers:
            try:
                # Build count query with optional standards filter
                if has_filters and layer.get('has_layer_name'):
                    # Check if table has layer_name column and filter by standards
                    filter_conditions = []
                    if disciplines:
                        disc_pattern = '|'.join([f'^{d}-' for d in disciplines])
                        filter_conditions.append(f"layer_name ~ '{disc_pattern}'")
                    if categories:
                        cat_pattern = '|'.join([f'-{c}-' for c in categories])
                        filter_conditions.append(f"layer_name ~ '{cat_pattern}'")
                    if phases:
                        phase_pattern = '|'.join([f'-{p}-' for p in phases])
                        filter_conditions.append(f"layer_name ~ '{phase_pattern}'")

                    where_clause = " OR ".join(filter_conditions) if filter_conditions else "1=1"
                    count_query = f"SELECT COUNT(*) as count FROM {layer['table']} WHERE {where_clause}"
                else:
                    count_query = f"SELECT COUNT(*) as count FROM {layer['table']}"

                result = execute_query(count_query)
                if result and result[0]['count'] > 0:
                    layer['feature_count'] = result[0]['count']
                    available_layers.append(layer)
            except Exception as e:
                # Table doesn't exist or error checking - skip it
                print(f"Skipping layer {layer['id']}: {e}")
                continue

        return jsonify({'layers': available_layers})
    except Exception as e:
        print(f"Error getting database layers: {e}")
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/layer-data/<layer_id>')
def get_layer_data(layer_id: str):
    """Fetch GIS layer data from FeatureServer and convert to GeoJSON"""
    try:
        import requests
        from arcgis2geojson import arcgis2geojson

        # Get layer config
        query = "SELECT * FROM gis_layers WHERE id = %s AND enabled = true"
        layers = execute_query(query, (layer_id,))

        if not layers:
            return jsonify({'error': 'Layer not found'}), 404

        layer_config = layers[0]

        # Get bbox from request params
        minx = request.args.get('minx', type=float)
        miny = request.args.get('miny', type=float)
        maxx = request.args.get('maxx', type=float)
        maxy = request.args.get('maxy', type=float)

        if not all([minx, miny, maxx, maxy]):
            return jsonify({'error': 'Missing bbox parameters'}), 400

        # Query FeatureServer with ESRI JSON format
        query_url = f"{layer_config['url']}/query"
        query_params = {
            'where': '1=1',
            'geometry': f'{minx},{miny},{maxx},{maxy}',
            'geometryType': 'esriGeometryEnvelope',
            'inSR': '4326',
            'outSR': '4326',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': '*',
            'returnGeometry': 'true',
            'resultRecordCount': '1000',
            'f': 'json'  # ESRI JSON format
        }

        response = requests.get(query_url, params=query_params, timeout=30)
        response.raise_for_status()
        esri_data = response.json()

        # Convert ESRI JSON to GeoJSON
        features = []
        for esri_feature in esri_data.get('features', []):
            try:
                geojson_feature = arcgis2geojson(esri_feature)
                if geojson_feature.get('geometry') is not None:
                    features.append(geojson_feature)
            except Exception as e:
                print(f"Failed to convert feature: {e}")
                continue

        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })

    except Exception as e:
        print(f"Error fetching layer data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/database-layer-data/<layer_id>')
def get_database_layer_data(layer_id: str):
    """Fetch database layer data from PostGIS tables"""
    try:
        # Map layer IDs to table and geometry column
        layer_map = {
            'survey_points': ('survey_points', 'geometry', 'Point'),
            'utility_lines': ('utility_lines', 'geometry', 'LineString'),
            'utility_structures': ('utility_structures', 'geometry', 'Point'),
            'parcels': ('parcels', 'geometry', 'Polygon'),
            'horizontal_alignments': ('horizontal_alignments', 'geometry', 'LineString'),
            'surface_features': ('surface_features', 'geometry', 'Mixed'),
            'drawing_entities': ('drawing_entities', 'geometry', 'Mixed')
        }

        if layer_id not in layer_map:
            return jsonify({'error': 'Invalid layer ID'}), 400

        table_name, geom_column, geom_type = layer_map[layer_id]

        # Get bbox from request params (WGS84)
        minx = request.args.get('minx', type=float)
        miny = request.args.get('miny', type=float)
        maxx = request.args.get('maxx', type=float)
        maxy = request.args.get('maxy', type=float)

        if not all([minx, miny, maxx, maxy]):
            return jsonify({'error': 'Missing bbox parameters'}), 400

        # Transform bbox from WGS84 to EPSG:2226 for PostGIS query
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2226", always_xy=True)
        min_x_2226, min_y_2226 = transformer.transform(minx, miny)
        max_x_2226, max_y_2226 = transformer.transform(maxx, maxy)

        # Build query to fetch features within bbox (data in EPSG:2226, transformed to WGS84 for output)
        # Get all columns except the geometry column to avoid conflicts
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    AND column_name != '{geom_column}'
                """)
                columns = [row[0] for row in cur.fetchall()]

        columns_str = ', '.join(columns)
        query = f"""
            SELECT
                ST_AsGeoJSON(ST_Transform({geom_column}, 4326)) as geometry_json,
                {columns_str}
            FROM {table_name}
            WHERE {geom_column} && ST_MakeEnvelope(%s, %s, %s, %s, 2226)
            LIMIT 1000
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (min_x_2226, min_y_2226, max_x_2226, max_y_2226))
                rows = cur.fetchall()

        # Convert to GeoJSON features
        features = []
        for row in rows:
            geom_json = json.loads(row['geometry_json'])

            # Build properties (exclude geometry_json column)
            properties = {}
            for key, value in row.items():
                if key != 'geometry_json':
                    # Convert datetime/UUID/etc to string
                    if hasattr(value, 'isoformat'):
                        properties[key] = value.isoformat()
                    elif value is None:
                        continue
                    else:
                        properties[key] = str(value)

            features.append({
                'type': 'Feature',
                'geometry': geom_json,
                'properties': properties
            })

        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })

    except Exception as e:
        print(f"Error fetching database layer data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/projects')
def get_map_projects():
    """Get all projects with spatial data for map display (computed from entity bounding boxes)"""
    try:
        from pyproj import Transformer

        # Query all projects with computed bounding boxes from entities
        query = """
            SELECT
                p.project_id,
                p.project_name,
                p.project_number,
                p.client_name,
                p.created_at,
                ST_XMin(ST_Extent(de.geometry)) as bbox_min_x,
                ST_YMin(ST_Extent(de.geometry)) as bbox_min_y,
                ST_XMax(ST_Extent(de.geometry)) as bbox_max_x,
                ST_YMax(ST_Extent(de.geometry)) as bbox_max_y,
                COUNT(de.entity_id) as entity_count
            FROM projects p
            LEFT JOIN drawing_entities de ON de.project_id = p.project_id
            GROUP BY p.project_id, p.project_name, p.project_number, p.client_name, p.created_at
            HAVING ST_XMin(ST_Extent(de.geometry)) IS NOT NULL
            ORDER BY p.created_at DESC
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                projects = cur.fetchall()

        # Transformer to convert EPSG:2226 to WGS84 for map display
        transformer = Transformer.from_crs("EPSG:2226", "EPSG:4326", always_xy=True)

        features = []
        for project in projects:
            # Get bbox in EPSG:2226 (State Plane)
            min_x_2226 = project['bbox_min_x']
            min_y_2226 = project['bbox_min_y']
            max_x_2226 = project['bbox_max_x']
            max_y_2226 = project['bbox_max_y']

            # Transform all 4 corners to WGS84
            min_lon, min_lat = transformer.transform(min_x_2226, min_y_2226)
            max_lon, max_lat = transformer.transform(max_x_2226, max_y_2226)

            # Also transform the other two corners for accurate bbox
            top_left_lon, top_left_lat = transformer.transform(min_x_2226, max_y_2226)
            bottom_right_lon, bottom_right_lat = transformer.transform(max_x_2226, min_y_2226)

            # Create GeoJSON polygon in WGS84 (lon, lat order for GeoJSON)
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [min_lon, min_lat],              # Bottom-left
                        [bottom_right_lon, bottom_right_lat],  # Bottom-right
                        [max_lon, max_lat],              # Top-right
                        [top_left_lon, top_left_lat],    # Top-left
                        [min_lon, min_lat]               # Close the ring
                    ]]
                },
                'properties': {
                    'project_id': str(project['project_id']),
                    'project_name': project['project_name'],
                    'project_number': project['project_number'],
                    'client_name': project['client_name'],
                    'entity_count': project['entity_count'],
                    'epsg_code': 'EPSG:2226',
                    'created_at': project['created_at'].isoformat() if project['created_at'] else None
                }
            }
            features.append(feature)

        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })
    except Exception as e:
        print(f"Error fetching projects: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/project-structure')
def get_project_structure():
    """Get all projects with entity counts and bounding boxes (project-only architecture)"""
    try:
        # Query all projects with their entity counts and calculated bounding boxes
        query = """
            SELECT
                p.project_id,
                p.project_name,
                p.client_name,
                p.description,
                -- Calculate bbox from project's drawing_entities
                (SELECT ST_XMin(ST_Extent(geometry))
                 FROM drawing_entities
                 WHERE project_id = p.project_id AND geometry IS NOT NULL) as bbox_min_x,
                (SELECT ST_YMin(ST_Extent(geometry))
                 FROM drawing_entities
                 WHERE project_id = p.project_id AND geometry IS NOT NULL) as bbox_min_y,
                (SELECT ST_XMax(ST_Extent(geometry))
                 FROM drawing_entities
                 WHERE project_id = p.project_id AND geometry IS NOT NULL) as bbox_max_x,
                (SELECT ST_YMax(ST_Extent(geometry))
                 FROM drawing_entities
                 WHERE project_id = p.project_id AND geometry IS NOT NULL) as bbox_max_y,
                (SELECT COUNT(*)
                 FROM drawing_entities
                 WHERE project_id = p.project_id) as entity_count
            FROM projects p
            ORDER BY p.created_at DESC, p.project_name
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                rows = cur.fetchall()

        # Group by project
        projects = {}
        for row in rows:
            project_id = str(row['project_id'])

            bbox_min_x = row['bbox_min_x']
            bbox_min_y = row['bbox_min_y']
            bbox_max_x = row['bbox_max_x']
            bbox_max_y = row['bbox_max_y']

            if project_id not in projects:
                projects[project_id] = {
                    'project_id': project_id,
                    'project_name': row['project_name'],
                    'client_name': row['client_name'],
                    'description': row['description'],
                    'bbox': {
                        'min_x': bbox_min_x,
                        'min_y': bbox_min_y,
                        'max_x': bbox_max_x,
                        'max_y': bbox_max_y
                    } if bbox_min_x is not None else None
                }

        return jsonify({'projects': list(projects.values())})

    except Exception as e:
        print(f"Error fetching project structure: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/project-entities/<project_id>')
def get_project_entities_map(project_id: str):
    """Get project entities as GeoJSON for map display"""
    try:
        from pyproj import Transformer

        # Get all drawing entities for this project
        query = """
            SELECT
                entity_id,
                entity_type,
                layer_name,
                color_aci,
                linetype,
                lineweight,
                ST_AsText(geometry) as wkt_geometry,
                attributes
            FROM drawing_entities
            WHERE project_id = %s
            AND geometry IS NOT NULL
            LIMIT 5000
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (project_id,))
                entities = cur.fetchall()

        # Transform to WGS84 for map display
        transformer = Transformer.from_crs("EPSG:2226", "EPSG:4326", always_xy=True)

        # Convert to GeoJSON (simplified - just return WKT for now)
        features = []
        for entity in entities:
            # Basic feature structure
            feature = {
                'type': 'Feature',
                'properties': {
                    'entity_id': str(entity['entity_id']),
                    'entity_type': entity['entity_type'],
                    'layer_name': entity['layer_name'],
                    'color_aci': entity['color_aci'],
                    'linetype': entity['linetype'] or 'Continuous',
                    'lineweight': entity['lineweight'] or 0
                }
            }
            # Note: WKT to GeoJSON conversion would happen here in production
            features.append(feature)

        return jsonify({
            'type': 'FeatureCollection',
            'features': features,
            'count': len(features)
        })

    except Exception as e:
        print(f"Error fetching project entities: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/project-layers/<project_id>')
def get_project_layers(project_id: str):
    """Get unique layer names for a project"""
    try:
        query = """
            SELECT DISTINCT layer_name, COUNT(*) as entity_count
            FROM drawing_entities
            WHERE project_id = %s
            GROUP BY layer_name
            ORDER BY layer_name
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (project_id,))
                layers = cur.fetchall()

        return jsonify({'layers': layers})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-viewer/project-extent/<project_id>')
def get_project_extent(project_id: str):
    """Get bounding box extent for a project in WGS84"""
    try:
        from pyproj import Transformer

        query = """
            SELECT
                ST_XMin(ST_Extent(geometry)) as min_x,
                ST_YMin(ST_Extent(geometry)) as min_y,
                ST_XMax(ST_Extent(geometry)) as max_x,
                ST_YMax(ST_Extent(geometry)) as max_y
            FROM drawing_entities
            WHERE project_id = %s
            AND geometry IS NOT NULL
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (project_id,))
                result = cur.fetchone()

        if not result or result['min_x'] is None:
            return jsonify({'error': 'No spatial data for project'}), 404

        # Transform from EPSG:2226 to WGS84
        transformer = Transformer.from_crs("EPSG:2226", "EPSG:4326", always_xy=True)

        min_lon, min_lat = transformer.transform(result['min_x'], result['min_y'])
        max_lon, max_lat = transformer.transform(result['max_x'], result['max_y'])

        return jsonify({
            'bbox': {
                'min_lon': min_lon,
                'min_lat': min_lat,
                'max_lon': max_lon,
                'max_lat': max_lat
            },
            'epsg': '4326'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# MAP EXPORT API
# ============================================

@gis_bp.route('/api/map-export/create-simple', methods=['POST'])
def create_simple_export():
    """Create shapefile with real GIS data from Sonoma County"""
    try:
        import requests
        from shapely.geometry import shape, box
        from shapely import geometry as geom_lib
        from pyproj import Transformer
        import fiona
        from fiona.crs import from_epsg

        params = request.json
        bbox = params.get('bbox', {})
        requested_layers = params.get('layers', ['parcels', 'buildings', 'roads'])

        print(f"Creating export for bbox: {bbox}")
        print(f"Requested layers: {requested_layers}")

        # Create unique ID for this export
        export_id = str(uuid.uuid4())
        export_dir = os.path.join('/tmp/exports', export_id)
        os.makedirs(export_dir, exist_ok=True)

        # Get bounding box in WGS84
        minx, miny, maxx, maxy = bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy']

        # Coordinate transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2226", always_xy=True)

        # Get GIS layer configurations from database
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM gis_layers WHERE enabled = true AND id = ANY(%s)", (requested_layers,))
                layers = cur.fetchall()

        print(f"Found {len(layers)} layers in database matching requested layers")
        if len(layers) == 0:
            print(f"WARNING: No layers found! Requested: {requested_layers}")
            print("Checking all available layers...")
            with get_db() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT id, name, enabled FROM gis_layers")
                    all_layers = cur.fetchall()
                    print(f"All layers in DB: {all_layers}")

        feature_counts = {}

        # Fetch and export each layer
        for layer_config in layers:
            layer_id = layer_config['id']
            layer_url = layer_config['url']
            layer_name = layer_config['name']

            print(f"Fetching {layer_name} from {layer_url}")

            try:
                # Query FeatureServer with bounding box
                query_url = f"{layer_url}/query"
                query_params = {
                    'where': '1=1',
                    'geometry': f'{minx},{miny},{maxx},{maxy}',
                    'geometryType': 'esriGeometryEnvelope',
                    'inSR': '4326',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'outFields': '*',
                    'returnGeometry': 'true',
                    'outSR': '4326',  # Return in WGS84
                    'f': 'json'  # ESRI JSON format (geojson not supported)
                }

                response = requests.get(query_url, params=query_params, timeout=30)
                response.raise_for_status()
                esri_data = response.json()

                # Convert ESRI JSON features to GeoJSON using arcgis2geojson library
                from arcgis2geojson import arcgis2geojson

                features = []
                skipped = 0
                total_features = len(esri_data.get('features', []))

                for esri_feature in esri_data.get('features', []):
                    try:
                        # arcgis2geojson handles all geometry types, MultiPolygons, null geoms
                        geojson_feature = arcgis2geojson(esri_feature)

                        # Skip features with null geometries
                        if geojson_feature.get('geometry') is not None:
                            features.append(geojson_feature)
                        else:
                            skipped += 1
                    except Exception as e:
                        print(f"  WARNING: Failed to convert feature: {e}")
                        skipped += 1
                        continue

                feature_counts[layer_id] = len(features)
                if skipped > 0:
                    print(f"  Skipped {skipped}/{total_features} features (null/invalid geometries)")

                print(f"  Found {len(features)} features in {layer_name}")

                if len(features) == 0:
                    continue

                # Determine geometry type from first feature
                first_feature = features[0]
                if not first_feature or not first_feature.get('geometry'):
                    continue
                first_geom = shape(first_feature['geometry'])
                geom_type = first_geom.geom_type

                # Create schema based on first feature properties
                sample_props = first_feature.get('properties') or {}
                schema_props = {}
                for key, value in sample_props.items():
                    if value is None:
                        schema_props[key] = 'str'
                    elif isinstance(value, bool):
                        schema_props[key] = 'bool'
                    elif isinstance(value, int):
                        schema_props[key] = 'int'
                    elif isinstance(value, float):
                        schema_props[key] = 'float'
                    else:
                        schema_props[key] = 'str'

                schema = {
                    'geometry': geom_type,
                    'properties': schema_props
                }

                # Create shapefile for this layer
                shp_path = os.path.join(export_dir, f'{layer_id}.shp')

                with fiona.open(shp_path, 'w', driver='ESRI Shapefile',
                               crs=from_epsg(2226), schema=schema) as output:
                    for feature in features:
                        # Transform geometry to EPSG:2226
                        geom_wgs84 = shape(feature['geometry'])

                        # Transform coordinates
                        if geom_wgs84.geom_type == 'Point':
                            x, y = transformer.transform(geom_wgs84.x, geom_wgs84.y)
                            geom_2226 = geom_lib.Point(x, y)
                        elif geom_wgs84.geom_type in ['LineString', 'MultiLineString']:
                            coords_2226 = [transformer.transform(x, y) for x, y in geom_wgs84.coords]
                            geom_2226 = geom_lib.LineString(coords_2226)
                        elif geom_wgs84.geom_type == 'Polygon':
                            exterior_2226 = [transformer.transform(x, y) for x, y in geom_wgs84.exterior.coords]
                            geom_2226 = geom_lib.Polygon(exterior_2226)
                        elif geom_wgs84.geom_type == 'MultiPolygon':
                            polys_2226 = []
                            for poly in geom_wgs84.geoms:
                                exterior_2226 = [transformer.transform(x, y) for x, y in poly.exterior.coords]
                                polys_2226.append(geom_lib.Polygon(exterior_2226))
                            geom_2226 = geom_lib.MultiPolygon(polys_2226)
                        else:
                            continue  # Skip unsupported geometry types

                        output.write({
                            'geometry': geom_2226.__geo_interface__,
                            'properties': feature['properties']
                        })

                print(f"  Wrote {len(features)} features to {layer_id}.shp")

            except Exception as e:
                print(f"  ERROR fetching {layer_name}: {e}")
                feature_counts[layer_id] = 0

        # Create download URL
        download_url = f"/api/map-export/download-simple/{export_id}"

        return jsonify({
            'status': 'complete',
            'download_url': download_url,
            'export_id': export_id,
            'feature_counts': feature_counts,
            'message': f'Exported {sum(feature_counts.values())} total features'
        })

    except Exception as e:
        print(f"ERROR in create_simple_export: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-export/create', methods=['POST'])
def create_multi_format_export():
    """Create export with multiple formats (PNG, DXF, SHP, KML)"""
    try:
        import requests
        from shapely.geometry import shape
        from shapely import geometry as geom_lib
        from pyproj import Transformer

        params = request.json
        bbox = params.get('bbox', {})
        requested_layers = params.get('layers', [])
        formats = params.get('formats', ['shp'])  # Default to shapefile only
        png_options = params.get('png_options', {'north_arrow': True, 'scale_bar': True})

        print(f"Creating multi-format export:")
        print(f"  Formats: {formats}")
        print(f"  Layers: {requested_layers}")
        print(f"  PNG options: {png_options}")

        # Create unique ID for this export
        export_id = str(uuid.uuid4())
        export_dir = os.path.join('/tmp/exports', export_id)
        os.makedirs(export_dir, exist_ok=True)

        # Get bounding box in WGS84
        minx, miny, maxx, maxy = bbox['minx'], bbox['miny'], bbox['maxx'], bbox['maxy']

        # Coordinate transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:2226", always_xy=True)

        # Get GIS layer configurations from database
        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM gis_layers WHERE enabled = true AND id = ANY(%s)", (requested_layers,))
                layers = cur.fetchall()

        print(f"Found {len(layers)} layers in database")

        # PRIORITY 1: Fetch drawing entities from database (automatic, ALL layers)
        print("Fetching drawing entities from database...")
        all_layers_data = {}
        feature_counts = {}

        # Transform bbox to EPSG:2226 for PostGIS query
        min_x_2226, min_y_2226 = transformer.transform(minx, miny)
        max_x_2226, max_y_2226 = transformer.transform(maxx, maxy)
        bbox_2226 = (min_x_2226, min_y_2226, max_x_2226, max_y_2226)

        # Use MapExportService with database connection
        with get_db() as conn:
            export_service = MapExportService(db_conn=conn)
            project_id = params.get('project_id')
            drawing_layers = export_service.fetch_drawing_entities_by_layer(bbox_2226, project_id=project_id, srid=2226)

            if drawing_layers:
                print(f"Found {len(drawing_layers)} DXF-imported layers")
                for layer_name, features in drawing_layers.items():
                    # Features are already in EPSG:2226, need to transform to WGS84 for consistency
                    features_wgs84 = []
                    back_transformer = Transformer.from_crs("EPSG:2226", "EPSG:4326", always_xy=True)

                    for feature in features:
                        try:
                            geom_2226 = shape(feature['geometry'])

                            # Transform to WGS84 (handle both 2D and 3D geometries)
                            if geom_2226.geom_type == 'LineString':
                                # Handle 3D coordinates (x, y, z) by ignoring Z
                                coords_wgs84 = []
                                for coord in geom_2226.coords:
                                    x, y = coord[0], coord[1]  # Ignore Z if present
                                    lon, lat = back_transformer.transform(x, y)
                                    coords_wgs84.append((lon, lat))
                                geom_wgs84 = geom_lib.LineString(coords_wgs84)
                            elif geom_2226.geom_type == 'Polygon':
                                exterior_wgs84 = []
                                for coord in geom_2226.exterior.coords:
                                    x, y = coord[0], coord[1]  # Ignore Z if present
                                    lon, lat = back_transformer.transform(x, y)
                                    exterior_wgs84.append((lon, lat))
                                geom_wgs84 = geom_lib.Polygon(exterior_wgs84)
                            elif geom_2226.geom_type == 'Point':
                                x, y = geom_2226.x, geom_2226.y
                                lon, lat = back_transformer.transform(x, y)
                                geom_wgs84 = geom_lib.Point(lon, lat)
                            else:
                                geom_wgs84 = geom_2226  # Keep as-is for unsupported types

                            features_wgs84.append({
                                'type': 'Feature',
                                'geometry': geom_wgs84.__geo_interface__,
                                'properties': feature['properties']
                            })
                        except Exception as e:
                            print(f"Error transforming drawing entity: {e}")
                            import traceback
                            traceback.print_exc()
                            continue

                    all_layers_data[layer_name] = features_wgs84
                    feature_counts[layer_name] = len(features_wgs84)
                    print(f"  {layer_name}: {len(features_wgs84)} features")

        # PRIORITY 2: Fetch external WFS layers
        for layer_config in layers:
            layer_id = layer_config['id']
            layer_url = layer_config['url']
            layer_name = layer_config['name']

            print(f"Fetching external WFS layer {layer_name}...")

            try:
                # Query FeatureServer with bounding box
                query_url = f"{layer_url}/query"
                query_params = {
                    'where': '1=1',
                    'geometry': f'{minx},{miny},{maxx},{maxy}',
                    'geometryType': 'esriGeometryEnvelope',
                    'inSR': '4326',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'outFields': '*',
                    'returnGeometry': 'true',
                    'outSR': '4326',
                    'f': 'json'
                }

                response = requests.get(query_url, params=query_params, timeout=30)
                response.raise_for_status()
                esri_data = response.json()

                # Convert ESRI JSON to GeoJSON
                from arcgis2geojson import arcgis2geojson

                features = []
                for esri_feature in esri_data.get('features', []):
                    try:
                        geojson_feature = arcgis2geojson(esri_feature)
                        if geojson_feature.get('geometry') is not None:
                            features.append(geojson_feature)
                    except Exception as e:
                        continue

                feature_counts[layer_id] = len(features)
                all_layers_data[layer_id] = features
                print(f"  Found {len(features)} features")

            except Exception as e:
                print(f"  ERROR fetching {layer_name}: {e}")
                feature_counts[layer_id] = 0

        return jsonify({
            'status': 'complete',
            'export_id': export_id,
            'feature_counts': feature_counts,
            'message': f'Exported {sum(feature_counts.values())} total features'
        })

    except Exception as e:
        print(f"ERROR in create_multi_format_export: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-export/download-simple/<export_id>')
def download_simple_export(export_id: str):
    """Download exported shapefile as ZIP"""
    try:
        export_dir = os.path.join('/tmp/exports', export_id)

        if not os.path.exists(export_dir):
            return jsonify({'error': 'Export not found'}), 404

        # Create ZIP archive
        zip_path = os.path.join('/tmp', f'export_{export_id}.zip')

        import zipfile
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(export_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, export_dir)
                    zipf.write(file_path, arcname)

        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f'gis_export_{export_id}.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-export/status/<job_id>')
def get_export_status(job_id: str):
    """Get status of export job"""
    try:
        query = """
            SELECT id, status, params, download_url, file_size_mb,
                   error_message, created_at, expires_at
            FROM map_export_jobs
            WHERE id = %s
        """

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (job_id,))
                job = cur.fetchone()

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        return jsonify({
            'job_id': str(job['id']),
            'status': job['status'],
            'download_url': job['download_url'],
            'file_size_mb': float(job['file_size_mb']) if job['file_size_mb'] else None,
            'error': job['error_message'],
            'created_at': job['created_at'].isoformat() if job['created_at'] else None,
            'expires_at': job['expires_at'].isoformat() if job['expires_at'] else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map-export/download/<job_id>/<filename>')
def download_export(job_id: str, filename: str):
    """Download completed export file"""
    try:
        # Verify job exists and is complete
        query = "SELECT status, download_url FROM map_export_jobs WHERE id = %s"

        with get_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (job_id,))
                job = cur.fetchone()

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        if job['status'] != 'complete':
            return jsonify({'error': 'Export not complete'}), 400

        # Construct file path
        file_path = os.path.join('/tmp/exports', job_id, filename)

        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# COORDINATE SYSTEMS CRUD API
# ============================================

@gis_bp.route('/api/coordinate_systems')
def get_coordinate_systems_crud():
    """Get all coordinate systems"""
    try:
        query = """
            SELECT system_id, system_name, epsg_code, system_type, zone_number,
                   units, description, wkt, is_active
            FROM coordinate_systems
            WHERE is_active = TRUE
            ORDER BY system_type, system_name
        """
        systems = execute_query(query)
        return jsonify({'systems': systems})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/coordinate_systems', methods=['POST'])
def create_coordinate_system_crud():
    """Create a new coordinate system"""
    try:
        data = request.get_json()
        if not data or not data.get('system_name'):
            return jsonify({'error': 'system_name is required'}), 400

        query = """
            INSERT INTO coordinate_systems
            (system_name, epsg_code, system_type, zone_number, units, description, wkt, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING system_id
        """
        params = (
            data['system_name'],
            data.get('epsg_code'),
            data.get('system_type'),
            data.get('zone_number'),
            data.get('units'),
            data.get('description'),
            data.get('wkt'),
            data.get('is_active', True)
        )
        result = execute_query(query, params)
        return jsonify({'message': 'Coordinate system created successfully', 'system_id': result[0]['system_id']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/coordinate_systems/<system_id>', methods=['PUT'])
def update_coordinate_system_crud(system_id: str):
    """Update a coordinate system"""
    try:
        data = request.get_json()
        if not data.get('system_name'):
            return jsonify({'error': 'system_name is required'}), 400

        query = """
            UPDATE coordinate_systems
            SET system_name = %s, epsg_code = %s, system_type = %s, zone_number = %s,
                units = %s, description = %s, wkt = %s, is_active = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE system_id = %s
            RETURNING system_id
        """
        params = (
            data['system_name'],
            data.get('epsg_code'),
            data.get('system_type'),
            data.get('zone_number'),
            data.get('units'),
            data.get('description'),
            data.get('wkt'),
            data.get('is_active', True),
            system_id
        )
        result = execute_query(query, params)
        if not result:
            return jsonify({'error': 'Coordinate system not found'}), 404
        return jsonify({'message': 'Coordinate system updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/coordinate_systems/<system_id>', methods=['DELETE'])
def delete_coordinate_system_crud(system_id: str):
    """Delete a coordinate system (soft delete)"""
    try:
        query = "UPDATE coordinate_systems SET is_active = FALSE WHERE system_id = %s RETURNING system_id"
        result = execute_query(query, (system_id,))
        if not result:
            return jsonify({'error': 'Coordinate system not found'}), 404
        return jsonify({'message': 'Coordinate system deactivated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# MAP DATA & MEASUREMENT API
# ============================================

@gis_bp.route('/api/map/data', methods=['POST'])
def get_map_data():
    """Get spatial data for map with filters and styling"""
    try:
        data = request.get_json()
        entity_types = data.get('entity_types', [])
        filters = data.get('filters', {})
        bbox = data.get('bbox')  # [minx, miny, maxx, maxy]
        color_by = data.get('color_by', 'type')

        features = []

        # Color schemes
        type_colors = {
            'utility_structures': '#ff00ff',
            'survey_points': '#00ffff',
            'utility_lines': '#00ff88'
        }

        material_colors = {
            'PVC': '#00ffff',
            'HDPE': '#ff00ff',
            'DI': '#00ff88',
            'CONC': '#ffff00'
        }

        for entity_type in entity_types:
            # Build query based on entity type
            if entity_type == 'survey_points':
                query = """
                    SELECT id, point_number, northing, easting, elevation, description,
                           ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geojson
                    FROM survey_points
                    WHERE is_active = TRUE
                """
            elif entity_type == 'utility_structures':
                query = """
                    SELECT id, structure_number, structure_type, rim_elevation, invert_elevation,
                           ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geojson
                    FROM utility_structures
                    WHERE is_active = TRUE
                """
            elif entity_type == 'utility_lines':
                query = """
                    SELECT id, material, diameter, ST_Length(geometry) as length,
                           ST_AsGeoJSON(ST_Transform(geometry, 4326)) as geojson
                    FROM utility_lines
                    WHERE is_active = TRUE
                """
            else:
                continue

            # Add bbox filter if provided
            if bbox:
                query += f" AND ST_Intersects(geometry, ST_MakeEnvelope({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]}, 4326))"

            # Add other filters
            for key, value in filters.items():
                if value:
                    query += f" AND {key} = '{value}'"

            query += " LIMIT 1000"

            results = execute_query(query)

            # Convert to GeoJSON features
            for row in results:
                geom = json.loads(row['geojson']) if row.get('geojson') else None

                # Determine color
                if color_by == 'type':
                    color = type_colors.get(entity_type, '#ffffff')
                elif color_by == 'material' and 'material' in row:
                    color = material_colors.get(row['material'], '#ffffff')
                else:
                    color = '#00ffff'

                feature = {
                    'type': 'Feature',
                    'geometry': geom,
                    'properties': {
                        **{k: v for k, v in row.items() if k != 'geojson'},
                        'entity_type': entity_type,
                        'color': color
                    }
                }
                features.append(feature)

        return jsonify({
            'type': 'FeatureCollection',
            'features': features
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@gis_bp.route('/api/map/measure', methods=['POST'])
def map_measure():
    """Perform measurement on map"""
    try:
        data = request.get_json()
        measurement_type = data.get('measurement_type')
        coordinates = data.get('coordinates', [])

        if measurement_type == 'distance':
            # Calculate distance between points
            if len(coordinates) < 2:
                return jsonify({'error': 'Need at least 2 points'}), 400

            # Use PostGIS to calculate distance
            coords_str = ','.join([f"ST_SetSRID(ST_MakePoint({c[0]}, {c[1]}), 4326)" for c in coordinates])
            query = f"SELECT ST_Length(ST_MakeLine(ARRAY[{coords_str}]::geometry[])) as distance"
            result = execute_query(query)

            return jsonify({'distance': result[0]['distance'], 'unit': 'meters'})

        elif measurement_type == 'area':
            # Calculate area of polygon
            if len(coordinates) < 3:
                return jsonify({'error': 'Need at least 3 points'}), 400

            coords_str = ','.join([f"{c[0]} {c[1]}" for c in coordinates])
            query = f"SELECT ST_Area(ST_GeomFromText('POLYGON(({coords_str}))', 4326)) as area"
            result = execute_query(query)

            return jsonify({'area': result[0]['area'], 'unit': 'square meters'})

        elif measurement_type == 'elevation_profile':
            # Get elevation profile along a line
            elevations = []
            for coord in coordinates:
                # Query elevation at each point (simplified)
                query = f"""
                    SELECT elevation
                    FROM survey_points
                    WHERE ST_DWithin(geometry, ST_SetSRID(ST_MakePoint({coord[0]}, {coord[1]}), 4326), 10)
                    ORDER BY ST_Distance(geometry, ST_SetSRID(ST_MakePoint({coord[0]}, {coord[1]}), 4326))
                    LIMIT 1
                """
                result = execute_query(query)
                if result:
                    elevations.append(result[0]['elevation'])

            return jsonify({'elevations': elevations, 'count': len(elevations)})

        else:
            return jsonify({'error': 'Invalid measurement type'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500
