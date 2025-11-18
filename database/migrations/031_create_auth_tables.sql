-- ==========================================
-- Migration 031: Authentication & Authorization System
-- ==========================================
-- Description: Creates tables for user authentication, role-based access control,
--              project-level permissions, audit logging, and session management.
-- Dependencies: Requires projects table from core schema
-- Author: ACAD-GIS Security Foundation
-- Date: 2025-11-18
-- ==========================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==========================================
-- USERS TABLE
-- ==========================================
-- Stores user accounts with Replit Auth integration
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    replit_user_id VARCHAR(255) UNIQUE NOT NULL,  -- From Replit Auth OAuth
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    full_name VARCHAR(200),
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',  -- ADMIN, ENGINEER, VIEWER
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('ADMIN', 'ENGINEER', 'VIEWER'))
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_replit_id ON users(replit_user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Comments
COMMENT ON TABLE users IS 'User accounts with Replit Auth integration for authentication';
COMMENT ON COLUMN users.replit_user_id IS 'Unique identifier from Replit OAuth';
COMMENT ON COLUMN users.role IS 'System-wide role: ADMIN (full access), ENGINEER (read/write), VIEWER (read-only)';
COMMENT ON COLUMN users.is_active IS 'Whether user account is active (false = deactivated)';

-- ==========================================
-- PROJECT PERMISSIONS TABLE
-- ==========================================
-- Stores fine-grained project-level access control
CREATE TABLE IF NOT EXISTS project_permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    access_level VARCHAR(20) NOT NULL,  -- READ, WRITE, ADMIN
    granted_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Optional expiration date
    notes TEXT,  -- Optional notes about why access was granted

    -- Constraints
    UNIQUE(user_id, project_id),
    CONSTRAINT valid_access_level CHECK (access_level IN ('READ', 'WRITE', 'ADMIN'))
);

-- Indexes for project_permissions
CREATE INDEX IF NOT EXISTS idx_project_perms_user ON project_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_project_perms_project ON project_permissions(project_id);
CREATE INDEX IF NOT EXISTS idx_project_perms_granted_by ON project_permissions(granted_by);
CREATE INDEX IF NOT EXISTS idx_project_perms_expires_at ON project_permissions(expires_at) WHERE expires_at IS NOT NULL;

-- Comments
COMMENT ON TABLE project_permissions IS 'Project-level access control for fine-grained permissions';
COMMENT ON COLUMN project_permissions.access_level IS 'READ (view only), WRITE (edit data), ADMIN (manage permissions)';
COMMENT ON COLUMN project_permissions.expires_at IS 'Optional expiration for temporary access (NULL = permanent)';
COMMENT ON COLUMN project_permissions.granted_by IS 'User who granted this permission (for audit trail)';

-- ==========================================
-- AUDIT LOG TABLE
-- ==========================================
-- Comprehensive audit trail for all user actions
CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    username VARCHAR(100),  -- Denormalized for historical record even if user deleted
    action VARCHAR(50) NOT NULL,  -- LOGIN, LOGOUT, CREATE, UPDATE, DELETE, GRANT_PERMISSION, etc.
    table_name VARCHAR(100),  -- Table affected by action (if applicable)
    record_id UUID,  -- ID of record affected (if applicable)
    project_id UUID REFERENCES projects(project_id) ON DELETE SET NULL,  -- Associated project (if applicable)
    old_values JSONB,  -- Previous values for UPDATE/DELETE operations
    new_values JSONB,  -- New values for CREATE/UPDATE operations
    ip_address INET,  -- IP address of user
    user_agent TEXT,  -- Browser/client user agent
    success BOOLEAN DEFAULT true,  -- Whether action succeeded
    error_message TEXT,  -- Error message if action failed
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_action CHECK (action IN (
        'LOGIN', 'LOGOUT', 'LOGIN_FAILED',
        'CREATE', 'UPDATE', 'DELETE',
        'GRANT_PERMISSION', 'REVOKE_PERMISSION',
        'CHANGE_ROLE', 'ACTIVATE_USER', 'DEACTIVATE_USER',
        'EXPORT', 'IMPORT',
        'ACCESS_DENIED'
    ))
);

-- Indexes for audit_log (optimized for common queries)
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_username ON audit_log(username);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_project ON audit_log(project_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_failed_actions ON audit_log(timestamp DESC) WHERE success = false;

-- Comments
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail of all user actions for compliance and security';
COMMENT ON COLUMN audit_log.username IS 'Denormalized username for historical record (preserved even if user deleted)';
COMMENT ON COLUMN audit_log.action IS 'Type of action performed (LOGIN, CREATE, UPDATE, DELETE, etc.)';
COMMENT ON COLUMN audit_log.old_values IS 'JSON snapshot of record before modification (for UPDATE/DELETE)';
COMMENT ON COLUMN audit_log.new_values IS 'JSON snapshot of record after modification (for CREATE/UPDATE)';
COMMENT ON COLUMN audit_log.success IS 'Whether the action succeeded (false for failed login attempts, permission denials)';

-- ==========================================
-- USER SESSIONS TABLE
-- ==========================================
-- Manages active user sessions for security and monitoring
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,  -- Flask session ID or custom token
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,

    -- Constraints
    CONSTRAINT valid_expiration CHECK (expires_at > created_at)
);

-- Indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON user_sessions(last_activity DESC);

-- Comments
COMMENT ON TABLE user_sessions IS 'Active user sessions for security monitoring and session management';
COMMENT ON COLUMN user_sessions.session_token IS 'Unique session token (Flask session ID or JWT)';
COMMENT ON COLUMN user_sessions.expires_at IS 'Session expiration timestamp (configurable, default 8 hours)';
COMMENT ON COLUMN user_sessions.last_activity IS 'Last activity timestamp for idle session detection';
COMMENT ON COLUMN user_sessions.is_active IS 'Whether session is active (false = logged out or invalidated)';

-- ==========================================
-- INITIAL DATA: DEFAULT ADMIN USER
-- ==========================================
-- Create a default admin user for initial setup
-- NOTE: In production, this should be configured via environment variables
-- The first user to log in via Replit Auth with a specific email will be granted admin
INSERT INTO users (
    replit_user_id,
    username,
    email,
    full_name,
    role,
    is_active
) VALUES (
    'initial-admin',
    'admin',
    'admin@acad-gis.local',
    'System Administrator',
    'ADMIN',
    true
) ON CONFLICT (replit_user_id) DO NOTHING;

-- ==========================================
-- HELPER FUNCTIONS
-- ==========================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at for users table
DROP TRIGGER IF EXISTS users_updated_at_trigger ON users;
CREATE TRIGGER users_updated_at_trigger
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to clean up expired sessions (call periodically from app or cron)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP
       OR (last_activity < CURRENT_TIMESTAMP - INTERVAL '24 hours' AND is_active = false);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_sessions() IS 'Removes expired and old inactive sessions (call periodically)';

-- Function to check if user has project access
CREATE OR REPLACE FUNCTION user_has_project_access(
    p_user_id UUID,
    p_project_id UUID,
    p_required_level VARCHAR(20) DEFAULT 'READ'
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role VARCHAR(20);
    user_access_level VARCHAR(20);
    level_hierarchy INTEGER[];
    user_level_idx INTEGER;
    required_level_idx INTEGER;
BEGIN
    -- Get user's system role
    SELECT role INTO user_role
    FROM users
    WHERE user_id = p_user_id AND is_active = true;

    -- Admins have access to everything
    IF user_role = 'ADMIN' THEN
        RETURN true;
    END IF;

    -- Check project-specific permissions
    SELECT access_level INTO user_access_level
    FROM project_permissions
    WHERE user_id = p_user_id
      AND project_id = p_project_id
      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);

    -- No project permission found
    IF user_access_level IS NULL THEN
        RETURN false;
    END IF;

    -- Check access level hierarchy: READ < WRITE < ADMIN
    level_hierarchy := ARRAY[1, 2, 3];  -- READ=1, WRITE=2, ADMIN=3

    user_level_idx := CASE user_access_level
        WHEN 'READ' THEN 1
        WHEN 'WRITE' THEN 2
        WHEN 'ADMIN' THEN 3
        ELSE 0
    END;

    required_level_idx := CASE p_required_level
        WHEN 'READ' THEN 1
        WHEN 'WRITE' THEN 2
        WHEN 'ADMIN' THEN 3
        ELSE 0
    END;

    RETURN user_level_idx >= required_level_idx;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION user_has_project_access(UUID, UUID, VARCHAR) IS 'Checks if user has required access level to project';

-- ==========================================
-- VIEWS
-- ==========================================

-- View for active sessions with user info
CREATE OR REPLACE VIEW active_user_sessions AS
SELECT
    s.session_id,
    s.session_token,
    s.created_at,
    s.expires_at,
    s.last_activity,
    s.ip_address,
    u.user_id,
    u.username,
    u.email,
    u.role,
    EXTRACT(EPOCH FROM (s.expires_at - CURRENT_TIMESTAMP)) / 3600 AS hours_until_expiration,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.last_activity)) / 60 AS minutes_since_activity
FROM user_sessions s
JOIN users u ON s.user_id = u.user_id
WHERE s.is_active = true
  AND s.expires_at > CURRENT_TIMESTAMP
ORDER BY s.last_activity DESC;

COMMENT ON VIEW active_user_sessions IS 'Active user sessions with calculated expiration and activity metrics';

-- View for user activity summary
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT
    u.user_id,
    u.username,
    u.email,
    u.role,
    u.last_login,
    COUNT(DISTINCT s.session_id) FILTER (WHERE s.is_active AND s.expires_at > CURRENT_TIMESTAMP) AS active_sessions,
    COUNT(DISTINCT al.log_id) FILTER (WHERE al.timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours') AS actions_last_24h,
    COUNT(DISTINCT al.log_id) FILTER (WHERE al.timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days') AS actions_last_7d,
    MAX(al.timestamp) AS last_action,
    COUNT(DISTINCT pp.project_id) AS projects_with_access
FROM users u
LEFT JOIN user_sessions s ON u.user_id = s.user_id
LEFT JOIN audit_log al ON u.user_id = al.user_id
LEFT JOIN project_permissions pp ON u.user_id = pp.user_id
WHERE u.is_active = true
GROUP BY u.user_id, u.username, u.email, u.role, u.last_login
ORDER BY u.last_login DESC NULLS LAST;

COMMENT ON VIEW user_activity_summary IS 'User activity summary with session and action counts';

-- View for recent audit events
CREATE OR REPLACE VIEW recent_audit_events AS
SELECT
    al.log_id,
    al.timestamp,
    al.action,
    al.username,
    u.email,
    u.role,
    al.table_name,
    al.project_id,
    p.project_name,
    al.success,
    al.error_message,
    al.ip_address
FROM audit_log al
LEFT JOIN users u ON al.user_id = u.user_id
LEFT JOIN projects p ON al.project_id = p.project_id
WHERE al.timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY al.timestamp DESC
LIMIT 1000;

COMMENT ON VIEW recent_audit_events IS 'Recent audit events (last 7 days) with user and project context';

-- ==========================================
-- GRANTS (if using role-based DB access)
-- ==========================================
-- Uncomment and modify if using PostgreSQL roles for application access

-- GRANT SELECT, INSERT, UPDATE ON users TO acad_gis_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON project_permissions TO acad_gis_app;
-- GRANT SELECT, INSERT ON audit_log TO acad_gis_app;  -- No UPDATE/DELETE on audit log
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_sessions TO acad_gis_app;

-- ==========================================
-- MIGRATION COMPLETE
-- ==========================================
-- Run post-migration verification:
-- SELECT COUNT(*) FROM users;  -- Should have 1 initial admin
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users', 'project_permissions', 'audit_log', 'user_sessions');
-- SELECT * FROM pg_indexes WHERE tablename IN ('users', 'project_permissions', 'audit_log', 'user_sessions');
