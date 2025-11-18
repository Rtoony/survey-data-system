-- Migration 020: Drop Obsolete Drawing Tables
-- Date: 2025-11-18
-- Purpose: Remove obsolete drawing-related tables that are no longer used
--
-- Background:
-- This application has fully migrated from "Projects → Drawings → Entities" to "Projects → Entities".
-- These tables were used for tracking drawing-level metadata and are no longer needed:
-- - drawing_materials: Tracked materials used in specific drawings
-- - drawing_references: Tracked reference relationships between drawings
-- - drawings: Main drawings table (may have been removed in migration 012)
--
-- IMPORTANT: Run migrations 018 and 019 first before running this migration!
--
-- ============================================================================
-- BACKUP RECOMMENDATION
-- ============================================================================
-- Before running this migration, create a backup:
-- pg_dump <your_database> > backup_before_020_$(date +%Y%m%d).sql
-- ============================================================================

BEGIN;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting Migration 020: Drop obsolete drawing tables';
    RAISE NOTICE 'Time: %', NOW();
END $$;

-- ============================================================================
-- VALIDATION: Check if tables exist and contain data
-- ============================================================================

DO $$
DECLARE
    materials_count INTEGER := 0;
    references_count INTEGER := 0;
    drawings_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Checking for data in obsolete tables...';

    -- Check drawing_materials
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawing_materials' AND table_schema = 'public') THEN
        EXECUTE 'SELECT COUNT(*) FROM drawing_materials' INTO materials_count;
        RAISE NOTICE 'drawing_materials table exists with % records', materials_count;

        IF materials_count > 0 THEN
            RAISE WARNING 'drawing_materials contains % records - these will be deleted!', materials_count;
        END IF;
    ELSE
        RAISE NOTICE '✓ drawing_materials table does not exist (already dropped)';
    END IF;

    -- Check drawing_references
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawing_references' AND table_schema = 'public') THEN
        EXECUTE 'SELECT COUNT(*) FROM drawing_references' INTO references_count;
        RAISE NOTICE 'drawing_references table exists with % records', references_count;

        IF references_count > 0 THEN
            RAISE WARNING 'drawing_references contains % records - these will be deleted!', references_count;
        END IF;
    ELSE
        RAISE NOTICE '✓ drawing_references table does not exist (already dropped)';
    END IF;

    -- Check drawings
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'drawings' AND table_schema = 'public') THEN
        EXECUTE 'SELECT COUNT(*) FROM drawings' INTO drawings_count;
        RAISE NOTICE 'drawings table exists with % records', drawings_count;

        IF drawings_count > 0 THEN
            RAISE WARNING 'drawings contains % records - these will be deleted!', drawings_count;
        END IF;
    ELSE
        RAISE NOTICE '✓ drawings table does not exist (already dropped in migration 012)';
    END IF;
END $$;

-- ============================================================================
-- DROP OBSOLETE TABLES
-- ============================================================================

RAISE NOTICE 'Dropping obsolete drawing tables...';

-- Drop drawing_materials table
DROP TABLE IF EXISTS drawing_materials CASCADE;
RAISE NOTICE '✓ Dropped drawing_materials table (if it existed)';

-- Drop drawing_references table
DROP TABLE IF EXISTS drawing_references CASCADE;
RAISE NOTICE '✓ Dropped drawing_references table (if it existed)';

-- Drop drawings table (may have been removed in migration 012, but check anyway)
DROP TABLE IF EXISTS drawings CASCADE;
RAISE NOTICE '✓ Dropped drawings table (if it existed)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    obsolete_tables_remaining INTEGER := 0;
BEGIN
    -- Count any remaining obsolete tables
    SELECT COUNT(*) INTO obsolete_tables_remaining
    FROM information_schema.tables
    WHERE table_name IN ('drawing_materials', 'drawing_references', 'drawings')
      AND table_schema = 'public';

    IF obsolete_tables_remaining > 0 THEN
        RAISE EXCEPTION 'ERROR: % obsolete drawing tables still exist!', obsolete_tables_remaining;
    ELSE
        RAISE NOTICE '✓ All obsolete drawing tables successfully removed!';
    END IF;

    -- Final check: Verify no tables have drawing_id columns
    DECLARE
        tables_with_drawing_id INTEGER := 0;
    BEGIN
        SELECT COUNT(DISTINCT table_name) INTO tables_with_drawing_id
        FROM information_schema.columns
        WHERE column_name = 'drawing_id'
          AND table_schema = 'public'
          AND table_name NOT LIKE 'pg_%';

        IF tables_with_drawing_id > 0 THEN
            RAISE WARNING 'Note: % tables still have drawing_id column - run migration 019 if not done yet', tables_with_drawing_id;
        ELSE
            RAISE NOTICE '✓ No drawing_id columns found in database (migration 019 complete!)';
        END IF;
    END;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 020 Complete!';
    RAISE NOTICE 'All obsolete drawing tables removed';
    RAISE NOTICE '';
    RAISE NOTICE 'Migration Summary:';
    RAISE NOTICE '  - Dropped: drawing_materials';
    RAISE NOTICE '  - Dropped: drawing_references';
    RAISE NOTICE '  - Dropped: drawings (if not already removed)';
    RAISE NOTICE '';
    RAISE NOTICE 'Architecture is now: Projects → Entities';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
END $$;

COMMIT;
