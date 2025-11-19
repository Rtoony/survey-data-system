"""
Projects Blueprint
Handles all project-related routes including CRUD operations, survey points, and page rendering
"""
from flask import Blueprint, render_template, jsonify, request, session
from database import get_db, execute_query, DB_CONFIG

# Create the projects blueprint
projects_bp = Blueprint('projects', __name__)


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_active_project_id():
    """
    Get the current active project ID from session.
    Returns None if no project is active.
    """
    return session.get('active_project_id')


# ============================================
# PAGE ROUTES (HTML Templates)
# ============================================

@projects_bp.route('/projects')
def projects_page():
    """Projects manager page"""
    return render_template('projects.html')


@projects_bp.route('/projects/<project_id>')
def project_overview(project_id):
    """Project Overview dashboard page"""
    return render_template('project_overview.html', project_id=project_id)


@projects_bp.route('/projects/<project_id>/survey-points')
def project_survey_points(project_id):
    """Project Survey Point Manager page"""
    return render_template('project_survey_points.html', project_id=project_id)


@projects_bp.route('/projects/<project_id>/command-center')
def project_command_center(project_id):
    """Project Command Center - central hub for project operations"""
    return render_template('project_command_center.html', project_id=project_id)


@projects_bp.route('/projects/<project_id>/entities')
def project_entity_browser_page(project_id):
    """Entity Browser - unified view of all project entities"""
    return render_template('project_entity_browser.html', project_id=project_id)


@projects_bp.route('/projects/<project_id>/relationship-sets')
def project_relationship_sets_page(project_id):
    """Relationship Sets Manager - manage project dependencies and compliance tracking"""
    return render_template('project_relationship_sets.html', project_id=project_id)


@projects_bp.route('/projects/<project_id>/gis-manager')
def project_gis_manager(project_id):
    """Project GIS Manager tool"""
    return render_template('project_gis_manager.html', project_id=project_id)


@projects_bp.route('/project-operations')
def project_operations():
    """Project Operations landing page"""
    return render_template('project_operations.html')


# ============================================
# API ROUTES - ACTIVE PROJECT MANAGEMENT
# ============================================

@projects_bp.route('/api/active-project')
def get_active_project():
    """Get the currently active project from session"""
    try:
        active_project_id = session.get('active_project_id')

        if not active_project_id:
            return jsonify({
                'active_project': None
            })

        project_query = """
            SELECT p.*
            FROM projects p
            WHERE p.project_id = %s
        """
        projects = execute_query(project_query, (active_project_id,))

        if not projects:
            session.pop('active_project_id', None)
            return jsonify({
                'active_project': None,
                'message': 'Previously selected project no longer exists'
            })

        project = projects[0]

        return jsonify({
            'active_project': project
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/api/active-project', methods=['POST'])
def set_active_project():
    """Set the active project in session"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        project_id = data.get('project_id')

        if project_id is None:
            session.pop('active_project_id', None)
            return jsonify({
                'success': True,
                'active_project': None,
                'message': 'Active project cleared'
            })

        # Verify project exists
        project_query = """
            SELECT p.*
            FROM projects p
            WHERE p.project_id = %s
        """
        projects = execute_query(project_query, (project_id,))

        if not projects:
            return jsonify({'error': 'Project not found'}), 404

        # Set active project in session
        session['active_project_id'] = str(project_id)

        return jsonify({
            'success': True,
            'active_project': projects[0]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# API ROUTES - PROJECT CRUD
# ============================================

@projects_bp.route('/api/projects')
def get_projects():
    """Get all projects"""
    try:
        query = """
            SELECT p.*
            FROM projects p
            ORDER BY p.created_at DESC
        """
        projects = execute_query(query)
        return jsonify({'projects': projects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project with coordinate system support"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        project_name = data.get('project_name')
        client_id = data.get('client_id')
        client_name = data.get('client_name')
        project_number = data.get('project_number')
        description = data.get('description')
        default_coordinate_system_id = data.get('default_coordinate_system_id')

        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400

        # If no coordinate system specified, get the default (EPSG:2226)
        if not default_coordinate_system_id:
            from services.coordinate_system_service import CoordinateSystemService
            crs_service = CoordinateSystemService(DB_CONFIG)
            default_cs = crs_service.get_coordinate_system_by_epsg('EPSG:2226')
            if default_cs:
                default_coordinate_system_id = default_cs['system_id']

        with get_db() as conn:
            with conn.cursor() as cur:
                # If client_id is provided, fetch client_name from clients table
                if client_id:
                    cur.execute(
                        "SELECT client_name FROM clients WHERE client_id = %s",
                        (client_id,)
                    )
                    client_result = cur.fetchone()
                    if client_result:
                        client_name = client_result[0]

                cur.execute(
                    """
                    INSERT INTO projects (
                        project_name, client_id, client_name, project_number, description,
                        default_coordinate_system_id, quality_score, tags, attributes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 0.5, '{}', '{}')
                    RETURNING project_id, project_name, client_id, client_name, project_number,
                              default_coordinate_system_id, created_at
                    """,
                    (project_name, client_id, client_name, project_number, description, default_coordinate_system_id)
                )
                result = cur.fetchone()
                conn.commit()

                return jsonify({
                    'project_id': str(result[0]),
                    'project_name': result[1],
                    'client_id': result[2],
                    'client_name': result[3],
                    'project_number': result[4],
                    'default_coordinate_system_id': str(result[5]) if result[5] else None,
                    'created_at': result[6].isoformat() if result[6] else None
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Delete project (cascades will handle related entities)
                cur.execute('DELETE FROM projects WHERE project_id = %s', (project_id,))
                conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/api/projects/<project_id>')
def get_project(project_id):
    """Get a single project by ID"""
    try:
        query = """
            SELECT
                p.*,
                c.client_name as client_name_from_ref
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE p.project_id = %s
        """
        result = execute_query(query, (project_id,))

        if not result:
            return jsonify({'error': 'Project not found'}), 404

        project_data = result[0]
        if project_data.get('client_name_from_ref'):
            project_data['client_name'] = project_data['client_name_from_ref']

        return jsonify(project_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project with coordinate system support"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        project_name = data.get('project_name')
        client_id = data.get('client_id')
        client_name = data.get('client_name')
        project_number = data.get('project_number')
        description = data.get('description')
        default_coordinate_system_id = data.get('default_coordinate_system_id')

        if not project_name:
            return jsonify({'error': 'project_name is required'}), 400

        with get_db() as conn:
            with conn.cursor() as cur:
                if client_id:
                    cur.execute(
                        "SELECT client_name FROM clients WHERE client_id = %s",
                        (client_id,)
                    )
                    client_result = cur.fetchone()
                    if client_result:
                        client_name = client_result[0]

                cur.execute(
                    """
                    UPDATE projects
                    SET project_name = %s,
                        client_id = %s,
                        client_name = %s,
                        project_number = %s,
                        description = %s,
                        default_coordinate_system_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = %s
                    RETURNING project_id, project_name, client_id, client_name, project_number,
                              default_coordinate_system_id, updated_at
                    """,
                    (project_name, client_id, client_name, project_number, description,
                     default_coordinate_system_id, project_id)
                )
                result = cur.fetchone()
                if not result:
                    return jsonify({'error': 'Project not found'}), 404
                conn.commit()

                return jsonify({
                    'project_id': str(result[0]),
                    'project_name': result[1],
                    'client_id': result[2],
                    'client_name': result[3],
                    'project_number': result[4],
                    'default_coordinate_system_id': str(result[5]) if result[5] else None,
                    'updated_at': result[6].isoformat() if result[6] else None
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# API ROUTES - SURVEY POINTS
# ============================================

@projects_bp.route('/api/projects/<project_id>/survey-points')
def get_project_survey_points(project_id):
    """Get all survey points for a specific project with optional filtering"""
    try:
        # Get query parameters for filtering
        point_type = request.args.get('point_type')
        is_control = request.args.get('is_control')
        search = request.args.get('search')

        # Build dynamic WHERE clause
        where_conditions = ["sp.project_id = %s", "sp.is_active = true"]
        params = [project_id]

        if point_type:
            where_conditions.append("sp.point_type = %s")
            params.append(point_type)

        if is_control is not None:
            is_control_bool = is_control.lower() == 'true'
            where_conditions.append("sp.is_control_point = %s")
            params.append(is_control_bool)

        if search:
            where_conditions.append("LOWER(sp.point_number::text) LIKE %s")
            params.append(f"%{search.lower()}%")

        where_clause = " AND ".join(where_conditions)

        query = f"""
            SELECT
                sp.point_id,
                sp.point_number,
                sp.point_description,
                sp.point_type,
                sp.elevation,
                sp.northing,
                sp.easting,
                sp.is_control_point,
                sp.survey_date,
                sp.surveyed_by,
                sp.survey_method,
                sp.horizontal_accuracy,
                sp.vertical_accuracy,
                sp.quality_score,
                sp.notes,
                sp.created_at
            FROM survey_points sp
            WHERE {where_clause}
            ORDER BY sp.point_number
        """
        points = execute_query(query, tuple(params))
        return jsonify({
            'project_id': project_id,
            'count': len(points),
            'points': points
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@projects_bp.route('/api/projects/<project_id>/survey-points', methods=['DELETE'])
def delete_survey_points(project_id):
    """Soft-delete survey points by setting is_active = false"""
    try:
        data = request.get_json()
        if not data or 'point_ids' not in data:
            return jsonify({'error': 'point_ids array is required'}), 400

        point_ids = data['point_ids']
        if not isinstance(point_ids, list) or len(point_ids) == 0:
            return jsonify({'error': 'point_ids must be a non-empty array'}), 400

        # Soft delete points (set is_active = false)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE survey_points
                    SET is_active = false, updated_at = CURRENT_TIMESTAMP
                    WHERE project_id = %s
                      AND point_id = ANY(%s::uuid[])
                      AND is_active = true
                    """,
                    (project_id, point_ids)
                )
                deleted_count = cur.rowcount
                conn.commit()

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully soft-deleted {deleted_count} survey point(s)'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
