"""add_project_archiving

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-18 20:30:00.000000

This migration implements Phase 10: Two-Stage Project Archiving & Deletion System

SCOPE:
- Adds archiving columns to the projects table: is_archived, archived_at, archived_by
- Creates index on is_archived for performance
- Implements a two-stage deletion workflow:
  Stage 1: Soft delete (archive) - marks project as archived
  Stage 2: Hard delete - permanent deletion after archive period

IMPORTANT SAFETY NOTES:
- This migration is SAFE to run on production databases
- Adds nullable columns with defaults (no data migration needed)
- Uses PostgreSQL's transactional DDL (atomic migration)
- Can be rolled back safely if needed
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add archiving columns to projects table.

    This implements the Phase 10 two-stage deletion system:
    - is_archived: Boolean flag (soft delete indicator)
    - archived_at: Timestamp of archiving action
    - archived_by: User ID who performed the archiving

    All columns are nullable/have defaults, so this is safe to run
    on existing data.
    """

    # ========================================================================
    # ADD ARCHIVING COLUMNS TO PROJECTS TABLE
    # ========================================================================

    print("Adding archiving columns to projects table...")

    # Add is_archived column (Stage 1 soft delete flag)
    op.add_column(
        'projects',
        sa.Column(
            'is_archived',
            sa.Boolean(),
            nullable=False,
            server_default=text('false'),
            comment='Soft delete flag - project is archived but not permanently deleted'
        )
    )

    # Add archived_at timestamp column
    op.add_column(
        'projects',
        sa.Column(
            'archived_at',
            sa.DateTime(),
            nullable=True,
            comment='Timestamp when project was archived'
        )
    )

    # Add archived_by user tracking column
    op.add_column(
        'projects',
        sa.Column(
            'archived_by',
            sa.UUID(),
            nullable=True,
            comment='User ID who archived the project'
        )
    )

    print("✓ Archiving columns added successfully")

    # ========================================================================
    # CREATE INDEX FOR QUERY PERFORMANCE
    # ========================================================================

    print("Creating index on is_archived column...")

    # Create index for efficient filtering of archived/active projects
    # This dramatically improves query performance when filtering:
    # SELECT * FROM projects WHERE is_archived = false
    op.create_index(
        'idx_projects_archived',
        'projects',
        ['is_archived'],
        unique=False
    )

    print("✓ Index created successfully")

    # ========================================================================
    # ADD HELPFUL COMMENTS FOR DOCUMENTATION
    # ========================================================================

    # Note: Column comments were already added in the Column definitions above
    # PostgreSQL will store these in the system catalog for documentation

    print("✓ Phase 10 migration completed successfully!")
    print("")
    print("NEXT STEPS:")
    print("1. Update application queries to filter: WHERE is_archived = false")
    print("2. Implement archive/restore endpoints in the API")
    print("3. Create scheduled job for permanent deletion of old archived projects")
    print("4. Test the two-stage deletion workflow")


def downgrade() -> None:
    """
    Remove archiving columns from projects table.

    This safely rolls back the Phase 10 changes.

    WARNING: This will delete all archiving metadata!
    Any projects marked as archived will become active again,
    and all archive timestamps/user tracking will be lost.
    """

    print("Rolling back Phase 10 archiving migration...")

    # Drop the index first
    op.drop_index('idx_projects_archived', table_name='projects')
    print("✓ Index dropped")

    # Drop the archiving columns
    op.drop_column('projects', 'archived_by')
    print("✓ archived_by column dropped")

    op.drop_column('projects', 'archived_at')
    print("✓ archived_at column dropped")

    op.drop_column('projects', 'is_archived')
    print("✓ is_archived column dropped")

    print("✓ Phase 10 migration rolled back successfully")
    print("")
    print("WARNING: All archiving metadata has been deleted!")
