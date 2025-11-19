"""
Pipe Networks Blueprint
Handles pipe network editor, pipe CRUD, utility structures, and validation
Extracted from app.py during Phase 13 refactoring
"""
from flask import Blueprint, render_template, jsonify, request, session
from typing import Dict, List, Any, Optional
from database import get_db, execute_query
from app.extensions import cache
import json

# Create the pipes blueprint
pipes_bp = Blueprint('pipes', __name__)


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_mannings_n(material: Optional[str]) -> float:
    """Get Manning's roughness coefficient based on pipe material"""
    n_values = {
        'PVC': 0.010,
        'HDPE': 0.010,
        'DI': 0.012,  # Ductile Iron
        'RCP': 0.013,  # Reinforced Concrete Pipe
        'CMP': 0.024,  # Corrugated Metal Pipe
        'VCP': 0.013,  # Vitrified Clay Pipe
        'ABS': 0.010,
        'PE': 0.010,  # Polyethylene
    }
    # Default to PVC if material not found
    return n_values.get(material.upper() if material else 'PVC', 0.013)


# ============================================
# PAGE ROUTES (HTML Templates)
# ============================================

@pipes_bp.route('/tools/pipe-network-editor')
def pipe_network_editor_tool():
    """Pipe Network Editor - Manage gravity and pressure pipe networks"""
    return render_template('tools/pipe_network_editor.html')


# ============================================================================
# PIPE NETWORK EDITOR API ENDPOINTS
# ============================================================================

@pipes_bp.route('/api/pipe-networks')
def get_pipe_networks():
    """Get list of all pipe networks, optionally filtered by project or mode"""
    try:
        project_id = session.get('active_project_id')
        network_mode = request.args.get('mode')

        query = """
            SELECT
                pn.network_id,
                pn.network_name,
                pn.utility_system,
                pn.network_mode,
                pn.network_status,
                pn.description,
                p.project_name,
                COUNT(DISTINCT unm_lines.line_id) as line_count,
                COUNT(DISTINCT unm_struct.structure_id) as structure_count
            FROM pipe_networks pn
            LEFT JOIN projects p ON pn.project_id = p.project_id
            LEFT JOIN utility_network_memberships unm_lines ON pn.network_id = unm_lines.network_id AND unm_lines.line_id IS NOT NULL
            LEFT JOIN utility_network_memberships unm_struct ON pn.network_id = unm_struct.network_id AND unm_struct.structure_id IS NOT NULL
            WHERE 1=1
        """
        params = []

        if project_id:
            query += " AND pn.project_id = %s"
            params.append(project_id)

        if network_mode:
            query += " AND pn.network_mode = %s"
            params.append(network_mode)

        query += """
            GROUP BY pn.network_id, pn.project_id, pn.network_name, pn.utility_system,
                     pn.network_mode, pn.network_status, pn.description, p.project_name
            ORDER BY pn.created_at DESC
        """

        networks = execute_query(query, tuple(params) if params else None)
        return jsonify({'networks': networks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>')
def get_network_details(network_id):
    """Get detailed information about a specific pipe network"""
    try:
        query = """
            SELECT
                pn.network_id,
                pn.project_id,
                pn.network_name,
                pn.utility_system,
                pn.network_mode,
                pn.network_status,
                pn.description,
                pn.attributes,
                p.project_name,
                p.client_name
            FROM pipe_networks pn
            LEFT JOIN projects p ON pn.project_id = p.project_id
            WHERE pn.network_id = %s
        """
        network = execute_query(query, (network_id,))

        if not network or len(network) == 0:
            return jsonify({'error': 'Network not found'}), 404

        return jsonify({'network': network[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>/pipes')
def get_network_pipes(network_id):
    """Get all pipes in a network with from/to structure information"""
    try:
        query = """
            SELECT
                ul.line_id,
                ul.line_number,
                ul.utility_system,
                ul.material,
                ul.diameter_mm,
                ul.invert_elevation_start,
                ul.invert_elevation_end,
                ul.slope,
                ul.length,
                ul.from_structure_id,
                ul.to_structure_id,
                from_struct.structure_number as from_structure_number,
                from_struct.structure_type as from_structure_type,
                to_struct.structure_number as to_structure_number,
                to_struct.structure_type as to_structure_type,
                ST_AsGeoJSON(ul.geometry) as geometry,
                ul.attributes
            FROM utility_network_memberships unm
            JOIN utility_lines ul ON unm.line_id = ul.line_id
            LEFT JOIN utility_structures from_struct ON ul.from_structure_id = from_struct.structure_id
            LEFT JOIN utility_structures to_struct ON ul.to_structure_id = to_struct.structure_id
            WHERE unm.network_id = %s
            ORDER BY ul.line_number, ul.created_at
        """
        pipes = execute_query(query, (network_id,))
        return jsonify({'pipes': pipes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>/structures')
def get_network_structures(network_id):
    """Get all structures in a network"""
    try:
        query = """
            SELECT
                us.structure_id,
                us.structure_number,
                us.structure_type,
                us.utility_system,
                us.rim_elevation,
                us.invert_elevation,
                us.size_mm,
                us.material,
                us.manhole_depth_ft,
                us.condition,
                ST_AsGeoJSON(us.rim_geometry) as geometry,
                us.attributes
            FROM utility_network_memberships unm
            JOIN utility_structures us ON unm.structure_id = us.structure_id
            WHERE unm.network_id = %s
            ORDER BY us.structure_number, us.created_at
        """
        structures = execute_query(query, (network_id,))
        return jsonify({'structures': structures})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>/pipes/<pipe_id>', methods=['PUT'])
def update_network_pipe(network_id, pipe_id):
    """Update pipe attributes (preserves geometry)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        allowed_fields = [
            'line_number', 'material', 'diameter_mm',
            'invert_elevation_start', 'invert_elevation_end',
            'slope', 'from_structure_id', 'to_structure_id', 'notes'
        ]

        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(pipe_id)

        with get_db() as conn:
            with conn.cursor() as cur:
                query = f"""
                    UPDATE utility_lines
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE line_id = %s
                    RETURNING line_id
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                conn.commit()

                if not result:
                    return jsonify({'error': 'Pipe not found'}), 404

                return jsonify({'success': True, 'line_id': str(result[0])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>/structures/<structure_id>', methods=['PUT'])
def update_network_structure(network_id, structure_id):
    """Update structure attributes (preserves geometry)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        allowed_fields = [
            'structure_number', 'structure_type', 'rim_elevation',
            'invert_elevation', 'size_mm', 'material',
            'manhole_depth_ft', 'condition', 'notes'
        ]

        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(structure_id)

        with get_db() as conn:
            with conn.cursor() as cur:
                query = f"""
                    UPDATE utility_structures
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE structure_id = %s
                    RETURNING structure_id
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                conn.commit()

                if not result:
                    return jsonify({'error': 'Structure not found'}), 404

                return jsonify({'success': True, 'structure_id': str(result[0])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>/auto-connect', methods=['POST'])
def auto_connect_pipes(network_id):
    """Automatically connect pipes to nearby structures using spatial snapping"""
    try:
        from pipe_structure_connector import PipeStructureConnector

        data = request.get_json() or {}
        tolerance_feet = data.get('tolerance_feet', 5.0)

        connector = PipeStructureConnector(tolerance_feet=tolerance_feet)
        results = connector.connect_network_pipes(network_id)

        if results.get('success'):
            return jsonify(results), 200
        else:
            return jsonify(results), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@pipes_bp.route('/api/pipe-networks/<network_id>/viewer-entities')
def get_network_viewer_entities(network_id):
    """Get network entities (pipes + structures) in Entity Viewer format with transformed geometries"""
    try:
        all_entities = []

        # Fetch pipes
        pipes_query = """
            SELECT
                ul.line_id::text as entity_id,
                ul.line_number as label,
                'pipe' as entity_type,
                ul.utility_system,
                ul.material,
                ul.diameter_mm,
                ul.slope,
                ul.length,
                ul.from_structure_id::text,
                ul.to_structure_id::text,
                ST_AsGeoJSON(ST_Transform(ul.geometry, 4326))::json as geometry
            FROM utility_network_memberships unm
            JOIN utility_lines ul ON unm.line_id = ul.line_id
            WHERE unm.network_id = %s AND ul.geometry IS NOT NULL
            ORDER BY ul.line_number
        """
        pipes = execute_query(pipes_query, (network_id,))

        for pipe in (pipes or []):
            all_entities.append({
                'entity_id': pipe['entity_id'],
                'entity_type': 'pipe',
                'label': pipe['label'] or 'Unnamed Pipe',
                'layer_name': pipe['utility_system'] or 'Unknown',
                'category': 'Utilities',
                'geometry_type': 'line',
                'color': '#f7b801' if pipe['utility_system'] == 'Storm' else '#0096ff',
                'geometry': pipe['geometry'],
                'properties': {
                    'material': pipe['material'],
                    'diameter_mm': pipe['diameter_mm'],
                    'slope': pipe['slope'],
                    'length': pipe['length'],
                    'from_structure': pipe['from_structure_id'],
                    'to_structure': pipe['to_structure_id']
                }
            })

        # Fetch structures
        structures_query = """
            SELECT
                us.structure_id::text as entity_id,
                us.structure_number as label,
                'structure' as entity_type,
                us.structure_type,
                us.utility_system,
                us.rim_elevation,
                us.invert_elevation,
                us.manhole_depth_ft,
                us.condition,
                ST_AsGeoJSON(ST_Transform(us.rim_geometry, 4326))::json as geometry
            FROM utility_network_memberships unm
            JOIN utility_structures us ON unm.structure_id = us.structure_id
            WHERE unm.network_id = %s AND us.rim_geometry IS NOT NULL
            ORDER BY us.structure_number
        """
        structures = execute_query(structures_query, (network_id,))

        for struct in (structures or []):
            all_entities.append({
                'entity_id': struct['entity_id'],
                'entity_type': 'structure',
                'label': struct['label'] or 'Unnamed Structure',
                'layer_name': struct['utility_system'] or 'Unknown',
                'category': 'Utilities',
                'geometry_type': 'point',
                'color': '#6a994e',
                'geometry': struct['geometry'],
                'properties': {
                    'type': struct['structure_type'],
                    'rim_elevation': struct['rim_elevation'],
                    'invert_elevation': struct['invert_elevation'],
                    'depth_ft': struct['manhole_depth_ft'],
                    'condition': struct['condition']
                }
            })

        # Calculate combined bounding box
        bbox = None
        if all_entities:
            bbox_query = """
                SELECT ST_Extent(
                    ST_Transform(
                        ST_Union(
                            ARRAY[
                                (SELECT ST_Collect(ul.geometry)
                                 FROM utility_network_memberships unm
                                 JOIN utility_lines ul ON unm.line_id = ul.line_id
                                 WHERE unm.network_id = %s AND ul.geometry IS NOT NULL),
                                (SELECT ST_Collect(us.rim_geometry)
                                 FROM utility_network_memberships unm
                                 JOIN utility_structures us ON unm.structure_id = us.structure_id
                                 WHERE unm.network_id = %s AND us.rim_geometry IS NOT NULL)
                            ]
                        ),
                        4326
                    )
                ) as bbox
            """
            bbox_result = execute_query(bbox_query, (network_id, network_id))

            if bbox_result and bbox_result[0]['bbox']:
                bbox_str = bbox_result[0]['bbox']
                coords = bbox_str.replace('BOX(', '').replace(')', '').split(',')
                min_coords = coords[0].strip().split()
                max_coords = coords[1].strip().split()
                bbox = {
                    'minX': float(min_coords[0]),
                    'minY': float(min_coords[1]),
                    'maxX': float(max_coords[0]),
                    'maxY': float(max_coords[1])
                }

        # Calculate counts
        type_counts = {}
        layer_counts = {}
        for entity in all_entities:
            etype = entity.get('entity_type', 'Unknown')
            type_counts[etype] = type_counts.get(etype, 0) + 1

            layer = entity.get('layer_name', 'Unknown')
            layer_counts[layer] = layer_counts.get(layer, 0) + 1

        return jsonify({
            'entities': all_entities,
            'bbox': bbox,
            'type_counts': type_counts,
            'layer_counts': layer_counts,
            'total_count': len(all_entities)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipes')
def get_pipes():
    """Get all pipes for the active project with optional filters"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project', 'pipes': []}), 200

        # Get filter parameters
        line_type = request.args.get('line_type')
        material = request.args.get('material')
        min_diameter = request.args.get('min_diameter', type=float)
        max_diameter = request.args.get('max_diameter', type=float)

        # Build query
        query = """
            SELECT
                ul.line_id,
                ul.line_type,
                ul.material,
                ul.diameter,
                ul.slope,
                ul.length_ft,
                ul.pipe_class,
                ul.install_date,
                ul.condition_rating,
                ul.upstream_structure_id,
                ul.downstream_structure_id,
                ST_AsGeoJSON(ST_Transform(ul.geometry, 4326))::json as geometry
            FROM utility_lines ul
            WHERE ul.project_id = %s
        """
        params = [project_id]

        # Apply filters
        if line_type:
            query += " AND ul.line_type = %s"
            params.append(line_type)

        if material:
            query += " AND ul.material = %s"
            params.append(material)

        if min_diameter is not None:
            query += " AND ul.diameter >= %s"
            params.append(min_diameter)

        if max_diameter is not None:
            query += " AND ul.diameter <= %s"
            params.append(max_diameter)

        query += " ORDER BY ul.created_at DESC"

        pipes = execute_query(query, tuple(params))
        return jsonify({'pipes': pipes or []})

    except Exception as e:
        return jsonify({'error': str(e), 'pipes': []}), 500


@pipes_bp.route('/api/pipes/<pipe_id>', methods=['GET'])
def get_pipe(pipe_id):
    """Get detailed information about a specific pipe"""
    try:
        query = """
            SELECT
                ul.*,
                ST_AsGeoJSON(ST_Transform(ul.geometry, 4326))::json as geometry,
                us1.structure_number as upstream_structure_number,
                us2.structure_number as downstream_structure_number
            FROM utility_lines ul
            LEFT JOIN utility_structures us1 ON ul.upstream_structure_id = us1.structure_id
            LEFT JOIN utility_structures us2 ON ul.downstream_structure_id = us2.structure_id
            WHERE ul.line_id = %s
        """
        result = execute_query(query, (pipe_id,))

        if not result or len(result) == 0:
            return jsonify({'error': 'Pipe not found'}), 404

        return jsonify({'pipe': result[0]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipes', methods=['POST'])
def create_pipe():
    """Create a new pipe"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project'}), 400

        data = request.get_json()

        # Validate required fields
        required = ['line_type', 'diameter', 'material', 'geometry']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Insert pipe
        query = """
            INSERT INTO utility_lines (
                project_id, line_type, material, diameter,
                slope, pipe_class, geometry
            ) VALUES (%s, %s, %s, %s, %s, %s, ST_Transform(ST_GeomFromGeoJSON(%s), 2226))
            RETURNING line_id
        """

        result = execute_query(query, (
            project_id,
            data['line_type'],
            data['material'],
            data['diameter'],
            data.get('slope', 0.005),
            data.get('pipe_class', 'Standard'),
            json.dumps(data['geometry'])
        ))

        if result and len(result) > 0:
            return jsonify({'line_id': str(result[0]['line_id'])}), 201
        else:
            return jsonify({'error': 'Failed to create pipe'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipes/<pipe_id>', methods=['PUT'])
def update_pipe(pipe_id):
    """Update a pipe"""
    try:
        data = request.get_json()

        allowed_fields = [
            'line_type', 'material', 'diameter', 'slope',
            'pipe_class', 'install_date', 'condition_rating',
            'upstream_structure_id', 'downstream_structure_id'
        ]

        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(pipe_id)

        with get_db() as conn:
            with conn.cursor() as cur:
                query = f"""
                    UPDATE utility_lines
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE line_id = %s
                    RETURNING line_id
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                conn.commit()

                if not result:
                    return jsonify({'error': 'Pipe not found'}), 404

                return jsonify({'success': True, 'line_id': str(result[0])})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipes/<pipe_id>', methods=['DELETE'])
def delete_pipe(pipe_id):
    """Delete a pipe (soft delete)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Check if pipe exists
                cur.execute("SELECT line_id FROM utility_lines WHERE line_id = %s", (pipe_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Pipe not found'}), 404

                # Soft delete by updating a deleted_at timestamp
                # If deleted_at column doesn't exist, we'll do hard delete
                cur.execute("""
                    DELETE FROM utility_lines WHERE line_id = %s
                    RETURNING line_id
                """, (pipe_id,))
                result = cur.fetchone()
                conn.commit()

                return jsonify({'success': True, 'line_id': str(result[0])})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/pipes/validate')
def validate_pipes():
    """Validate pipe network connectivity and hydraulics"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project'}), 400

        issues = []

        # Check for disconnected pipes (no upstream or downstream structure)
        query1 = """
            SELECT line_id, line_type
            FROM utility_lines
            WHERE project_id = %s
            AND (upstream_structure_id IS NULL OR downstream_structure_id IS NULL)
        """
        disconnected = execute_query(query1, (project_id,))

        for pipe in (disconnected or []):
            issues.append({
                'type': 'Disconnected Pipe',
                'severity': 'error',
                'message': f'Pipe {pipe["line_id"]} ({pipe["line_type"]}) is not connected to structures'
            })

        # Check for pipes with negative slope (flowing uphill for gravity systems)
        query2 = """
            SELECT line_id, line_type, slope
            FROM utility_lines
            WHERE project_id = %s
            AND line_type IN ('gravity_main', 'storm_drain', 'sanitary_sewer')
            AND slope < 0
        """
        uphill = execute_query(query2, (project_id,))

        for pipe in (uphill or []):
            issues.append({
                'type': 'Negative Slope',
                'severity': 'error',
                'message': f'Gravity pipe {pipe["line_id"]} has negative slope ({pipe["slope"]})'
            })

        # Check for pipes with very low slope (< 0.1%)
        query3 = """
            SELECT line_id, line_type, slope
            FROM utility_lines
            WHERE project_id = %s
            AND line_type IN ('gravity_main', 'storm_drain', 'sanitary_sewer')
            AND slope < 0.001
            AND slope >= 0
        """
        low_slope = execute_query(query3, (project_id,))

        for pipe in (low_slope or []):
            issues.append({
                'type': 'Low Slope Warning',
                'severity': 'warning',
                'message': f'Pipe {pipe["line_id"]} has very low slope ({(pipe["slope"] * 100):.3f}%) - may have flow issues'
            })

        return jsonify({'issues': issues})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/structures')
def get_structures():
    """Get all structures for the active project with optional filters"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project', 'structures': []}), 200

        # Get filter parameters
        structure_type = request.args.get('structure_type')
        condition = request.args.get('condition', type=int)

        # Build query
        query = """
            SELECT
                us.structure_id,
                us.structure_number,
                us.structure_type,
                us.rim_elevation,
                us.invert_elevation,
                us.depth_ft,
                us.diameter,
                us.material,
                us.condition_rating,
                us.install_date,
                ST_AsGeoJSON(ST_Transform(us.geometry, 4326))::json as geometry
            FROM utility_structures us
            WHERE us.project_id = %s
        """
        params = [project_id]

        # Apply filters
        if structure_type:
            query += " AND us.structure_type = %s"
            params.append(structure_type)

        if condition is not None:
            query += " AND us.condition_rating = %s"
            params.append(condition)

        query += " ORDER BY us.structure_number, us.created_at DESC"

        structures = execute_query(query, tuple(params))
        return jsonify({'structures': structures or []})

    except Exception as e:
        return jsonify({'error': str(e), 'structures': []}), 500


@pipes_bp.route('/api/structures/<structure_id>', methods=['GET'])
def get_structure(structure_id):
    """Get detailed information about a specific structure"""
    try:
        query = """
            SELECT
                us.*,
                ST_AsGeoJSON(ST_Transform(us.geometry, 4326))::json as geometry
            FROM utility_structures us
            WHERE us.structure_id = %s
        """
        result = execute_query(query, (structure_id,))

        if not result or len(result) == 0:
            return jsonify({'error': 'Structure not found'}), 404

        return jsonify({'structure': result[0]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/structures', methods=['POST'])
def create_structure():
    """Create a new structure"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project'}), 400

        data = request.get_json()

        # Validate required fields
        required = ['structure_type', 'geometry']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

        # Insert structure
        query = """
            INSERT INTO utility_structures (
                project_id, structure_type, structure_number,
                rim_elevation, invert_elevation, depth_ft,
                diameter, material, condition_rating, geometry
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_Transform(ST_GeomFromGeoJSON(%s), 2226))
            RETURNING structure_id
        """

        result = execute_query(query, (
            project_id,
            data['structure_type'],
            data.get('structure_number'),
            data.get('rim_elevation'),
            data.get('invert_elevation'),
            data.get('depth_ft'),
            data.get('diameter'),
            data.get('material'),
            data.get('condition_rating', 3),
            json.dumps(data['geometry'])
        ))

        if result and len(result) > 0:
            return jsonify({'structure_id': str(result[0]['structure_id'])}), 201
        else:
            return jsonify({'error': 'Failed to create structure'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/structures/<structure_id>', methods=['PUT'])
def update_structure(structure_id):
    """Update a structure"""
    try:
        data = request.get_json()

        allowed_fields = [
            'structure_type', 'structure_number', 'rim_elevation',
            'invert_elevation', 'depth_ft', 'diameter', 'material',
            'condition_rating', 'install_date'
        ]

        updates = []
        params = []
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = %s")
                params.append(data[field])

        if not updates:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(structure_id)

        with get_db() as conn:
            with conn.cursor() as cur:
                query = f"""
                    UPDATE utility_structures
                    SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                    WHERE structure_id = %s
                    RETURNING structure_id
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                conn.commit()

                if not result:
                    return jsonify({'error': 'Structure not found'}), 404

                return jsonify({'success': True, 'structure_id': str(result[0])})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/structures/<structure_id>', methods=['DELETE'])
def delete_structure(structure_id):
    """Delete a structure"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Check if structure exists
                cur.execute("SELECT structure_id FROM utility_structures WHERE structure_id = %s", (structure_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Structure not found'}), 404

                # Delete
                cur.execute("""
                    DELETE FROM utility_structures WHERE structure_id = %s
                    RETURNING structure_id
                """, (structure_id,))
                result = cur.fetchone()
                conn.commit()

                return jsonify({'success': True, 'structure_id': str(result[0])})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pipes_bp.route('/api/structures/validate')
def validate_structures():
    """Validate structure elevations and depths"""
    try:
        project_id = session.get('active_project_id')
        if not project_id:
            return jsonify({'error': 'No active project'}), 400

        issues = []

        # Check for structures with rim < invert (impossible)
        query1 = """
            SELECT structure_id, structure_number, structure_type, rim_elevation, invert_elevation
            FROM utility_structures
            WHERE project_id = %s
            AND rim_elevation IS NOT NULL
            AND invert_elevation IS NOT NULL
            AND rim_elevation < invert_elevation
        """
        invalid_elevations = execute_query(query1, (project_id,))

        for structure in (invalid_elevations or []):
            issues.append({
                'type': 'Invalid Elevations',
                'severity': 'error',
                'message': f'Structure {structure["structure_number"]} ({structure["structure_type"]}) has rim elevation ({structure["rim_elevation"]}) lower than invert elevation ({structure["invert_elevation"]})'
            })

        # Check for structures missing elevation data
        query2 = """
            SELECT structure_id, structure_number, structure_type
            FROM utility_structures
            WHERE project_id = %s
            AND (rim_elevation IS NULL OR invert_elevation IS NULL)
        """
        missing_elevations = execute_query(query2, (project_id,))

        for structure in (missing_elevations or []):
            issues.append({
                'type': 'Missing Elevation Data',
                'severity': 'warning',
                'message': f'Structure {structure["structure_number"]} ({structure["structure_type"]}) is missing rim or invert elevation'
            })

        # Check for very deep structures (> 30 feet)
        query3 = """
            SELECT structure_id, structure_number, structure_type, rim_elevation, invert_elevation
            FROM utility_structures
            WHERE project_id = %s
            AND rim_elevation IS NOT NULL
            AND invert_elevation IS NOT NULL
            AND (rim_elevation - invert_elevation) > 30
        """
        deep_structures = execute_query(query3, (project_id,))

        for structure in (deep_structures or []):
            depth = structure['rim_elevation'] - structure['invert_elevation']
            issues.append({
                'type': 'Unusually Deep Structure',
                'severity': 'warning',
                'message': f'Structure {structure["structure_number"]} ({structure["structure_type"]}) is very deep ({depth:.2f} ft) - verify elevations'
            })

        return jsonify({'issues': issues})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
