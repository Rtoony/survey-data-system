# Authentication System Setup Guide

## 🎉 Status: Code Integration Complete!

The authentication system has been **fully implemented and integrated** into your app. All code is in place and ready to use once you configure your environment.

## ✅ What's Been Done

### 1. Core Services Implemented
- ✅ `services/auth_service.py` - Replit Auth integration, session management, audit logging
- ✅ `services/rbac_service.py` - Role-based access control service
- ✅ `auth/decorators.py` - Route protection decorators
- ✅ `auth/routes.py` - Authentication routes (login, logout, profile, admin)

### 2. Database Schema Created
- ✅ `database/migrations/031_create_auth_tables.sql` - Complete schema
  - `users` table (ADMIN, ENGINEER, VIEWER roles)
  - `project_permissions` table (READ, WRITE, ADMIN access levels)
  - `audit_log` table (comprehensive tracking)
  - `user_sessions` table (session management)

### 3. UI Integration Complete
- ✅ Auth blueprint registered in `app.py`
- ✅ User menu added to navbar (login/logout, profile, admin links)
- ✅ Role badges (ADMIN/ENGINEER/VIEWER) displayed
- ✅ Flash messages for auth feedback
- ✅ CSS styling for auth components
- ✅ Templates created:
  - `templates/auth/profile.html` - User profile page
  - `templates/auth/users.html` - User management (admin only)
  - `templates/auth/audit_log.html` - Audit log viewer (admin only)
  - `templates/auth/error.html` - Authentication error page

### 4. Security Features
- ✅ OAuth 2.0 via Replit Auth
- ✅ CSRF protection with state tokens
- ✅ Session management with configurable timeout
- ✅ Audit logging for all actions
- ✅ Role-based permissions
- ✅ Project-level access control

## 🚀 Next Steps: Configuration Required

### Step 1: Configure Database Connection

You need to set up your database credentials. Choose one option:

**Option A: Use Replit Secrets (Recommended)**
1. Open your Repl
2. Click on "Secrets" (lock icon) in the left sidebar
3. Add these secrets:
   ```
   PGHOST=your-database-host.supabase.co
   PGDATABASE=postgres
   PGUSER=postgres
   PGPASSWORD=your-database-password
   ```

**Option B: Create .env file**
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your database credentials

### Step 2: Run Database Migration

Once your database is configured, run the migration to create auth tables:

```bash
python3 -c "
from database import execute_query
with open('database/migrations/031_create_auth_tables.sql', 'r') as f:
    execute_query(f.read())
print('✅ Migration completed!')
"
```

Or use psql directly:
```bash
psql $DATABASE_URL -f database/migrations/031_create_auth_tables.sql
```

### Step 3: Configure Replit Auth

1. Go to https://replit.com/account/auth-apps
2. Create a new Auth App
3. Set callback URL to: `https://your-repl-name.your-username.repl.co/auth/callback`
4. Add the credentials to Replit Secrets or .env:
   ```
   REPLIT_CLIENT_ID=your_client_id
   REPLIT_CLIENT_SECRET=your_client_secret
   ```

### Step 4: Configure Initial Admin

Set the email address that should become admin on first login:

```bash
# Add to Replit Secrets or .env
INITIAL_ADMIN_EMAIL=your.email@company.com
```

The first user to log in with this email will automatically become an ADMIN.

### Step 5: Optional - Apply Login Requirements

The system is currently **optional auth** - users can browse without logging in. To require authentication:

1. Add `@login_required` decorator to routes in `app.py`:
   ```python
   from auth.decorators import login_required

   @app.route('/projects')
   @login_required
   def projects_page():
       return render_template('projects.html')
   ```

2. Add role-based restrictions:
   ```python
   from auth.decorators import login_required, role_required

   @app.route('/admin/settings')
   @login_required
   @role_required('ADMIN')
   def admin_settings():
       return render_template('admin_settings.html')
   ```

## 📖 How to Use

### Available Decorators

```python
from auth.decorators import (
    login_required,           # Require any authenticated user
    role_required,            # Require specific role(s)
    permission_required,      # Require specific permission
    project_permission_required, # Require project access
    optional_auth             # Optional auth (sets g.current_user)
)
```

### Usage Examples

```python
# Require login
@app.route('/dashboard')
@login_required
def dashboard():
    user = g.current_user
    return render_template('dashboard.html', user=user)

# Require admin role
@app.route('/admin/users')
@login_required
@role_required('ADMIN')
def admin_users():
    return render_template('admin/users.html')

# Require engineer or admin
@app.route('/projects/create')
@login_required
@role_required('ADMIN', 'ENGINEER')
def create_project():
    return render_template('create_project.html')

# Require project permission
@app.route('/projects/<project_id>/edit')
@login_required
@project_permission_required('WRITE')
def edit_project(project_id):
    return render_template('edit_project.html')

# Optional auth (works with or without login)
@app.route('/public')
@optional_auth
def public_page():
    if g.current_user:
        return f"Welcome {g.current_user['username']}!"
    else:
        return "Welcome guest!"
```

### Audit Logging

The system automatically logs authentication events. To log your own actions:

```python
from services.auth_service import auth_service

# Log a data modification
auth_service.create_audit_log(
    action='UPDATE',
    table_name='projects',
    record_id=project_id,
    old_values={'name': 'Old Name'},
    new_values={'name': 'New Name'},
    success=True
)
```

### User Management

Admins can manage users via:
- Web UI: `/auth/users`
- Programmatically:
  ```python
  from services.rbac_service import rbac_service

  # Change user role
  rbac_service.update_user_role(user_id, 'ENGINEER')

  # Grant project access
  rbac_service.grant_project_access(user_id, project_id, 'WRITE')
  ```

## 🎯 Role Permission Matrix

| Resource | ADMIN | ENGINEER | VIEWER |
|----------|-------|----------|--------|
| Projects | Full CRUD | Create, Read, Update | Read only |
| Users | Full CRUD | Read | No access |
| Standards | Full CRUD | Read, Update | Read only |
| Reference Data | Full CRUD | Read | Read only |
| Audit Log | Read | No access | No access |

## 🔒 Security Best Practices

1. **Always use HTTPS in production** - Set `SESSION_COOKIE_SECURE=true`
2. **Strong SECRET_KEY** - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Session timeout** - Default 8 hours, adjust via `SESSION_TIMEOUT_HOURS`
4. **Monitor audit log** - Check `/auth/audit-log` regularly for suspicious activity
5. **Regular session cleanup** - The `cleanup_expired_sessions()` function runs automatically

## 🐛 Troubleshooting

### Database Connection Failed
- Check your database credentials in Replit Secrets or .env
- Verify database is accessible: `psql $DATABASE_URL -c "SELECT 1;"`

### Migration Failed
- Ensure `projects` table exists (required for foreign key)
- Check PostgreSQL logs for detailed error messages
- Try running migration in smaller chunks

### Replit Auth Not Working
- Verify CLIENT_ID and CLIENT_SECRET are set
- Check callback URL matches exactly (including https://)
- Ensure your Repl is running on a public URL

### Users Can't Log In
- Check audit log for failed login attempts: `/auth/audit-log`
- Verify user account is active: `SELECT * FROM users WHERE email = 'user@example.com'`
- Check session settings in environment variables

## 📊 Verification Checklist

After setup, verify everything works:

- [ ] Database tables created (users, project_permissions, audit_log, user_sessions)
- [ ] User menu appears in navbar
- [ ] Can navigate to `/auth/login`
- [ ] Can log in via Replit Auth
- [ ] User profile shows at `/auth/profile`
- [ ] Admin can access `/auth/users` and `/auth/audit-log`
- [ ] Logout works and clears session
- [ ] Audit log captures login/logout events

## 📚 Additional Documentation

- `AUTH_IMPLEMENTATION_GUIDE.md` - Detailed implementation documentation
- `database/migrations/031_EXECUTE_INSTRUCTIONS.md` - Database migration guide
- `.env.example` - Environment variable template

## 🎊 You're Ready!

Once you complete the configuration steps above, your authentication system will be fully operational. The integration is complete - you just need to:

1. ✅ Configure database connection
2. ✅ Run migration
3. ✅ Configure Replit Auth
4. ✅ Set initial admin email
5. ✅ (Optional) Apply decorators to protect routes

Happy securing! 🔐
