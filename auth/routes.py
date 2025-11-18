"""
Authentication Routes for ACAD-GIS
Handles login, logout, and OAuth callbacks
"""

import secrets
from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash, g
from services.auth_service import auth_service
from services.rbac_service import rbac_service
from auth.decorators import login_required, role_required

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """
    Initiate Replit Auth login flow
    Redirects to Replit OAuth authorization page
    """
    # Store next URL in session for redirect after login
    next_url = request.args.get('next', url_for('index'))
    session['next_url'] = next_url

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Get OAuth authorization URL
    redirect_uri = url_for('auth.callback', _external=True)
    auth_url = auth_service.get_auth_url(redirect_uri)

    # Add state parameter for CSRF protection
    auth_url += f"&state={state}"

    return redirect(auth_url)


@auth_bp.route('/callback')
def callback():
    """
    Handle OAuth callback from Replit
    Exchanges authorization code for access token and creates user session
    """
    # Verify state parameter for CSRF protection
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        auth_service.create_audit_log(
            'LOGIN_FAILED',
            success=False,
            error_message='Invalid state parameter (CSRF protection)'
        )
        return render_template('auth/error.html',
                             error='Invalid authentication request',
                             message='Security token mismatch. Please try again.'), 400

    # Get authorization code
    code = request.args.get('code')
    if not code:
        error = request.args.get('error', 'unknown_error')
        error_description = request.args.get('error_description', 'No authorization code received')

        auth_service.create_audit_log(
            'LOGIN_FAILED',
            success=False,
            error_message=f'{error}: {error_description}'
        )

        return render_template('auth/error.html',
                             error='Authentication failed',
                             message=error_description), 400

    # Exchange code for access token
    redirect_uri = url_for('auth.callback', _external=True)
    access_token = auth_service.exchange_code_for_token(code, redirect_uri)

    if not access_token:
        auth_service.create_audit_log(
            'LOGIN_FAILED',
            success=False,
            error_message='Failed to exchange code for token'
        )
        return render_template('auth/error.html',
                             error='Authentication failed',
                             message='Could not obtain access token from Replit'), 500

    # Get user info from Replit
    replit_user = auth_service.get_replit_user_info(access_token)

    if not replit_user:
        auth_service.create_audit_log(
            'LOGIN_FAILED',
            success=False,
            error_message='Failed to get user info from Replit'
        )
        return render_template('auth/error.html',
                             error='Authentication failed',
                             message='Could not retrieve user information from Replit'), 500

    # Create or update user in database
    user = auth_service.create_or_update_user(replit_user)

    if not user:
        auth_service.create_audit_log(
            'LOGIN_FAILED',
            success=False,
            error_message='Failed to create/update user in database'
        )
        return render_template('auth/error.html',
                             error='Login failed',
                             message='Could not create user account'), 500

    # Check if user is active
    if not user.get('is_active'):
        auth_service.create_audit_log(
            'LOGIN_FAILED',
            success=False,
            error_message='User account is deactivated'
        )
        return render_template('auth/error.html',
                             error='Account deactivated',
                             message='Your account has been deactivated. Please contact an administrator.'), 403

    # Generate session token
    session_token = secrets.token_urlsafe(64)

    # Store user info in session
    session.permanent = True  # Use permanent session for remember me
    session['user_id'] = str(user['user_id'])
    session['username'] = user['username']
    session['email'] = user['email']
    session['role'] = user['role']
    session['session_token'] = session_token

    # Create session in database
    auth_service.create_session(user['user_id'], session_token)

    # Audit log for successful login
    auth_service.create_audit_log('LOGIN', success=True)

    # Clean up OAuth state
    session.pop('oauth_state', None)

    # Redirect to next URL or home
    next_url = session.pop('next_url', url_for('index'))

    # Add welcome flash message
    flash(f"Welcome back, {user['username']}!", 'success')

    return redirect(next_url)


@auth_bp.route('/logout')
def logout():
    """
    Log out current user
    Clears session and invalidates session token
    """
    # Invalidate session in database
    if 'session_token' in session:
        auth_service.invalidate_session(session['session_token'])

    # Audit log for logout
    auth_service.create_audit_log('LOGOUT', success=True)

    # Clear session
    session.clear()

    flash('You have been logged out successfully', 'info')

    return redirect(url_for('index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """
    Show user profile page
    """
    user = g.current_user

    # Get user statistics
    stats = rbac_service.get_user_stats(user['user_id'])

    # Get projects user has access to
    projects = rbac_service.get_user_projects(user['user_id'])

    # Get active sessions
    from database import execute_query
    sessions_result = execute_query("""
        SELECT
            session_id,
            created_at,
            expires_at,
            last_activity,
            ip_address,
            user_agent
        FROM user_sessions
        WHERE user_id = %s AND is_active = true AND expires_at > CURRENT_TIMESTAMP
        ORDER BY last_activity DESC
    """, (user['user_id'],))

    active_sessions = [dict(row) for row in sessions_result] if sessions_result else []

    return render_template('auth/profile.html',
                         user=user,
                         stats=stats,
                         projects=projects,
                         active_sessions=active_sessions)


@auth_bp.route('/users')
@login_required
@role_required('ADMIN')
def list_users():
    """
    List all users (admin only)
    """
    users = rbac_service.get_all_users()

    # Get stats for each user
    for user in users:
        user['stats'] = rbac_service.get_user_stats(user['user_id'])

    return render_template('auth/users.html', users=users)


@auth_bp.route('/users/<user_id>/role', methods=['POST'])
@login_required
@role_required('ADMIN')
def update_user_role(user_id):
    """
    Update user role (admin only)
    """
    data = request.get_json() or request.form

    new_role = data.get('role')
    if not new_role or new_role not in ['ADMIN', 'ENGINEER', 'VIEWER']:
        return jsonify({'error': 'Invalid role'}), 400

    # Get old role for audit
    from database import execute_query
    result = execute_query("SELECT role FROM users WHERE user_id = %s", (user_id,))
    old_role = result[0]['role'] if result else None

    # Update role
    success = rbac_service.update_user_role(user_id, new_role)

    if success:
        # Audit log
        auth_service.create_audit_log(
            'CHANGE_ROLE',
            table_name='users',
            record_id=user_id,
            old_values={'role': old_role},
            new_values={'role': new_role},
            success=True
        )

        return jsonify({'message': 'Role updated successfully', 'new_role': new_role})
    else:
        return jsonify({'error': 'Failed to update role'}), 500


@auth_bp.route('/users/<user_id>/deactivate', methods=['POST'])
@login_required
@role_required('ADMIN')
def deactivate_user(user_id):
    """
    Deactivate user account (admin only)
    """
    # Prevent self-deactivation
    if user_id == g.current_user['user_id']:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400

    success = rbac_service.deactivate_user(user_id)

    if success:
        auth_service.create_audit_log(
            'DEACTIVATE_USER',
            table_name='users',
            record_id=user_id,
            success=True
        )
        return jsonify({'message': 'User deactivated successfully'})
    else:
        return jsonify({'error': 'Failed to deactivate user'}), 500


@auth_bp.route('/users/<user_id>/activate', methods=['POST'])
@login_required
@role_required('ADMIN')
def activate_user(user_id):
    """
    Activate user account (admin only)
    """
    success = rbac_service.activate_user(user_id)

    if success:
        auth_service.create_audit_log(
            'ACTIVATE_USER',
            table_name='users',
            record_id=user_id,
            success=True
        )
        return jsonify({'message': 'User activated successfully'})
    else:
        return jsonify({'error': 'Failed to activate user'}), 500


@auth_bp.route('/audit-log')
@login_required
@role_required('ADMIN')
def audit_log():
    """
    View audit log (admin only)
    """
    # Get filter parameters
    user_id = request.args.get('user_id')
    action = request.args.get('action')
    table_name = request.args.get('table_name')
    project_id = request.args.get('project_id')
    limit = int(request.args.get('limit', 100))

    # Get audit logs
    logs = auth_service.get_audit_logs(
        user_id=user_id,
        action=action,
        table_name=table_name,
        project_id=project_id,
        limit=limit
    )

    # Get unique actions for filter dropdown
    from database import execute_query
    actions_result = execute_query("""
        SELECT DISTINCT action FROM audit_log ORDER BY action
    """)
    actions = [row['action'] for row in actions_result] if actions_result else []

    return render_template('auth/audit_log.html',
                         logs=logs,
                         actions=actions,
                         current_filters={
                             'action': action,
                             'table_name': table_name,
                             'user_id': user_id,
                             'project_id': project_id
                         })


@auth_bp.route('/check')
def check_auth():
    """
    Check authentication status (useful for AJAX)
    """
    if 'user_id' in session:
        user = auth_service.get_current_user()
        if user and user.get('is_active'):
            return jsonify({
                'authenticated': True,
                'user': {
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                }
            })

    return jsonify({'authenticated': False})
