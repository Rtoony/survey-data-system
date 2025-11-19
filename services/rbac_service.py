"""
Role-Based Access Control (RBAC) Service for ACAD-GIS
Handles permission checking, role management, and project-level access control
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import text
from app.db_session import get_db_connection


class UserRole(str, Enum):
    """System-wide user roles"""
    ADMIN = 'ADMIN'
    ENGINEER = 'ENGINEER'
    VIEWER = 'VIEWER'


class AccessLevel(str, Enum):
    """Project-level access levels"""
    READ = 'READ'
    WRITE = 'WRITE'
    ADMIN = 'ADMIN'


class RBACService:
    """Role-Based Access Control service"""

    # Define role permissions matrix
    ROLE_PERMISSIONS = {
        'ADMIN': {
            'projects': ['CREATE', 'READ', 'UPDATE', 'DELETE', 'MANAGE_PERMISSIONS'],
            'users': ['CREATE', 'READ', 'UPDATE', 'DELETE', 'CHANGE_ROLE'],
            'standards': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
            'reference_data': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
            'audit_log': ['READ'],
            'dxf': ['IMPORT', 'EXPORT'],
            'gis': ['READ', 'WRITE', 'EXPORT'],
            'relationships': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
            'ai_tools': ['READ', 'WRITE'],
        },
        'ENGINEER': {
            'projects': ['CREATE', 'READ', 'UPDATE'],  # Can't delete projects
            'users': ['READ'],  # Can see other users
            'standards': ['READ', 'UPDATE'],  # Can modify standards
            'reference_data': ['READ'],  # Read-only reference data
            'audit_log': [],  # No audit log access
            'dxf': ['IMPORT', 'EXPORT'],
            'gis': ['READ', 'WRITE', 'EXPORT'],
            'relationships': ['CREATE', 'READ', 'UPDATE', 'DELETE'],
            'ai_tools': ['READ', 'WRITE'],
        },
        'VIEWER': {
            'projects': ['READ'],  # Read-only
            'users': [],  # Can't see other users
            'standards': ['READ'],
            'reference_data': ['READ'],
            'audit_log': [],
            'dxf': ['EXPORT'],  # Can export but not import
            'gis': ['READ', 'EXPORT'],  # Read-only GIS
            'relationships': ['READ'],
            'ai_tools': ['READ'],  # Can use AI tools but not train
        }
    }

    # ==========================================
    # PERMISSION CHECKING
    # ==========================================

    def has_permission(self, user: Dict[str, Any], resource: str, action: str) -> bool:
        """
        Check if user has permission to perform action on resource

        Args:
            user: User dict with 'role' field
            resource: Resource type (projects, users, standards, etc.)
            action: Action to perform (CREATE, READ, UPDATE, DELETE, etc.)

        Returns:
            True if user has permission, False otherwise
        """
        if not user or not user.get('is_active'):
            return False

        role = user.get('role')
        if not role or role not in self.ROLE_PERMISSIONS:
            return False

        resource_permissions = self.ROLE_PERMISSIONS[role].get(resource, [])
        return action in resource_permissions

    def has_any_permission(self, user: Dict[str, Any], resource: str, actions: List[str]) -> bool:
        """
        Check if user has any of the specified permissions

        Args:
            user: User dict
            resource: Resource type
            actions: List of actions to check

        Returns:
            True if user has at least one permission
        """
        return any(self.has_permission(user, resource, action) for action in actions)

    def has_all_permissions(self, user: Dict[str, Any], resource: str, actions: List[str]) -> bool:
        """
        Check if user has all specified permissions

        Args:
            user: User dict
            resource: Resource type
            actions: List of actions to check

        Returns:
            True if user has all permissions
        """
        return all(self.has_permission(user, resource, action) for action in actions)

    # ==========================================
    # PROJECT-LEVEL ACCESS CONTROL
    # ==========================================

    def has_project_access(
        self,
        user_id: str,
        project_id: str,
        required_level: str = 'READ'
    ) -> bool:
        """
        Check if user has access to specific project

        Args:
            user_id: User UUID
            project_id: Project UUID
            required_level: Required access level (READ, WRITE, ADMIN)

        Returns:
            True if user has required access level
        """
        try:
            result = execute_query("""
                SELECT user_has_project_access(%s, %s, %s) as has_access
            """, (user_id, project_id, required_level))

            return result[0]['has_access'] if result else False
        except Exception as e:
            print(f"Error checking project access: {e}")
            return False

    def get_user_projects(
        self,
        user_id: str,
        min_access_level: str = 'READ'
    ) -> List[Dict[str, Any]]:
        """
        Get all projects user has access to

        Args:
            user_id: User UUID
            min_access_level: Minimum access level required

        Returns:
            List of project dicts with access level
        """
        try:
            # Get user role first
            user_result = execute_query("""
                SELECT role FROM users WHERE user_id = %s
            """, (user_id,))

            if not user_result:
                return []

            role = user_result[0]['role']

            # Admins see all projects
            if role == 'ADMIN':
                result = execute_query("""
                    SELECT
                        p.project_id,
                        p.project_name,
                        p.project_number,
                        p.client_name,
                        p.description,
                        'ADMIN' as access_level,
                        NULL as granted_at,
                        NULL as expires_at
                    FROM projects p
                    ORDER BY p.project_name
                """)
            else:
                # Get projects with explicit permissions
                result = execute_query("""
                    SELECT
                        p.project_id,
                        p.project_name,
                        p.project_number,
                        p.client_name,
                        p.description,
                        pp.access_level,
                        pp.granted_at,
                        pp.expires_at
                    FROM projects p
                    JOIN project_permissions pp ON p.project_id = pp.project_id
                    WHERE pp.user_id = %s
                      AND (pp.expires_at IS NULL OR pp.expires_at > CURRENT_TIMESTAMP)
                    ORDER BY p.project_name
                """, (user_id,))

            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f"Error getting user projects: {e}")
            return []

    def grant_project_permission(
        self,
        user_id: str,
        project_id: str,
        access_level: str,
        granted_by: str,
        expires_at: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Grant project access to user

        Args:
            user_id: User UUID
            project_id: Project UUID
            access_level: Access level (READ, WRITE, ADMIN)
            granted_by: User UUID of granter
            expires_at: Optional expiration timestamp
            notes: Optional notes about permission

        Returns:
            Created permission dict
        """
        try:
            result = execute_query("""
                INSERT INTO project_permissions (
                    user_id,
                    project_id,
                    access_level,
                    granted_by,
                    expires_at,
                    notes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, project_id) DO UPDATE SET
                    access_level = EXCLUDED.access_level,
                    granted_by = EXCLUDED.granted_by,
                    expires_at = EXCLUDED.expires_at,
                    notes = EXCLUDED.notes,
                    granted_at = CURRENT_TIMESTAMP
                RETURNING
                    permission_id,
                    user_id,
                    project_id,
                    access_level,
                    granted_at,
                    expires_at
            """, (user_id, project_id, access_level, granted_by, expires_at, notes))

            return dict(result[0]) if result else None
        except Exception as e:
            print(f"Error granting project permission: {e}")
            return None

    def revoke_project_permission(self, user_id: str, project_id: str) -> bool:
        """
        Revoke project access from user

        Args:
            user_id: User UUID
            project_id: Project UUID

        Returns:
            True if permission was revoked
        """
        try:
            execute_query("""
                DELETE FROM project_permissions
                WHERE user_id = %s AND project_id = %s
            """, (user_id, project_id))
            return True
        except Exception as e:
            print(f"Error revoking project permission: {e}")
            return False

    def get_project_permissions(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all users with access to project

        Args:
            project_id: Project UUID

        Returns:
            List of permission dicts with user info
        """
        try:
            result = execute_query("""
                SELECT
                    pp.permission_id,
                    pp.user_id,
                    pp.access_level,
                    pp.granted_at,
                    pp.expires_at,
                    pp.notes,
                    u.username,
                    u.email,
                    u.full_name,
                    u.role,
                    gb.username as granted_by_username
                FROM project_permissions pp
                JOIN users u ON pp.user_id = u.user_id
                LEFT JOIN users gb ON pp.granted_by = gb.user_id
                WHERE pp.project_id = %s
                ORDER BY u.username
            """, (project_id,))

            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f"Error getting project permissions: {e}")
            return []

    # ==========================================
    # USER MANAGEMENT
    # ==========================================

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users in system

        Returns:
            List of user dicts
        """
        try:
            result = execute_query("""
                SELECT
                    user_id,
                    username,
                    email,
                    full_name,
                    role,
                    is_active,
                    last_login,
                    created_at
                FROM users
                WHERE replit_user_id != 'initial-admin'
                ORDER BY username
            """)

            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    def update_user_role(self, user_id: str, new_role: str) -> bool:
        """
        Update user's system role

        Args:
            user_id: User UUID
            new_role: New role (ADMIN, ENGINEER, VIEWER)

        Returns:
            True if role was updated
        """
        if new_role not in ['ADMIN', 'ENGINEER', 'VIEWER']:
            return False

        try:
            execute_query("""
                UPDATE users
                SET role = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (new_role, user_id))
            return True
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False

    def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user account

        Args:
            user_id: User UUID

        Returns:
            True if user was deactivated
        """
        try:
            execute_query("""
                UPDATE users
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))

            # Invalidate all active sessions
            execute_query("""
                UPDATE user_sessions
                SET is_active = false
                WHERE user_id = %s
            """, (user_id,))

            return True
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False

    def activate_user(self, user_id: str) -> bool:
        """
        Activate user account

        Args:
            user_id: User UUID

        Returns:
            True if user was activated
        """
        try:
            execute_query("""
                UPDATE users
                SET is_active = true, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
            """, (user_id,))
            return True
        except Exception as e:
            print(f"Error activating user: {e}")
            return False

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for user

        Args:
            user_id: User UUID

        Returns:
            Dict with user statistics
        """
        stats: Dict[str, Any] = {
            'projects_with_access': 0,
            'active_sessions': 0,
            'actions_last_24h': 0,
            'actions_last_7d': 0,
            'last_action': None
        }
        
        try:
            # Projects with access
            result = execute_query("""
                SELECT COUNT(*) as count FROM project_permissions
                WHERE user_id = %s
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """, (user_id,))
            stats['projects_with_access'] = result[0]['count'] if result else 0

            # Active sessions
            result = execute_query("""
                SELECT COUNT(*) as count FROM user_sessions
                WHERE user_id = %s AND is_active = true AND expires_at > CURRENT_TIMESTAMP
            """, (user_id,))
            stats['active_sessions'] = result[0]['count'] if result else 0

            # Recent actions
            result = execute_query("""
                SELECT
                    COUNT(*) FILTER (WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours') as last_24h,
                    COUNT(*) FILTER (WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days') as last_7d,
                    MAX(timestamp) as last_action
                FROM audit_log
                WHERE user_id = %s
            """, (user_id,))

            if result:
                stats['actions_last_24h'] = result[0]['last_24h'] or 0
                stats['actions_last_7d'] = result[0]['last_7d'] or 0
                stats['last_action'] = result[0]['last_action']

            return stats
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return stats


# Global RBAC service instance
rbac_service = RBACService()
