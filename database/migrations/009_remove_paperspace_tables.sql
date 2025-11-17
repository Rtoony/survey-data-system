-- Migration 009: Remove Paper Space Tables and Unused Drawing Tracking Tables
-- Date: 2025-11-17
-- Purpose: Clean up legacy paper space and drawing-level tracking tables
--
-- Background:
-- This application has migrated from "Projects → Drawings → Entities" to "Projects → Entities" architecture.
-- Paper space (AutoCAD layout/viewport) functionality is completely irrelevant to our GIS use case.
-- We only care about Model Space entities.
--
-- Phase 1: Paper Space Cleanup
-- - Drop layout_viewports table (100% paper space)
-- - Drop drawing_layer_usage table (unused, no code references)
-- - Drop drawing_linetype_usage table (unused, no code references)

-- ============================================================================
-- BACKUP RECOMMENDATION
-- ============================================================================
-- Before running this migration, create a backup:
-- pg_dump survey_data > backup_before_paperspace_cleanup_$(date +%Y%m%d).sql
-- ============================================================================

BEGIN;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting Migration 009: Remove Paper Space Tables';
    RAISE NOTICE 'Time: %', NOW();
END $$;

-- ============================================================================
-- 1. DROP LAYOUT_VIEWPORTS TABLE (Paper Space Only)
-- ============================================================================
-- This table stores paper space viewport configurations (print layouts).
-- Our application only uses Model Space for GIS data.
-- All import/export code now skips paper space entirely.

DO $$
DECLARE
    viewport_count INTEGER;
BEGIN
    -- Check if table exists and count records
    SELECT COUNT(*) INTO viewport_count
    FROM layout_viewports;

    RAISE NOTICE 'Found % viewport records (will be deleted)', viewport_count;

    IF viewport_count > 0 THEN
        RAISE WARNING 'layout_viewports contains data that will be permanently deleted';
    END IF;
END $$;

-- Drop indexes first
DROP INDEX IF EXISTS idx_viewports_layout;

-- Drop the table
DROP TABLE IF EXISTS layout_viewports CASCADE;

RAISE NOTICE '✓ Dropped layout_viewports table';

-- ============================================================================
-- 2. DROP DRAWING_LAYER_USAGE TABLE (Unused)
-- ============================================================================
-- This table was intended to track layer usage per drawing.
-- No code references found. Table structure is incomplete (missing drawing_id FK).

DO $$
DECLARE
    usage_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO usage_count
    FROM drawing_layer_usage;

    RAISE NOTICE 'Found % layer usage records (will be deleted)', usage_count;
END $$;

-- Drop the table
DROP TABLE IF EXISTS drawing_layer_usage CASCADE;

RAISE NOTICE '✓ Dropped drawing_layer_usage table';

-- ============================================================================
-- 3. DROP DRAWING_LINETYPE_USAGE TABLE (Unused)
-- ============================================================================
-- This table was intended to track linetype usage per drawing.
-- No code references found. Table structure is incomplete (missing drawing_id FK).

DO $$
DECLARE
    usage_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO usage_count
    FROM drawing_linetype_usage;

    RAISE NOTICE 'Found % linetype usage records (will be deleted)', usage_count;
END $$;

-- Drop the table
DROP TABLE IF EXISTS drawing_linetype_usage CASCADE;

RAISE NOTICE '✓ Dropped drawing_linetype_usage table';

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Verify tables were dropped successfully

DO $$
BEGIN
    -- Check layout_viewports
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'layout_viewports') THEN
        RAISE EXCEPTION 'ERROR: layout_viewports table still exists!';
    END IF;

    -- Check drawing_layer_usage
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawing_layer_usage') THEN
        RAISE EXCEPTION 'ERROR: drawing_layer_usage table still exists!';
    END IF;

    -- Check drawing_linetype_usage
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawing_linetype_usage') THEN
        RAISE EXCEPTION 'ERROR: drawing_linetype_usage table still exists!';
    END IF;

    RAISE NOTICE '✓ All tables successfully dropped';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 009 Complete!';
    RAISE NOTICE 'Dropped tables:';
    RAISE NOTICE '  - layout_viewports (paper space)';
    RAISE NOTICE '  - drawing_layer_usage (unused)';
    RAISE NOTICE '  - drawing_linetype_usage (unused)';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
END $$;

COMMIT;
