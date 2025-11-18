"""
Authentication Decorators for ACAD-GIS
Provides decorators for protecting Flask routes with authentication and authorization
"""

from functools import wraps
from typing import Callable, List, Optional
from flask import session, redirect, url_for, request, jsonify, g
from services.auth_service import auth_service
from services.rbac_service import rbac_service


def login_required(f: Callable) -> Callable:
    """
    Decorator to require authentication for route

    Usage:
        @app.route('/protected')
        @login_required
        def protected_route():
            return "You are logged in!"

    Returns:
        - HTTP 401 if not authenticated (API routes)
        - Redirect to login page (HTML routes)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Audit log for access denied
            auth_service.create_audit_log(
                'ACCESS_DENIED',
                success=False,
                error_message='Not authenticated'
            )

            # API routes return JSON
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'Please log in to access this resource'
                }), 401

            # HTML routes redirect to login
            return redirect(url_for('auth_login', next=request.url))

        # Get current user and store in g for request context
        user = auth_service.get_current_user()
        if not user:
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Invalid session'}), 401
            return redirect(url_for('auth_login'))

        # Check if user is active
        if not user.get('is_active'):
            session.clear()
            auth_service.create_audit_log(
                'ACCESS_DENIED',
                success=False,
                error_message='User account deactivated'
            )
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Account deactivated'}), 403
            return redirect(url_for('auth_login'))

        # Store user in Flask g object for easy access in routes
        g.current_user = user

        # Update session activity
        if 'session_token' in session:
            auth_service.update_session_activity(session['session_token'])

        return f(*args, **kwargs)

    return decorated_function


def role_required(*roles: str) -> Callable:
    """
    Decorator to require specific role(s) for route

    Usage:
        @app.route('/admin')
        @login_required
        @role_required('ADMIN')
        def admin_route():
            return "Admin only"

        @app.route('/engineering')
        @login_required
        @role_required('ADMIN', 'ENGINEER')
        def engineering_route():
            return "Admin or Engineer only"

    Args:
        *roles: One or more required roles (ADMIN, ENGINEER, VIEWER)

    Returns:
        - HTTP 403 if user doesn't have required role
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # login_required should be applied first
            if not hasattr(g, 'current_user') or not g.current_user:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth_login'))

            user_role = g.current_user.get('role')

            if user_role not in roles:
                # Audit log for access denied
                auth_service.create_audit_log(
                    'ACCESS_DENIED',
                    success=False,
                    error_message=f'Role {user_role} not in {roles}'
                )

                if request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'This resource requires one of the following roles: {", ".join(roles)}',
                        'your_role': user_role
                    }), 403

                # HTML routes show error page
                return f"<h1>403 Forbidden</h1><p>You don't have permission to access this resource. Required role: {', '.join(roles)}. Your role: {user_role}</p>", 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def permission_required(resource: str, action: str) -> Callable:
    """
    Decorator to require specific permission for route

    Usage:
        @app.route('/api/standards', methods=['POST'])
        @login_required
        @permission_required('standards', 'CREATE')
        def create_standard():
            return "Standard created"

    Args:
        resource: Resource type (projects, standards, users, etc.)
        action: Action to perform (CREATE, READ, UPDATE, DELETE, etc.)

    Returns:
        - HTTP 403 if user doesn't have required permission
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # login_required should be applied first
            if not hasattr(g, 'current_user') or not g.current_user:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth_login'))

            # Check permission
            if not rbac_service.has_permission(g.current_user, resource, action):
                # Audit log for access denied
                auth_service.create_audit_log(
                    'ACCESS_DENIED',
                    table_name=resource,
                    success=False,
                    error_message=f'Missing permission: {resource}:{action}'
                )

                if request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'You do not have permission to {action} {resource}',
                        'required_permission': f'{resource}:{action}'
                    }), 403

                return f"<h1>403 Forbidden</h1><p>You don't have permission to {action} {resource}</p>", 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def project_permission_required(access_level: str = 'READ') -> Callable:
    """
    Decorator to require project-level permission

    Usage:
        @app.route('/projects/<project_id>/data', methods=['GET'])
        @login_required
        @project_permission_required('READ')
        def get_project_data(project_id):
            return "Project data"

        @app.route('/projects/<project_id>/data', methods=['POST'])
        @login_required
        @project_permission_required('WRITE')
        def update_project_data(project_id):
            return "Data updated"

    Args:
        access_level: Required access level (READ, WRITE, ADMIN)

    Returns:
        - HTTP 403 if user doesn't have required project access
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # login_required should be applied first
            if not hasattr(g, 'current_user') or not g.current_user:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth_login'))

            # Get project_id from route parameters
            project_id = kwargs.get('project_id')
            if not project_id:
                # Try to get from request args or JSON body
                project_id = request.args.get('project_id') or (
                    request.get_json(silent=True) or {}).get('project_id')

            if not project_id:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Missing project_id parameter'}), 400
                return "Bad Request: Missing project_id", 400

            # Admins have access to all projects
            if g.current_user.get('role') == 'ADMIN':
                return f(*args, **kwargs)

            # Check project-specific permission
            has_access = rbac_service.has_project_access(
                g.current_user['user_id'],
                project_id,
                access_level
            )

            if not has_access:
                # Audit log for access denied
                auth_service.create_audit_log(
                    'ACCESS_DENIED',
                    table_name='projects',
                    record_id=project_id,
                    project_id=project_id,
                    success=False,
                    error_message=f'No {access_level} access to project {project_id}'
                )

                if request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'You do not have {access_level} access to this project',
                        'project_id': project_id,
                        'required_access_level': access_level
                    }), 403

                return f"<h1>403 Forbidden</h1><p>You don't have {access_level} access to this project</p>", 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for routes that work with or without authentication
    If user is authenticated, sets g.current_user, otherwise sets None

    Usage:
        @app.route('/public-with-optional-features')
        @optional_auth
        def public_route():
            if g.current_user:
                return "Logged in view"
            else:
                return "Public view"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            user = auth_service.get_current_user()
            g.current_user = user if user and user.get('is_active') else None
        else:
            g.current_user = None

        return f(*args, **kwargs)

    return decorated_function


def api_key_or_login_required(f: Callable) -> Callable:
    """
    Decorator that accepts either session authentication or API key
    Useful for API endpoints that need to support both web and programmatic access

    Usage:
        @app.route('/api/data')
        @api_key_or_login_required
        def get_data():
            return jsonify(data)

    Checks:
        1. Session-based authentication (cookie)
        2. API key in Authorization header
        3. API key in query parameter
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Try session authentication first
        if 'user_id' in session:
            user = auth_service.get_current_user()
            if user and user.get('is_active'):
                g.current_user = user
                return f(*args, **kwargs)

        # Try API key authentication
        # Check Authorization header
        api_key = request.headers.get('Authorization')
        if api_key and api_key.startswith('Bearer '):
            api_key = api_key[7:]  # Remove 'Bearer ' prefix

        # Check query parameter
        if not api_key:
            api_key = request.args.get('api_key')

        if api_key:
            # TODO: Implement API key validation
            # For now, just deny
            return jsonify({
                'error': 'API key authentication not yet implemented',
                'message': 'Please use session-based authentication'
            }), 501

        # No valid authentication found
        return jsonify({
            'error': 'Authentication required',
            'message': 'Please log in or provide a valid API key'
        }), 401

    return decorated_function
