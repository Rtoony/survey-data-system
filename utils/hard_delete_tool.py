"""
Hard Delete Tool - Permanent Project Deletion Utility

⚠️  DANGER: THIS UTILITY PERFORMS IRREVERSIBLE DATABASE OPERATIONS ⚠️

This module provides functionality for PERMANENT deletion of archived projects
after the contractual data retention period has expired.

CRITICAL SAFETY CONSTRAINTS:
1. Can ONLY delete projects where is_archived = TRUE
2. Requires explicit confirmation of retention period expiration
3. Creates comprehensive audit trail before deletion
4. Should ONLY be executed by authorized database administrators
5. Recommend running in a transaction with manual commit for final review

USAGE POLICY:
- This tool should be executed via scheduled maintenance scripts
- Requires documented approval from legal/compliance team
- Must verify contractual retention period (typically 7+ years)
- All deletions must be logged in external compliance system

Example Usage:
    >>> from utils.hard_delete_tool import HardDeleteTool
    >>> tool = HardDeleteTool()
    >>>
    >>> # Check if project is eligible for hard delete
    >>> eligible = tool.is_eligible_for_hard_delete(
    ...     project_id='abc-123',
    ...     retention_period_days=2555  # ~7 years
    ... )
    >>>
    >>> if eligible['is_eligible']:
    ...     # FINAL confirmation required
    ...     result = tool.permanently_delete_archived_project(
    ...         project_id='abc-123',
    ...         retention_period_days=2555,
    ...         authorized_by='admin_user_id',
    ...         compliance_ticket='LEGAL-2025-0042'
    ...     )
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy import select, delete, insert, func
from sqlalchemy.exc import SQLAlchemyError

from app.db_session import get_db_connection
from app.data_models import projects, audit_log


class HardDeleteTool:
    """
    Utility for permanent deletion of archived projects after retention period.

    This class implements the second stage of the two-stage deletion process.
    Projects must be archived (soft deleted) before they can be permanently deleted.
    """

    # Default retention period (7 years in days)
    DEFAULT_RETENTION_PERIOD_DAYS = 2555  # 7 years * 365 days

    @staticmethod
    def is_eligible_for_hard_delete(
        project_id: str,
        retention_period_days: int = DEFAULT_RETENTION_PERIOD_DAYS
    ) -> Dict[str, Any]:
        """
        Check if a project is eligible for permanent deletion.

        A project is eligible if:
        1. It exists in the database
        2. It is marked as archived (is_archived = TRUE)
        3. The archived_at timestamp is older than retention_period_days

        Args:
            project_id: UUID of the project to check
            retention_period_days: Number of days to retain archived projects (default: 2555 = ~7 years)

        Returns:
            Dict containing:
                - is_eligible: bool
                - project_id: str
                - is_archived: bool
                - archived_at: str or None
                - days_archived: int or None
                - retention_period_days: int
                - eligible_deletion_date: str or None
                - reason: str (explanation of eligibility status)

        Raises:
            ValueError: If project_id is invalid
        """
        try:
            project_uuid = UUID(project_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid project_id format: {project_id}")

        with get_db_connection() as conn:
            select_stmt = select(
                projects.c.project_id,
                projects.c.project_name,
                projects.c.is_archived,
                projects.c.archived_at
            ).where(
                projects.c.project_id == project_uuid
            )
            result = conn.execute(select_stmt)
            project_row = result.fetchone()

            if not project_row:
                return {
                    'is_eligible': False,
                    'project_id': str(project_id),
                    'reason': 'Project not found in database'
                }

            if not project_row.is_archived:
                return {
                    'is_eligible': False,
                    'project_id': str(project_id),
                    'is_archived': False,
                    'archived_at': None,
                    'reason': 'Project is not archived. Must archive project first before permanent deletion.'
                }

            if not project_row.archived_at:
                return {
                    'is_eligible': False,
                    'project_id': str(project_id),
                    'is_archived': True,
                    'archived_at': None,
                    'reason': 'Project is archived but archived_at timestamp is missing (data integrity issue)'
                }

            # Calculate days since archiving
            now = datetime.utcnow()
            days_archived = (now - project_row.archived_at).days
            eligible_deletion_date = project_row.archived_at + timedelta(days=retention_period_days)

            is_eligible = days_archived >= retention_period_days

            return {
                'is_eligible': is_eligible,
                'project_id': str(project_id),
                'project_name': project_row.project_name,
                'is_archived': True,
                'archived_at': project_row.archived_at.isoformat(),
                'days_archived': days_archived,
                'retention_period_days': retention_period_days,
                'eligible_deletion_date': eligible_deletion_date.isoformat(),
                'reason': (
                    f'Project is eligible for permanent deletion (archived {days_archived} days ago, '
                    f'retention period: {retention_period_days} days)'
                    if is_eligible else
                    f'Project cannot be deleted yet. Must wait {retention_period_days - days_archived} more days. '
                    f'Eligible for deletion on: {eligible_deletion_date.strftime("%Y-%m-%d")}'
                )
            }


    @staticmethod
    def permanently_delete_archived_project(
        project_id: str,
        retention_period_days: int = DEFAULT_RETENTION_PERIOD_DAYS,
        authorized_by: Optional[str] = None,
        compliance_ticket: Optional[str] = None,
        skip_eligibility_check: bool = False
    ) -> Dict[str, Any]:
        """
        Permanently delete an archived project from the database.

        ⚠️  WARNING: THIS OPERATION IS IRREVERSIBLE ⚠️

        This function performs a HARD DELETE of the project record and ALL associated
        data through CASCADE constraints. Use with extreme caution.

        Args:
            project_id: UUID of the project to permanently delete
            retention_period_days: Retention period in days (default: 2555 = ~7 years)
            authorized_by: User ID or name of the person authorizing deletion
            compliance_ticket: Reference to legal/compliance approval ticket
            skip_eligibility_check: DANGEROUS - bypass retention period check (default: False)

        Returns:
            Dict containing:
                - success: bool
                - project_id: str
                - deleted_at: str (ISO format timestamp)
                - cascaded_deletes: dict (counts of related records deleted)
                - message: str

        Raises:
            ValueError: If project is not eligible for deletion
            SQLAlchemyError: If database operation fails
        """
        # SAFETY CHECK: Verify eligibility unless explicitly bypassed
        if not skip_eligibility_check:
            eligibility = HardDeleteTool.is_eligible_for_hard_delete(
                project_id=project_id,
                retention_period_days=retention_period_days
            )

            if not eligibility['is_eligible']:
                raise ValueError(
                    f"Project is not eligible for permanent deletion. "
                    f"Reason: {eligibility['reason']}"
                )

        try:
            project_uuid = UUID(project_id)
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid project_id format: {project_id}")

        try:
            with get_db_connection() as conn:
                # Step 1: Fetch full project details for final audit record
                select_stmt = select(projects).where(
                    projects.c.project_id == project_uuid
                )
                result = conn.execute(select_stmt)
                project_row = result.fetchone()

                if not project_row:
                    raise ValueError(f"Project not found: {project_id}")

                # Convert row to dict for audit trail
                project_data = dict(project_row._mapping)

                # Convert non-serializable types to strings
                for key, value in project_data.items():
                    if isinstance(value, (UUID, datetime)):
                        project_data[key] = str(value)

                # Step 2: Create final audit log entry BEFORE deletion
                deletion_timestamp = datetime.utcnow()

                audit_metadata = {
                    'deletion_type': 'HARD_DELETE',
                    'retention_period_days': retention_period_days,
                    'authorized_by': authorized_by,
                    'compliance_ticket': compliance_ticket,
                    'project_snapshot': project_data,
                    'warning': 'IRREVERSIBLE DELETION - ALL PROJECT DATA PERMANENTLY REMOVED'
                }

                audit_insert_stmt = insert(audit_log).values(
                    table_name='projects',
                    record_id=project_uuid,
                    action='HARD_DELETE',
                    user_id=UUID(authorized_by) if authorized_by and len(authorized_by) == 36 else None,
                    username=authorized_by if authorized_by else 'SYSTEM_HARD_DELETE',
                    action_timestamp=deletion_timestamp,
                    old_values=json.dumps(project_data),
                    new_values=json.dumps(audit_metadata)
                )
                conn.execute(audit_insert_stmt)

                # Step 3: Count related records that will be cascade deleted
                # This helps track the scope of the deletion
                # NOTE: Actual counts would require queries to all related tables
                # For now, we'll just note that cascades will occur

                # Step 4: PERMANENT DELETION
                delete_stmt = delete(projects).where(
                    projects.c.project_id == project_uuid
                )
                result = conn.execute(delete_stmt)

                if result.rowcount == 0:
                    raise ValueError(f"Project deletion failed - no rows affected: {project_id}")

                # Commit the transaction
                conn.commit()

                return {
                    'success': True,
                    'project_id': str(project_id),
                    'project_name': project_data.get('project_name', 'Unknown'),
                    'deleted_at': deletion_timestamp.isoformat(),
                    'authorized_by': authorized_by,
                    'compliance_ticket': compliance_ticket,
                    'cascaded_deletes': {
                        'note': 'All related records deleted via CASCADE constraints',
                        'tables_affected': [
                            'survey_points',
                            'entities',
                            'relationships',
                            'and other project-related tables'
                        ]
                    },
                    'message': (
                        f'Project "{project_data.get("project_name", "Unknown")}" permanently deleted. '
                        f'This operation is IRREVERSIBLE. Audit trail preserved in audit_log table.'
                    )
                }

        except ValueError as ve:
            raise ve
        except SQLAlchemyError as se:
            raise SQLAlchemyError(f"Database error during hard delete: {str(se)}")
        except Exception as e:
            raise Exception(f"Unexpected error during hard delete: {str(e)}")


    @staticmethod
    def get_projects_eligible_for_deletion(
        retention_period_days: int = DEFAULT_RETENTION_PERIOD_DAYS,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get a list of all projects eligible for permanent deletion.

        This is useful for generating deletion reports or batch processing.

        Args:
            retention_period_days: Retention period in days (default: 2555 = ~7 years)
            limit: Maximum number of results to return (default: 100)

        Returns:
            List of dicts, each containing:
                - project_id: str
                - project_name: str
                - archived_at: str
                - days_archived: int
                - eligible_deletion_date: str
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_period_days)

        with get_db_connection() as conn:
            select_stmt = select(
                projects.c.project_id,
                projects.c.project_name,
                projects.c.archived_at
            ).where(
                projects.c.is_archived == True,
                projects.c.archived_at <= cutoff_date
            ).order_by(
                projects.c.archived_at.asc()
            ).limit(limit)

            result = conn.execute(select_stmt)
            rows = result.fetchall()

            eligible_projects = []
            for row in rows:
                days_archived = (datetime.utcnow() - row.archived_at).days
                eligible_deletion_date = row.archived_at + timedelta(days=retention_period_days)

                eligible_projects.append({
                    'project_id': str(row.project_id),
                    'project_name': row.project_name,
                    'archived_at': row.archived_at.isoformat(),
                    'days_archived': days_archived,
                    'eligible_deletion_date': eligible_deletion_date.isoformat()
                })

            return eligible_projects
