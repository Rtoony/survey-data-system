"""
Authentication Service for ACAD-GIS
Handles Replit Auth integration, session management, and audit logging
"""

import os
import json
import requests
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any, List
from flask import session, request, jsonify
from database import execute_query


class AuthService:
    """Core authentication service for ACAD-GIS"""

    def __init__(self):
        """Initialize authentication service with Replit Auth configuration"""
        self.replit_auth_url = 'https://replit.com/api/v0/oauth'
        self.replit_api_url = 'https://replit.com/api/v0'
        self.client_id = os.getenv('REPLIT_CLIENT_ID')
        self.client_secret = os.getenv('REPLIT_CLIENT_SECRET')
        self.session_timeout_hours = int(os.getenv('SESSION_TIMEOUT_HOURS', '8'))
        self.initial_admin_email = os.getenv('INITIAL_ADMIN_EMAIL', '')

    # ==========================================
    # SESSION MANAGEMENT
    # ==========================================

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get currently authenticated user from session

        Returns:
            User dict if authenticated, None otherwise
        """
        if 'user_id' not in session:
            return None

        try:
            result = execute_query("""
                SELECT
                    user_id,
                    replit_user_id,
                    username,
                    email,
                    full_name,
                    role,
                    is_active,
                    last_login,
                    created_at
                FROM users
                WHERE user_id = %s AND is_active = true
            """, (session['user_id'],))

            return dict(result[0]) if result else None
        except Exception as e:
            print(f"Error getting current user: {e}")
            return None

    def create_session(self, user_id: str, session_token: str) -> Dict[str, Any]:
        """
        Create new user session in database

        Args:
            user_id: User UUID
            session_token: Flask session token

        Returns:
            Created session dict
        """
        expires_at = datetime.now() + timedelta(hours=self.session_timeout_hours)

        result = execute_query("""
            INSERT INTO user_sessions (
                user_id,
                session_token,
                ip_address,
                user_agent,
                expires_at
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING session_id, created_at, expires_at
        """, (
            user_id,
            session_token,
            request.remote_addr,
            request.headers.get('User-Agent'),
            expires_at
        ))

        return dict(result[0]) if result else {}

    def update_session_activity(self, session_token: str) -> None:
        """
        Update last activity timestamp for session

        Args:
            session_token: Flask session token
        """
        try:
            execute_query("""
                UPDATE user_sessions
                SET last_activity = CURRENT_TIMESTAMP
                WHERE session_token = %s AND is_active = true
            """, (session_token,))
        except Exception as e:
            print(f"Error updating session activity: {e}")

    def invalidate_session(self, session_token: str) -> None:
        """
        Invalidate user session (logout)

        Args:
            session_token: Flask session token
        """
        try:
            execute_query("""
                UPDATE user_sessions
                SET is_active = false
                WHERE session_token = %s
            """, (session_token,))
        except Exception as e:
            print(f"Error invalidating session: {e}")

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from database

        Returns:
            Number of sessions deleted
        """
        try:
            result = execute_query("SELECT cleanup_expired_sessions()")
            return result[0]['cleanup_expired_sessions'] if result else 0
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0

    # ==========================================
    # REPLIT AUTH INTEGRATION
    # ==========================================

    def get_auth_url(self, redirect_uri: str) -> str:
        """
        Generate Replit OAuth authorization URL

        Args:
            redirect_uri: Callback URL after authentication

        Returns:
            Authorization URL to redirect user to
        """
        return (f"{self.replit_auth_url}/authorize"
                f"?client_id={self.client_id}"
                f"&redirect_uri={redirect_uri}"
                f"&response_type=code"
                f"&scope=user:read")

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[str]:
        """
        Exchange OAuth authorization code for access token

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Access token if successful, None otherwise
        """
        try:
            response = requests.post(
                f"{self.replit_auth_url}/token",
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri
                },
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                print(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None

    def get_replit_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Replit API

        Args:
            access_token: OAuth access token

        Returns:
            User info dict if successful, None otherwise
        """
        try:
            response = requests.get(
                f"{self.replit_api_url}/user",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Get user info failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error getting Replit user info: {e}")
            return None

    def create_or_update_user(self, replit_user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create new user or update existing user from Replit data

        Args:
            replit_user: User data from Replit API

        Returns:
            User dict from database
        """
        try:
            # Determine role for new users
            email = replit_user.get('email', '')
            is_initial_admin = (email and
                              self.initial_admin_email and
                              email.lower() == self.initial_admin_email.lower())

            # Check if this is the first user (becomes admin)
            user_count = execute_query("SELECT COUNT(*) as count FROM users WHERE replit_user_id != 'initial-admin'")
            is_first_user = user_count and user_count[0]['count'] == 0

            default_role = 'ADMIN' if (is_initial_admin or is_first_user) else 'VIEWER'

            # Create or update user
            result = execute_query("""
                INSERT INTO users (
                    replit_user_id,
                    username,
                    email,
                    full_name,
                    role,
                    last_login
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (replit_user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    full_name = EXCLUDED.full_name,
                    last_login = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING
                    user_id,
                    replit_user_id,
                    username,
                    email,
                    full_name,
                    role,
                    is_active
            """, (
                str(replit_user['id']),
                replit_user.get('username', ''),
                replit_user.get('email', ''),
                replit_user.get('name', replit_user.get('full_name', '')),
                default_role
            ))

            return dict(result[0]) if result else None
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return None

    # ==========================================
    # AUDIT LOGGING
    # ==========================================

    def create_audit_log(
        self,
        action: str,
        table_name: Optional[str] = None,
        record_id: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        project_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """
        Create audit log entry for user action

        Args:
            action: Type of action (LOGIN, CREATE, UPDATE, DELETE, etc.)
            table_name: Name of table affected
            record_id: ID of record affected
            old_values: Previous values (for UPDATE/DELETE)
            new_values: New values (for CREATE/UPDATE)
            project_id: Associated project ID
            success: Whether action succeeded
            error_message: Error message if action failed
        """
        user = self.get_current_user()
        username = user['username'] if user else 'anonymous'
        user_id = user['user_id'] if user else None

        try:
            execute_query("""
                INSERT INTO audit_log (
                    user_id,
                    username,
                    action,
                    table_name,
                    record_id,
                    project_id,
                    old_values,
                    new_values,
                    ip_address,
                    user_agent,
                    success,
                    error_message
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                username,
                action,
                table_name,
                record_id,
                project_id,
                json.dumps(old_values) if old_values else None,
                json.dumps(new_values) if new_values else None,
                request.remote_addr if request else None,
                request.headers.get('User-Agent') if request else None,
                success,
                error_message
            ))
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            print(f"Error creating audit log: {e}")

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        table_name: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit logs with filters

        Args:
            user_id: Filter by user
            action: Filter by action type
            table_name: Filter by table
            project_id: Filter by project
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results

        Returns:
            List of audit log entries
        """
        conditions = []
        params = []

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if action:
            conditions.append("action = %s")
            params.append(action)

        if table_name:
            conditions.append("table_name = %s")
            params.append(table_name)

        if project_id:
            conditions.append("project_id = %s")
            params.append(project_id)

        if start_date:
            conditions.append("timestamp >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("timestamp <= %s")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        try:
            result = execute_query(f"""
                SELECT
                    log_id,
                    username,
                    action,
                    table_name,
                    record_id,
                    project_id,
                    old_values,
                    new_values,
                    ip_address,
                    success,
                    error_message,
                    timestamp
                FROM audit_log
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s
            """, params + [limit])

            return [dict(row) for row in result] if result else []
        except Exception as e:
            print(f"Error querying audit logs: {e}")
            return []


# Global auth service instance
auth_service = AuthService()
