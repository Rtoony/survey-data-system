-- Migration 012: Remove drawings Table
-- Date: 2025-11-17
-- Purpose: Remove drawings table and complete migration to "Projects → Entities" architecture
--
-- Background:
-- This application has fully migrated from "Projects → Drawings → Entities" to "Projects → Entities".
-- The drawings table is no longer used:
-- - All DXF imports go directly to projects
-- - All entities reference project_id (drawing_id is always NULL)
-- - No code creates or manages drawings
--
-- Phase 4: drawings Table Removal
-- - Drop drawings table
-- - Drop any columns in other tables that reference drawings
-- - Update any remaining legacy code references

-- ============================================================================
-- BACKUP RECOMMENDATION
-- ============================================================================
-- Before running this migration, create a backup:
-- pg_dump survey_data > backup_before_drawings_table_removal_$(date +%Y%m%d).sql
-- ============================================================================

BEGIN;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting Migration 012: Remove drawings Table';
    RAISE NOTICE 'Time: %', NOW();
END $$;

-- ============================================================================
-- VALIDATION: Check if drawings table has any important data
-- ============================================================================

DO $$
DECLARE
    drawing_count INTEGER := 0;
BEGIN
    -- Check if drawings table exists and count records
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawings') THEN

        SELECT COUNT(*) INTO drawing_count FROM drawings;
        RAISE NOTICE 'Found % drawings in drawings table', drawing_count;

        IF drawing_count > 0 THEN
            RAISE WARNING 'drawings table contains % records - these will be deleted!', drawing_count;
        ELSE
            RAISE NOTICE '✓ drawings table is empty (expected)';
        END IF;
    ELSE
        RAISE NOTICE '✓ drawings table does not exist (already dropped)';
    END IF;
END $$;

-- ============================================================================
-- 1. DROP FOREIGN KEY COLUMNS IN OTHER TABLES
-- ============================================================================

-- Drop drawing_id from export_jobs if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'export_jobs' AND column_name = 'drawing_id') THEN
        ALTER TABLE export_jobs DROP COLUMN drawing_id;
        RAISE NOTICE '✓ Dropped drawing_id column from export_jobs table';
    ELSE
        RAISE NOTICE '✓ export_jobs.drawing_id column does not exist (already dropped)';
    END IF;
END $$;

-- ============================================================================
-- 2. DROP drawings TABLE
-- ============================================================================

DROP TABLE IF EXISTS drawings CASCADE;
RAISE NOTICE '✓ Dropped drawings table (if it existed)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify drawings table was dropped
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawings') THEN
        RAISE EXCEPTION 'ERROR: drawings table still exists!';
    END IF;

    -- Verify drawing_id column was dropped from export_jobs
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'export_jobs' AND column_name = 'drawing_id') THEN
        RAISE EXCEPTION 'ERROR: export_jobs.drawing_id column still exists!';
    END IF;

    RAISE NOTICE '✓ All verifications passed';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 012 Complete!';
    RAISE NOTICE 'Removed drawings table';
    RAISE NOTICE 'Architecture is now: Projects → Entities';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
END $$;

COMMIT;
