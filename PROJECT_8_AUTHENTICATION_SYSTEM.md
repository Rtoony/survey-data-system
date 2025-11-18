# Project 8: Authentication & Authorization System - Security Foundation

## Executive Summary
Implement comprehensive authentication and role-based access control (RBAC) for ACAD-GIS using Replit Auth integration. Transform the currently open system into a secure, multi-user environment with Admin/Engineer/Viewer roles, project-level permissions, audit logging, and session management. This 4-week project establishes the security foundation for enterprise deployment.

## Current State Assessment

### ⚠️ Security Gaps
1. **No Authentication**: System is wide open (TODO comment at line 18748: `# TODO: Add authentication when app-wide auth strategy is implemented`)
2. **No Authorization**: Any user can access/modify any data
3. **No Audit Trail**: No logging of who changed what
4. **No Session Management**: No user context tracking
5. **No Project Permissions**: Can't restrict access to specific projects
6. **No API Security**: All API endpoints unprotected

### ✅ What Exists
1. **Replit Platform**: Built-in authentication service available
2. **User-Aware Tables**: Some tables have `created_by` fields (ready for user IDs)
3. **Flask Framework**: Middleware support for auth decorators
4. **PostgreSQL**: Role/permission tables ready to add

### Current Workflow (Insecure)
```
User opens ACAD-GIS → Full access to everything
User modifies project → No record of who made changes
User deletes data → No audit trail
```

### Target Workflow (Secure)
```
User opens ACAD-GIS → Redirects to Replit Auth login
User authenticates → Session created with role (Admin/Engineer/Viewer)
User browses projects → Only sees projects they have access to
User modifies project → Change logged with user ID, timestamp, action
Admin manages permissions → Grant/revoke project access per user
```

## Goals & Objectives

### Primary Goals
1. **Implement Replit Auth**: Integrate native authentication service
2. **Role-Based Access Control**: 3 roles (Admin, Engineer, Viewer)
3. **Project-Level Permissions**: Fine-grained access control
4. **Audit Logging**: Track all data modifications
5. **Session Management**: Secure user context across requests
6. **Protected API Endpoints**: Decorator-based auth enforcement

### Success Metrics
- 100% of pages require authentication
- 100% of write API endpoints check permissions
- Audit log captures all CREATE/UPDATE/DELETE operations
- Admins can manage user access via UI
- Session timeout configurable (default 8 hours)
- Zero security vulnerabilities in penetration test

## Technical Architecture

### Database Schema

```sql
-- ==========================================
-- USERS & AUTHENTICATION
-- ==========================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    replit_user_id VARCHAR(255) UNIQUE NOT NULL,  -- From Replit Auth
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(200),
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',  -- ADMIN, ENGINEER, VIEWER
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_replit_id ON users(replit_user_id);
CREATE INDEX idx_users_role ON users(role);

-- ==========================================
-- PROJECT PERMISSIONS
-- ==========================================

CREATE TABLE project_permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    access_level VARCHAR(20) NOT NULL,  -- READ, WRITE, ADMIN
    granted_by UUID REFERENCES users(user_id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Optional expiration
    UNIQUE(user_id, project_id)
);

CREATE INDEX idx_project_perms_user ON project_permissions(user_id);
CREATE INDEX idx_project_perms_project ON project_permissions(project_id);

-- ==========================================
-- AUDIT LOG
-- ==========================================

CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_table ON audit_log(table_name);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);

-- ==========================================
-- SESSIONS
-- ==========================================

CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
```

### Role Definitions

```python
# models/roles.py

from enum import Enum

class UserRole(str, Enum):
    ADMIN = 'ADMIN'
    ENGINEER = 'ENGINEER'
    VIEWER = 'VIEWER'

class AccessLevel(str, Enum):
    READ = 'READ'
    WRITE = 'WRITE'
    ADMIN = 'ADMIN'

ROLE_PERMISSIONS = {
    'ADMIN': {
        'projects': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
        'users': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
        'standards': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
        'reference_data': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
        'audit_log': ['READ'],
    },
    'ENGINEER': {
        'projects': ['CREATE', 'READ', 'UPDATE'],
        'users': ['READ'],  # Can see other users
        'standards': ['READ', 'UPDATE'],
        'reference_data': ['READ'],
        'audit_log': [],  # No access
    },
    'VIEWER': {
        'projects': ['READ'],
        'users': [],  # Can't see other users
        'standards': ['READ'],
        'reference_data': ['READ'],
        'audit_log': [],
    }
}
```

### Replit Auth Integration

```python
# services/auth_service.py

from flask import session, redirect, url_for, request
from functools import wraps
import requests
import os

class AuthService:
    def __init__(self):
        self.replit_auth_url = 'https://replit.com/auth'
        self.client_id = os.getenv('REPLIT_CLIENT_ID')
        self.client_secret = os.getenv('REPLIT_CLIENT_SECRET')
    
    def login_required(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    
    def role_required(self, *roles):
        """Decorator to require specific role"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    return redirect(url_for('login'))
                
                user = self.get_current_user()
                if user['role'] not in roles:
                    return {'error': 'Insufficient permissions'}, 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def project_permission_required(self, project_id, access_level='READ'):
        """Decorator to check project-level permissions"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user = self.get_current_user()
                
                # Admins have access to everything
                if user['role'] == 'ADMIN':
                    return f(*args, **kwargs)
                
                # Check project-specific permissions
                if not self.has_project_access(user['user_id'], project_id, access_level):
                    return {'error': 'No access to this project'}, 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def get_current_user(self):
        """Get current authenticated user from session"""
        if 'user_id' not in session:
            return None
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE user_id = %s", (session['user_id'],))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
    
    def has_project_access(self, user_id, project_id, required_level='READ'):
        """Check if user has access to project"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT access_level
            FROM project_permissions
            WHERE user_id = %s AND project_id = %s
              AND (expires_at IS NULL OR expires_at > NOW())
        """, (user_id, project_id))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return False
        
        access_level = result[0]
        
        # Check if access level meets requirement
        level_hierarchy = ['READ', 'WRITE', 'ADMIN']
        user_level_idx = level_hierarchy.index(access_level)
        required_level_idx = level_hierarchy.index(required_level)
        
        return user_level_idx >= required_level_idx
    
    def create_audit_log(self, action, table_name=None, record_id=None, 
                         old_values=None, new_values=None):
        """Log user action to audit trail"""
        user = self.get_current_user()
        if not user:
            return
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO audit_log (
                user_id, action, table_name, record_id,
                old_values, new_values, ip_address, user_agent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user['user_id'],
            action,
            table_name,
            record_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            request.remote_addr,
            request.headers.get('User-Agent')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
```

### Flask Routes

```python
# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/login')
def login():
    """Initiate Replit Auth login"""
    redirect_uri = url_for('auth_callback', _external=True)
    auth_url = f"{auth_service.replit_auth_url}/authorize?client_id={auth_service.client_id}&redirect_uri={redirect_uri}"
    return redirect(auth_url)


@app.route('/auth/callback')
def auth_callback():
    """Handle Replit Auth callback"""
    code = request.args.get('code')
    
    # Exchange code for access token
    token_response = requests.post(
        f"{auth_service.replit_auth_url}/token",
        data={
            'client_id': auth_service.client_id,
            'client_secret': auth_service.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    
    token_data = token_response.json()
    access_token = token_data['access_token']
    
    # Get user info from Replit
    user_response = requests.get(
        'https://replit.com/api/user',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    replit_user = user_response.json()
    
    # Create or update user in database
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        INSERT INTO users (replit_user_id, username, email, full_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (replit_user_id) DO UPDATE SET
            last_login = NOW(),
            updated_at = NOW()
        RETURNING user_id, role
    """, (
        replit_user['id'],
        replit_user['username'],
        replit_user.get('email'),
        replit_user.get('name')
    ))
    
    user = cur.fetchone()
    
    # Create session
    session['user_id'] = str(user['user_id'])
    session['role'] = user['role']
    session['username'] = replit_user['username']
    
    # Log login
    auth_service.create_audit_log('LOGIN')
    
    conn.commit()
    cur.close()
    conn.close()
    
    next_url = request.args.get('next', url_for('index'))
    return redirect(next_url)


@app.route('/logout')
def logout():
    """Log out user"""
    auth_service.create_audit_log('LOGOUT')
    session.clear()
    return redirect(url_for('login'))


# ==========================================
# USER MANAGEMENT ROUTES
# ==========================================

@app.route('/api/users', methods=['GET'])
@auth_service.role_required('ADMIN')
def get_users():
    """Get all users (admin only)"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT user_id, username, email, full_name, role, 
               is_active, last_login, created_at
        FROM users
        ORDER BY username
    """)
    
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify([dict(row) for row in users])


@app.route('/api/users/<user_id>/role', methods=['PUT'])
@auth_service.role_required('ADMIN')
def update_user_role(user_id):
    """Update user role (admin only)"""
    data = request.json
    new_role = data['role']
    
    if new_role not in ['ADMIN', 'ENGINEER', 'VIEWER']:
        return {'error': 'Invalid role'}, 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get old role for audit
    cur.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
    old_role = cur.fetchone()[0]
    
    # Update role
    cur.execute("""
        UPDATE users SET role = %s, updated_at = NOW()
        WHERE user_id = %s
    """, (new_role, user_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Audit log
    auth_service.create_audit_log(
        'UPDATE',
        'users',
        user_id,
        old_values={'role': old_role},
        new_values={'role': new_role}
    )
    
    return {'message': 'Role updated successfully'}


# ==========================================
# PROJECT PERMISSIONS ROUTES
# ==========================================

@app.route('/api/projects/<project_id>/permissions', methods=['GET'])
@auth_service.role_required('ADMIN', 'ENGINEER')
def get_project_permissions(project_id):
    """Get users with access to project"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT 
            pp.permission_id,
            pp.access_level,
            pp.granted_at,
            pp.expires_at,
            u.username,
            u.email,
            u.role,
            gb.username as granted_by_username
        FROM project_permissions pp
        JOIN users u ON pp.user_id = u.user_id
        LEFT JOIN users gb ON pp.granted_by = gb.user_id
        WHERE pp.project_id = %s
        ORDER BY u.username
    """, (project_id,))
    
    permissions = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify([dict(row) for row in permissions])


@app.route('/api/projects/<project_id>/permissions', methods=['POST'])
@auth_service.role_required('ADMIN')
def grant_project_permission(project_id):
    """Grant user access to project"""
    data = request.json
    current_user = auth_service.get_current_user()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO project_permissions (
            user_id, project_id, access_level, granted_by, expires_at
        ) VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id, project_id) DO UPDATE SET
            access_level = EXCLUDED.access_level,
            granted_by = EXCLUDED.granted_by,
            expires_at = EXCLUDED.expires_at,
            granted_at = NOW()
    """, (
        data['user_id'],
        project_id,
        data['access_level'],
        current_user['user_id'],
        data.get('expires_at')
    ))
    
    conn.commit()
    cur.close()
    conn.close()
    
    auth_service.create_audit_log(
        'GRANT_PERMISSION',
        'project_permissions',
        project_id,
        new_values=data
    )
    
    return {'message': 'Permission granted successfully'}
```

### User Management UI

```html
<!-- templates/admin/user_management.html -->

{% extends "base.html" %}
{% block content %}
<div class="admin-container">
    <h1><i class="fas fa-users"></i> User Management</h1>
    
    <div class="users-table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Last Login</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="usersTableBody">
                <!-- Populated via JavaScript -->
            </tbody>
        </table>
    </div>
    
    <!-- Project Permissions Modal -->
    <div id="permissionsModal" class="modal">
        <div class="modal-content">
            <h2>Manage Project Access</h2>
            <div id="permissionsContent"></div>
        </div>
    </div>
</div>
{% endblock %}
```

## Implementation Phases

### Phase 1: Core Authentication (Week 1)

**Deliverables**:
1. Create database tables (users, sessions, audit_log)
2. Integrate Replit Auth
3. Implement login/logout flow
4. Session management
5. Basic `@login_required` decorator

**Testing**:
- User login via Replit Auth
- Session persists across requests
- Logout clears session
- Unauthorized users redirected to login

### Phase 2: RBAC & Decorators (Week 2)

**Deliverables**:
1. Implement 3 roles (Admin, Engineer, Viewer)
2. `@role_required` decorator
3. Role permissions matrix
4. Apply decorators to all routes
5. Role-based UI element hiding

**Testing**:
- Admin can access admin pages
- Engineer blocked from admin pages
- Viewer can only read
- API endpoints enforce role permissions

### Phase 3: Project Permissions (Week 3)

**Deliverables**:
1. Create `project_permissions` table
2. `@project_permission_required` decorator
3. Project access UI (grant/revoke)
4. Filter project lists by user access
5. Permission inheritance (Admin sees all)

**Testing**:
- User A can't access User B's private project
- Admin can grant access
- Access expiration works
- Revoked access blocks immediately

### Phase 4: Audit Logging & UI (Week 4)

**Deliverables**:
1. Audit log for all write operations
2. User management UI (admin only)
3. Audit log viewer
4. Permission management UI
5. User activity dashboard

**Testing**:
- All CREATE/UPDATE/DELETE operations logged
- Admin can view audit log
- Search/filter audit entries
- User activity trends displayed

## Success Criteria

### Must Have
- ✅ 100% of pages require authentication
- ✅ 3 roles implemented with permission matrix
- ✅ Project-level access control
- ✅ Audit log captures all write ops
- ✅ Admin UI for user/permission management

### Should Have
- ✅ Session timeout configurable
- ✅ Password-less auth (via Replit)
- ✅ User activity dashboard
- ✅ Audit log search/filter
- ✅ Permission expiration

### Nice to Have
- ✅ Two-factor authentication
- ✅ API key generation for external tools
- ✅ IP-based access restrictions
- ✅ Single Sign-On (SSO) support
- ✅ Granular permissions (table-level)

## Risk Assessment

### Security Risks
- **Session Hijacking**: Use secure cookies, HTTPS only
  - **Mitigation**: Flask session with SECRET_KEY, httponly cookies
- **Permission Bypass**: Decorator applied inconsistently
  - **Mitigation**: Automated tests for all protected routes
- **Audit Log Tampering**: Admins could delete logs
  - **Mitigation**: Write-only audit table, no DELETE permission

### User Experience Risks
- **Login Friction**: Extra step to access system
  - **Mitigation**: Remember me (30-day sessions), SSO
- **Permission Confusion**: Users don't know why access denied
  - **Mitigation**: Clear error messages, permission help text

## Dependencies
- Replit Auth service
- Flask-Session (server-side sessions)
- Secure SECRET_KEY environment variable

## Timeline
- **Week 1**: Core authentication
- **Week 2**: RBAC & decorators
- **Week 3**: Project permissions
- **Week 4**: Audit logging & UI

**Total Duration**: 4 weeks

## ROI & Business Value

### Security Benefits
- **Compliance**: Audit trail for SOC 2, HIPAA, etc.
- **Data Protection**: Prevent unauthorized access/modification
- **Accountability**: Know who changed what, when

### Enterprise Readiness
- **Multi-User Support**: Multiple engineers collaborate safely
- **Client Separation**: Project-level permissions for multi-client firms
- **Role Hierarchy**: Reflect organizational structure

### Integration with Other Projects
- **All Projects**: Authentication required before using any feature
- **Project #3 (Compliance Engine)**: Audit log feeds compliance reports
- **Project #1 (AI Agent)**: User context improves AI recommendations

## Post-Implementation Enhancements

### Future Phases
1. **API Keys**: Machine-to-machine authentication
2. **Fine-Grained Permissions**: Table/column-level access
3. **Approval Workflows**: Multi-step change approvals
4. **Activity Feeds**: Real-time user action streams
5. **Mobile App Auth**: OAuth for mobile clients

## Conclusion

Authentication is the foundation for enterprise deployment. This project transforms ACAD-GIS from a single-user tool into a secure, multi-user platform with role-based access control, project permissions, and comprehensive audit logging. The 4-week timeline delivers production-ready security.

**Recommended Start**: Immediately (critical security gap).
