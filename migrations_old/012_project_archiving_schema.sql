-- Migration 012: Project Archiving Schema
-- Adds two-stage deletion support to the projects table
--
-- This migration implements contractual data retention by adding:
-- 1. is_archived: Soft delete flag
-- 2. archived_at: Timestamp of archiving
-- 3. archived_by: User who performed the archive
--
-- Purpose: Compliance with contractual data retention obligations
-- Phase: 10 - Contractual Project Archiving & Deletion

-- ============================================================================
-- ADD ARCHIVING COLUMNS TO PROJECTS TABLE
-- ============================================================================

-- Add is_archived column (defaults to FALSE for existing projects)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Add archived_at column (NULL until project is archived)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP;

-- Add archived_by column (NULL until project is archived)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS archived_by UUID;

-- Add comment to is_archived column
COMMENT ON COLUMN projects.is_archived IS
'Soft delete flag - project is archived but not permanently deleted';

-- Add comment to archived_at column
COMMENT ON COLUMN projects.archived_at IS
'Timestamp when project was archived';

-- Add comment to archived_by column
COMMENT ON COLUMN projects.archived_by IS
'User ID who archived the project';

-- ============================================================================
-- CREATE INDEX FOR ARCHIVING QUERIES
-- ============================================================================

-- Index to efficiently filter out archived projects
CREATE INDEX IF NOT EXISTS idx_projects_archived
ON projects(is_archived);

-- Composite index for finding projects eligible for hard delete
CREATE INDEX IF NOT EXISTS idx_projects_archived_timestamp
ON projects(is_archived, archived_at)
WHERE is_archived = TRUE;

-- ============================================================================
-- ADD NEW AUDIT LOG ACTION TYPES
-- ============================================================================

-- The audit_log table already exists, but we need to ensure it can handle
-- the new action types: 'ARCHIVE', 'UNARCHIVE', and 'HARD_DELETE'
-- No schema changes needed - just documenting the new action types

COMMENT ON COLUMN audit_log.action IS
'Action performed (INSERT, UPDATE, DELETE, ARCHIVE, UNARCHIVE, HARD_DELETE)';

-- ============================================================================
-- MIGRATION VERIFICATION QUERY
-- ============================================================================

-- Run this query to verify the migration was successful:
/*
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'projects'
  AND column_name IN ('is_archived', 'archived_at', 'archived_by')
ORDER BY column_name;
*/

-- Expected output:
--  column_name  |     data_type      | is_nullable | column_default
-- --------------+--------------------+-------------+----------------
--  archived_at  | timestamp          | YES         |
--  archived_by  | uuid               | YES         |
--  is_archived  | boolean            | NO          | false

-- ============================================================================
-- ROLLBACK SCRIPT (IF NEEDED)
-- ============================================================================

/*
-- WARNING: This will remove all archiving data
-- Only run if you need to completely undo this migration

DROP INDEX IF EXISTS idx_projects_archived_timestamp;
DROP INDEX IF EXISTS idx_projects_archived;

ALTER TABLE projects DROP COLUMN IF EXISTS archived_by;
ALTER TABLE projects DROP COLUMN IF EXISTS archived_at;
ALTER TABLE projects DROP COLUMN IF EXISTS is_archived;
*/
