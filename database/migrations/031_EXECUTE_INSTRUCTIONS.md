# Migration 031: Authentication & Authorization System

## Overview
This migration creates the complete authentication and authorization infrastructure for ACAD-GIS, including:
- User accounts with Replit Auth integration
- Role-based access control (RBAC)
- Project-level permissions
- Comprehensive audit logging
- Session management

## Tables Created
1. **users** - User accounts (ADMIN, ENGINEER, VIEWER roles)
2. **project_permissions** - Fine-grained project access control
3. **audit_log** - Comprehensive audit trail of all actions
4. **user_sessions** - Active session tracking and management

## Functions Created
- `update_updated_at_column()` - Auto-updates timestamps
- `cleanup_expired_sessions()` - Removes old sessions
- `user_has_project_access()` - Permission checking logic

## Views Created
- `active_user_sessions` - Current active sessions
- `user_activity_summary` - User activity metrics
- `recent_audit_events` - Recent audit trail (7 days)

## Execution Steps

### 1. Verify Prerequisites
```bash
# Ensure database connection is configured
cat .env | grep -E "(PGHOST|PGDATABASE|PGUSER)"

# Test database connection
psql "$DATABASE_URL" -c "SELECT version();"
```

### 2. Run Migration
```bash
# Execute SQL migration
psql "$DATABASE_URL" -f database/migrations/031_create_auth_tables.sql

# Or using the database.py utility
python3 -c "
from database import execute_query
with open('database/migrations/031_create_auth_tables.sql', 'r') as f:
    execute_query(f.read())
print('Migration completed successfully')
"
```

### 3. Verify Migration
```sql
-- Check tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('users', 'project_permissions', 'audit_log', 'user_sessions')
ORDER BY table_name;

-- Check indexes created
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('users', 'project_permissions', 'audit_log', 'user_sessions')
ORDER BY tablename, indexname;

-- Check initial admin user created
SELECT user_id, username, email, role, is_active
FROM users
WHERE username = 'admin';

-- Verify helper functions
SELECT proname, pg_get_functiondef(oid)
FROM pg_proc
WHERE proname IN ('update_updated_at_column', 'cleanup_expired_sessions', 'user_has_project_access');

-- Check views created
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('active_user_sessions', 'user_activity_summary', 'recent_audit_events');
```

### 4. Test Functionality
```sql
-- Test 1: Create a test user
INSERT INTO users (replit_user_id, username, email, role)
VALUES ('test-user-1', 'testuser', 'test@example.com', 'ENGINEER')
RETURNING *;

-- Test 2: Grant project permission (replace UUIDs with actual values)
INSERT INTO project_permissions (user_id, project_id, access_level, granted_by)
SELECT
    u.user_id,
    p.project_id,
    'WRITE',
    (SELECT user_id FROM users WHERE role = 'ADMIN' LIMIT 1)
FROM users u, projects p
WHERE u.username = 'testuser'
  AND p.project_name LIKE '%Test%'
LIMIT 1
RETURNING *;

-- Test 3: Create audit log entry
INSERT INTO audit_log (user_id, username, action, table_name, success)
SELECT user_id, username, 'LOGIN', NULL, true
FROM users WHERE username = 'testuser'
RETURNING *;

-- Test 4: Check if user has project access
SELECT user_has_project_access(
    (SELECT user_id FROM users WHERE username = 'testuser'),
    (SELECT project_id FROM projects LIMIT 1),
    'READ'
) AS has_read_access;

-- Test 5: View active sessions (should be empty initially)
SELECT * FROM active_user_sessions;

-- Test 6: View user activity summary
SELECT * FROM user_activity_summary;

-- Test 7: View recent audit events
SELECT * FROM recent_audit_events LIMIT 10;
```

## Post-Migration Configuration

### 1. Set Up Environment Variables
Add to `.env`:
```bash
# Replit Auth Configuration
REPLIT_CLIENT_ID=your_replit_client_id_here
REPLIT_CLIENT_SECRET=your_replit_client_secret_here

# Session Configuration
SESSION_TIMEOUT_HOURS=8
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Initial Admin Email (user with this email becomes admin on first login)
INITIAL_ADMIN_EMAIL=your.email@company.com
```

### 2. Configure First Admin User
The initial admin user will be created when the first person logs in via Replit Auth. To configure who becomes admin:

**Option A: Manual Database Update**
```sql
-- After first user logs in, promote them to admin
UPDATE users
SET role = 'ADMIN'
WHERE email = 'your.email@company.com';
```

**Option B: Application Logic**
The auth service will check `INITIAL_ADMIN_EMAIL` environment variable and auto-promote on first login.

### 3. Session Cleanup Scheduling
Schedule the cleanup function to run periodically:

**Option A: Application Startup**
```python
# In app.py startup
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_expired_sessions, 'interval', hours=1)
scheduler.start()
```

**Option B: Database Cron (if using pg_cron extension)**
```sql
SELECT cron.schedule('cleanup-sessions', '0 * * * *', 'SELECT cleanup_expired_sessions()');
```

**Option C: System Cron**
```bash
# Add to crontab
0 * * * * psql "$DATABASE_URL" -c "SELECT cleanup_expired_sessions();"
```

## Rollback Instructions
⚠️ **WARNING**: This will delete all user accounts, permissions, and audit logs!

```sql
-- Drop views
DROP VIEW IF EXISTS recent_audit_events CASCADE;
DROP VIEW IF EXISTS user_activity_summary CASCADE;
DROP VIEW IF EXISTS active_user_sessions CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS user_has_project_access(UUID, UUID, VARCHAR) CASCADE;
DROP FUNCTION IF EXISTS cleanup_expired_sessions() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Drop tables (cascades to foreign keys)
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS project_permissions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
```

## Security Considerations

### 1. Database Permissions
- Audit log should be INSERT and SELECT only (no UPDATE/DELETE)
- Consider separate database role for auth operations
- Use row-level security (RLS) if needed

### 2. Session Security
- Always use HTTPS in production
- Set `SESSION_COOKIE_SECURE=true`
- Set `SESSION_COOKIE_HTTPONLY=true`
- Configure appropriate session timeout

### 3. Audit Log Retention
- Implement log rotation or archival strategy
- Consider separate database/table for long-term audit storage
- Set up monitoring for failed login attempts

### 4. Password Policy (if adding password auth)
- Minimum 12 characters
- Require complexity (uppercase, lowercase, numbers, symbols)
- Prevent common passwords
- Implement rate limiting on login attempts

## Next Steps
1. ✅ Run migration
2. ✅ Verify tables and functions created
3. ✅ Configure environment variables
4. ✅ Set up initial admin user
5. ⏭️ Implement auth service (auth_service.py)
6. ⏭️ Create Flask routes (login, logout, callback)
7. ⏭️ Apply decorators to protect routes
8. ⏭️ Build user management UI

## Support
For issues or questions:
- Check migration logs: `psql "$DATABASE_URL" -f migration.sql 2>&1 | tee migration.log`
- Review PostgreSQL error messages
- Verify foreign key constraints (projects table must exist)
- Check database user permissions

## Change Log
- 2025-11-18: Initial creation
- Adds comprehensive authentication infrastructure
- Implements RBAC with 3 roles (ADMIN, ENGINEER, VIEWER)
- Project-level permissions with expiration support
- Full audit trail with JSON field support
- Session management with cleanup utilities
