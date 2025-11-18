# ACAD-GIS Authentication & Authorization Implementation Guide

## 📋 Executive Summary

This document describes the comprehensive authentication and authorization system implemented for ACAD-GIS. The system provides:

- ✅ **Replit Auth Integration** - OAuth-based authentication
- ✅ **Role-Based Access Control (RBAC)** - 3 roles (Admin, Engineer, Viewer)
- ✅ **Project-Level Permissions** - Fine-grained access control
- ✅ **Comprehensive Audit Logging** - Track all user actions
- ✅ **Session Management** - Secure session tracking
- ✅ **Decorator-Based Protection** - Easy route protection

## 📂 Files Created

### Database Schema
- `database/migrations/031_create_auth_tables.sql` - Complete database schema
- `database/migrations/031_EXECUTE_INSTRUCTIONS.md` - Migration guide

### Services
- `services/auth_service.py` - Core authentication service
- `services/rbac_service.py` - Role-based access control service

### Auth Module
- `auth/__init__.py` - Module initialization
- `auth/decorators.py` - Route protection decorators
- `auth/routes.py` - Authentication routes (login, logout, profile, user management)

### Templates
- `templates/auth/error.html` - Authentication error page
- `templates/auth/profile.html` - User profile page
- `templates/auth/users.html` - User management interface (admin)
- `templates/auth/audit_log.html` - Audit log viewer (admin)

## 🗄️ Database Schema

### Tables Created
1. **users** - User accounts with Replit Auth integration
2. **project_permissions** - Project-level access control
3. **audit_log** - Comprehensive audit trail
4. **user_sessions** - Active session tracking

### Helper Functions
- `update_updated_at_column()` - Auto-update timestamps
- `cleanup_expired_sessions()` - Remove expired sessions
- `user_has_project_access()` - Check project permissions

### Views
- `active_user_sessions` - Current active sessions with metrics
- `user_activity_summary` - User activity statistics
- `recent_audit_events` - Recent audit entries (7 days)

## 🔐 Security Features

### Authentication
- **OAuth 2.0** via Replit Auth
- **CSRF Protection** with state tokens
- **Session Management** with configurable timeout (default: 8 hours)
- **Automatic Logout** on account deactivation

### Authorization
- **Role-Based Access Control (RBAC)**
  - **Admin**: Full system access
  - **Engineer**: Read/write data, no user management
  - **Viewer**: Read-only access

- **Project-Level Permissions**
  - **READ**: View project data
  - **WRITE**: Edit project data
  - **ADMIN**: Manage project permissions

### Audit Logging
- All user actions logged (LOGIN, LOGOUT, CREATE, UPDATE, DELETE)
- Failed authentication attempts tracked
- Permission denials recorded
- IP address and user agent captured
- JSON snapshots of old/new values for changes

## 🚀 Integration Guide

### Step 1: Run Database Migration

```bash
# Option 1: Direct SQL execution
psql "$DATABASE_URL" -f database/migrations/031_create_auth_tables.sql

# Option 2: Using Python
python3 -c "
from database import execute_query
with open('database/migrations/031_create_auth_tables.sql', 'r') as f:
    execute_query(f.read())
print('Migration completed')
"
```

### Step 2: Configure Environment Variables

Create/update `.env` file:

```bash
# Replit Auth Configuration
REPLIT_CLIENT_ID=your_replit_client_id
REPLIT_CLIENT_SECRET=your_replit_client_secret

# Session Configuration
SESSION_TIMEOUT_HOURS=8
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Initial Admin Email (first user with this email becomes admin)
INITIAL_ADMIN_EMAIL=your.email@company.com

# Flask Secret Key (must be set)
SECRET_KEY=your-secret-key-here
```

### Step 3: Register Auth Blueprint in app.py

Add to `app.py`:

```python
from auth.routes import auth_bp

# Register auth blueprint
app.register_blueprint(auth_bp)

# Configure permanent session lifetime
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=int(os.getenv('SESSION_TIMEOUT_HOURS', '8')))
```

### Step 4: Protect Routes with Decorators

#### Example 1: Require Login
```python
from auth.decorators import login_required

@app.route('/protected')
@login_required
def protected_route():
    # Access current user via g.current_user
    return f"Hello, {g.current_user['username']}!"
```

#### Example 2: Require Role
```python
from auth.decorators import login_required, role_required

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
```

#### Example 3: Require Project Permission
```python
from auth.decorators import login_required, project_permission_required

@app.route('/projects/<project_id>/data', methods=['GET'])
@login_required
@project_permission_required('READ')
def get_project_data(project_id):
    return jsonify(data)

@app.route('/projects/<project_id>/data', methods=['POST'])
@login_required
@project_permission_required('WRITE')
def update_project_data(project_id):
    return jsonify({'message': 'Updated'})
```

#### Example 4: Require Specific Permission
```python
from auth.decorators import login_required, permission_required

@app.route('/api/standards', methods=['POST'])
@login_required
@permission_required('standards', 'CREATE')
def create_standard():
    return jsonify({'message': 'Standard created'})
```

### Step 5: Update Base Template

Add authentication UI elements to `templates/base.html`:

```html
<!-- In navbar -->
{% if session.get('user_id') %}
    <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
            <i class="fas fa-user-circle"></i> {{ session.get('username') }}
        </a>
        <ul class="dropdown-menu">
            <li><a class="dropdown-item" href="{{ url_for('auth.profile') }}">
                <i class="fas fa-user"></i> Profile
            </a></li>
            {% if session.get('role') == 'ADMIN' %}
            <li><a class="dropdown-item" href="{{ url_for('auth.list_users') }}">
                <i class="fas fa-users-cog"></i> User Management
            </a></li>
            <li><a class="dropdown-item" href="{{ url_for('auth.audit_log') }}">
                <i class="fas fa-clipboard-list"></i> Audit Log
            </a></li>
            {% endif %}
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}">
                <i class="fas fa-sign-out-alt"></i> Logout
            </a></li>
        </ul>
    </li>
{% else %}
    <li class="nav-item">
        <a class="nav-link" href="{{ url_for('auth.login') }}">
            <i class="fas fa-sign-in-alt"></i> Login
        </a>
    </li>
{% endif %}
```

### Step 6: Add Audit Logging to Existing Routes

For data modification routes, add audit logging:

```python
from services.auth_service import auth_service

@app.route('/api/projects', methods=['POST'])
@login_required
@permission_required('projects', 'CREATE')
def create_project():
    data = request.get_json()

    # Create project
    project_id = create_project_in_db(data)

    # Audit log
    auth_service.create_audit_log(
        'CREATE',
        table_name='projects',
        record_id=project_id,
        new_values=data,
        project_id=project_id,
        success=True
    )

    return jsonify({'project_id': project_id})
```

## 📊 Role Permission Matrix

| Resource | Admin | Engineer | Viewer |
|----------|-------|----------|--------|
| **Projects** | CREATE, READ, UPDATE, DELETE, MANAGE_PERMISSIONS | CREATE, READ, UPDATE | READ |
| **Users** | CREATE, READ, UPDATE, DELETE, CHANGE_ROLE | READ | - |
| **Standards** | CREATE, READ, UPDATE, DELETE | READ, UPDATE | READ |
| **Reference Data** | CREATE, READ, UPDATE, DELETE | READ | READ |
| **Audit Log** | READ | - | - |
| **DXF Import/Export** | IMPORT, EXPORT | IMPORT, EXPORT | EXPORT |
| **GIS Operations** | READ, WRITE, EXPORT | READ, WRITE, EXPORT | READ, EXPORT |
| **Relationships** | CREATE, READ, UPDATE, DELETE | CREATE, READ, UPDATE, DELETE | READ |
| **AI Tools** | READ, WRITE | READ, WRITE | READ |

## 🔑 API Endpoints

### Authentication
- `GET /auth/login` - Initiate OAuth login
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout current user
- `GET /auth/check` - Check authentication status (AJAX)

### User Management (Admin Only)
- `GET /auth/users` - List all users
- `POST /auth/users/<user_id>/role` - Update user role
- `POST /auth/users/<user_id>/deactivate` - Deactivate user
- `POST /auth/users/<user_id>/activate` - Activate user

### Profile
- `GET /auth/profile` - View user profile and statistics

### Audit Log (Admin Only)
- `GET /auth/audit-log` - View audit log with filters
  - Query params: `action`, `table_name`, `user_id`, `project_id`, `limit`

## 🧪 Testing Checklist

### Phase 1: Authentication Flow
- [ ] User can initiate login via `/auth/login`
- [ ] OAuth redirects to Replit Auth
- [ ] OAuth callback creates user session
- [ ] User information stored in database
- [ ] Session persists across requests
- [ ] User can logout via `/auth/logout`
- [ ] Unauthenticated users redirected to login
- [ ] Login audit log entries created

### Phase 2: Role-Based Access Control
- [ ] Admin can access admin pages
- [ ] Engineer blocked from admin pages
- [ ] Viewer has read-only access
- [ ] Role-based permission checks work
- [ ] Invalid role returns 403 Forbidden
- [ ] Permission denied logged in audit

### Phase 3: Project Permissions
- [ ] Admin sees all projects
- [ ] Users see only accessible projects
- [ ] Project permission checks work
- [ ] Access levels enforced (READ < WRITE < ADMIN)
- [ ] Permission expiration works
- [ ] No project access returns 403

### Phase 4: Audit Logging
- [ ] Login/logout actions logged
- [ ] CREATE operations logged with new values
- [ ] UPDATE operations logged with old/new values
- [ ] DELETE operations logged with old values
- [ ] Failed login attempts logged
- [ ] Permission denials logged
- [ ] Audit log searchable by filters

### Phase 5: User Management
- [ ] Admin can list all users
- [ ] Admin can change user roles
- [ ] Admin can deactivate users
- [ ] Admin can activate users
- [ ] Deactivated users cannot login
- [ ] Active sessions invalidated on deactivation

## 📈 Usage Examples

### Example 1: Protecting All Routes

```python
# Protect all routes by default
from auth.decorators import login_required

# Apply to multiple routes
protected_routes = [
    '/projects',
    '/standards',
    '/data-manager',
    '/tools',
    '/reports'
]

for route_path in protected_routes:
    # Get existing view function
    view_func = app.view_functions.get(route_path.lstrip('/').replace('/', '_'))
    if view_func:
        # Wrap with login_required
        app.view_functions[route_path.lstrip('/').replace('/', '_')] = login_required(view_func)
```

### Example 2: Checking Permissions in Code

```python
from flask import g
from services.rbac_service import rbac_service

@app.route('/api/standards/<standard_id>', methods=['PUT'])
@login_required
def update_standard(standard_id):
    user = g.current_user

    # Check if user can update standards
    if not rbac_service.has_permission(user, 'standards', 'UPDATE'):
        return jsonify({'error': 'No permission to update standards'}), 403

    # Proceed with update
    ...
```

### Example 3: Getting User's Projects

```python
from services.rbac_service import rbac_service

@app.route('/api/my-projects')
@login_required
def get_my_projects():
    user_id = g.current_user['user_id']

    # Get projects user has access to
    projects = rbac_service.get_user_projects(user_id, min_access_level='READ')

    return jsonify({'projects': projects})
```

### Example 4: Granting Project Access

```python
from services.rbac_service import rbac_service
from services.auth_service import auth_service

@app.route('/api/projects/<project_id>/grant-access', methods=['POST'])
@login_required
@role_required('ADMIN')
def grant_access(project_id):
    data = request.get_json()
    user_id = data['user_id']
    access_level = data['access_level']  # READ, WRITE, ADMIN

    # Grant permission
    permission = rbac_service.grant_project_permission(
        user_id=user_id,
        project_id=project_id,
        access_level=access_level,
        granted_by=g.current_user['user_id'],
        expires_at=data.get('expires_at'),
        notes=data.get('notes')
    )

    # Audit log
    auth_service.create_audit_log(
        'GRANT_PERMISSION',
        table_name='project_permissions',
        record_id=permission['permission_id'],
        project_id=project_id,
        new_values=permission,
        success=True
    )

    return jsonify(permission)
```

## 🛠️ Maintenance

### Session Cleanup

Schedule periodic cleanup of expired sessions:

```python
# In app.py or background job
from services.auth_service import auth_service

# Run every hour
deleted_count = auth_service.cleanup_expired_sessions()
print(f"Cleaned up {deleted_count} expired sessions")
```

### Audit Log Retention

Consider archiving old audit logs:

```sql
-- Archive logs older than 1 year
CREATE TABLE audit_log_archive AS
SELECT * FROM audit_log
WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';

DELETE FROM audit_log
WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 year';
```

## 🔒 Security Best Practices

1. **Always use HTTPS in production**
2. **Set secure session cookies** (`SESSION_COOKIE_SECURE=true`)
3. **Rotate session keys** periodically
4. **Monitor failed login attempts** for brute force attacks
5. **Review audit logs** regularly for suspicious activity
6. **Implement rate limiting** on login endpoint
7. **Set strong session timeout** (8 hours recommended)
8. **Never log passwords** or sensitive data
9. **Validate all user input** before database operations
10. **Keep dependencies updated** for security patches

## 📝 Next Steps

1. **Run database migration** to create auth tables
2. **Configure environment variables** with Replit Auth credentials
3. **Register auth blueprint** in app.py
4. **Apply decorators** to existing routes systematically
5. **Update base template** with auth UI elements
6. **Test authentication flow** end-to-end
7. **Deploy to production** with HTTPS

## 🐛 Troubleshooting

### Issue: "Module not found: psycopg2"
```bash
pip install psycopg2-binary python-dotenv
```

### Issue: "Database connection failed"
Check environment variables:
```bash
echo $PGHOST $PGDATABASE $PGUSER
```

### Issue: "Replit Auth failed"
Verify Replit Auth credentials in `.env`:
- `REPLIT_CLIENT_ID` must be set
- `REPLIT_CLIENT_SECRET` must be set
- Callback URL must match registered URL in Replit

### Issue: "Session not persisting"
Check Flask SECRET_KEY:
```python
print(app.config['SECRET_KEY'])  # Should not be None
```

### Issue: "Permission denied for all users"
Check user role in database:
```sql
SELECT username, role, is_active FROM users;
```

## 📚 References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Replit Auth Documentation](https://docs.replit.com/power-ups/auth)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

---

**Implementation Date**: 2025-11-18
**Version**: 1.0
**Status**: Complete - Core functionality implemented, ready for integration
