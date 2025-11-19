"""
Project Management Service
Handles project lifecycle operations including archiving and deletion

This service uses SQLAlchemy Core for type-safe, parameterized queries
and integrates with the audit_log for comprehensive tracking.
"""
from typing import Optional, Dict, Any
from datetime import datetime
import json
from uuid import UUID

from sqlalchemy import select, update, insert
from sqlalchemy.exc import SQLAlchemyError

from app.db_session import get_db_connection
from app.data_models import projects, audit_log


class ProjectManagementService:
    """Service for managing project lifecycle operations"""

    @staticmethod
    def archive_project(
        project_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Archive a project (soft delete) with full audit trail.

        This is the first stage of the two-stage deletion process. The project
        is marked as archived but NOT permanently deleted, allowing for data
        retention compliance and potential restoration.

        Args:
            project_id: UUID of the project to archive
            user_id: UUID of the user performing the archive (optional)
            username: Username of the user performing the archive (optional)
            ip_address: IP address of the request (optional)
            user_agent: User agent string of the request (optional)

        Returns:
            Dict containing:
                - success: bool
                - project_id: str
                - archived_at: str (ISO format timestamp)
                - message: str

        Raises:
            ValueError: If project_id is invalid or project not found
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid project_id format: {project_id}")

            with get_db_connection() as conn:
                # First, fetch the current project state for audit trail
                select_stmt = select(projects).where(
                    projects.c.project_id == project_uuid
                )
                result = conn.execute(select_stmt)
                project_row = result.fetchone()

                if not project_row:
                    raise ValueError(f"Project not found: {project_id}")

                # Check if already archived
                if project_row.is_archived:
                    return {
                        'success': False,
                        'project_id': str(project_id),
                        'message': 'Project is already archived',
                        'archived_at': project_row.archived_at.isoformat() if project_row.archived_at else None
                    }

                # Capture old values for audit
                old_values = {
                    'is_archived': project_row.is_archived,
                    'archived_at': None,
                    'archived_by': None
                }

                # Current timestamp
                archived_timestamp = datetime.utcnow()

                # Update project to archived state
                update_stmt = update(projects).where(
                    projects.c.project_id == project_uuid
                ).values(
                    is_archived=True,
                    archived_at=archived_timestamp,
                    archived_by=UUID(user_id) if user_id else None,
                    updated_at=archived_timestamp
                )
                conn.execute(update_stmt)

                # New values for audit
                new_values = {
                    'is_archived': True,
                    'archived_at': archived_timestamp.isoformat(),
                    'archived_by': str(user_id) if user_id else None
                }

                # Create audit log entry
                audit_insert_stmt = insert(audit_log).values(
                    table_name='projects',
                    record_id=project_uuid,
                    action='ARCHIVE',
                    user_id=UUID(user_id) if user_id else None,
                    username=username,
                    action_timestamp=archived_timestamp,
                    old_values=json.dumps(old_values),
                    new_values=json.dumps(new_values),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                conn.execute(audit_insert_stmt)

                # Commit the transaction
                conn.commit()

                return {
                    'success': True,
                    'project_id': str(project_id),
                    'archived_at': archived_timestamp.isoformat(),
                    'message': f'Project successfully archived. Data will be retained per contractual obligations.'
                }

        except ValueError as ve:
            raise ve
        except SQLAlchemyError as se:
            raise SQLAlchemyError(f"Database error during project archiving: {str(se)}")
        except Exception as e:
            raise Exception(f"Unexpected error during project archiving: {str(e)}")


    @staticmethod
    def unarchive_project(
        project_id: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restore an archived project (undo soft delete).

        This allows restoration of projects that were archived by mistake
        or need to be reactivated before the retention period expires.

        Args:
            project_id: UUID of the project to restore
            user_id: UUID of the user performing the restore (optional)
            username: Username of the user performing the restore (optional)
            ip_address: IP address of the request (optional)
            user_agent: User agent string of the request (optional)

        Returns:
            Dict containing:
                - success: bool
                - project_id: str
                - restored_at: str (ISO format timestamp)
                - message: str

        Raises:
            ValueError: If project_id is invalid or project not found
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate UUID format
            try:
                project_uuid = UUID(project_id)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid project_id format: {project_id}")

            with get_db_connection() as conn:
                # Fetch the current project state
                select_stmt = select(projects).where(
                    projects.c.project_id == project_uuid
                )
                result = conn.execute(select_stmt)
                project_row = result.fetchone()

                if not project_row:
                    raise ValueError(f"Project not found: {project_id}")

                # Check if not archived
                if not project_row.is_archived:
                    return {
                        'success': False,
                        'project_id': str(project_id),
                        'message': 'Project is not archived - nothing to restore'
                    }

                # Capture old values for audit
                old_values = {
                    'is_archived': project_row.is_archived,
                    'archived_at': project_row.archived_at.isoformat() if project_row.archived_at else None,
                    'archived_by': str(project_row.archived_by) if project_row.archived_by else None
                }

                # Current timestamp
                restored_timestamp = datetime.utcnow()

                # Update project to active state
                update_stmt = update(projects).where(
                    projects.c.project_id == project_uuid
                ).values(
                    is_archived=False,
                    archived_at=None,
                    archived_by=None,
                    updated_at=restored_timestamp
                )
                conn.execute(update_stmt)

                # New values for audit
                new_values = {
                    'is_archived': False,
                    'archived_at': None,
                    'archived_by': None
                }

                # Create audit log entry
                audit_insert_stmt = insert(audit_log).values(
                    table_name='projects',
                    record_id=project_uuid,
                    action='UNARCHIVE',
                    user_id=UUID(user_id) if user_id else None,
                    username=username,
                    action_timestamp=restored_timestamp,
                    old_values=json.dumps(old_values),
                    new_values=json.dumps(new_values),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                conn.execute(audit_insert_stmt)

                # Commit the transaction
                conn.commit()

                return {
                    'success': True,
                    'project_id': str(project_id),
                    'restored_at': restored_timestamp.isoformat(),
                    'message': 'Project successfully restored from archive'
                }

        except ValueError as ve:
            raise ve
        except SQLAlchemyError as se:
            raise SQLAlchemyError(f"Database error during project restoration: {str(se)}")
        except Exception as e:
            raise Exception(f"Unexpected error during project restoration: {str(e)}")


    @staticmethod
    def get_project_archive_status(project_id: str) -> Dict[str, Any]:
        """
        Check the archive status of a project.

        Args:
            project_id: UUID of the project to check

        Returns:
            Dict containing:
                - project_id: str
                - is_archived: bool
                - archived_at: str (ISO format) or None
                - archived_by: str or None
                - days_archived: int or None

        Raises:
            ValueError: If project_id is invalid or project not found
        """
        try:
            project_uuid = UUID(project_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid project_id format: {project_id}")

        with get_db_connection() as conn:
            select_stmt = select(
                projects.c.project_id,
                projects.c.is_archived,
                projects.c.archived_at,
                projects.c.archived_by
            ).where(
                projects.c.project_id == project_uuid
            )
            result = conn.execute(select_stmt)
            project_row = result.fetchone()

            if not project_row:
                raise ValueError(f"Project not found: {project_id}")

            # Calculate days archived
            days_archived = None
            if project_row.is_archived and project_row.archived_at:
                delta = datetime.utcnow() - project_row.archived_at
                days_archived = delta.days

            return {
                'project_id': str(project_row.project_id),
                'is_archived': project_row.is_archived,
                'archived_at': project_row.archived_at.isoformat() if project_row.archived_at else None,
                'archived_by': str(project_row.archived_by) if project_row.archived_by else None,
                'days_archived': days_archived
            }
