-- Migration 010: Remove space_type Columns
-- Date: 2025-11-17
-- Purpose: Remove space_type columns from drawing entity tables
--
-- Background:
-- The space_type column was used to distinguish between MODEL space and PAPER space entities.
-- After Migration 009, all PAPER space support has been removed.
-- All entities are now MODEL space only, making this column redundant.
--
-- Phase 2: space_type Column Removal
-- - Remove space_type from drawing_entities
-- - Remove space_type from drawing_text
-- - Remove space_type from drawing_dimensions
-- - Remove space_type from drawing_hatches
-- - Drop associated indexes

-- ============================================================================
-- BACKUP RECOMMENDATION
-- ============================================================================
-- Before running this migration, create a backup:
-- pg_dump survey_data > backup_before_space_type_removal_$(date +%Y%m%d).sql
-- ============================================================================

BEGIN;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting Migration 010: Remove space_type Columns';
    RAISE NOTICE 'Time: %', NOW();
END $$;

-- ============================================================================
-- VALIDATION: Ensure no PAPER space data exists
-- ============================================================================

DO $$
DECLARE
    paper_entities INTEGER := 0;
    paper_text INTEGER := 0;
    paper_dimensions INTEGER := 0;
    paper_hatches INTEGER := 0;
BEGIN
    -- Count PAPER space entities in each table
    SELECT COUNT(*) INTO paper_entities
    FROM drawing_entities
    WHERE space_type = 'PAPER';

    SELECT COUNT(*) INTO paper_text
    FROM drawing_text
    WHERE space_type = 'PAPER';

    SELECT COUNT(*) INTO paper_dimensions
    FROM drawing_dimensions
    WHERE space_type = 'PAPER';

    SELECT COUNT(*) INTO paper_hatches
    FROM drawing_hatches
    WHERE space_type = 'PAPER';

    RAISE NOTICE 'PAPER space data found:';
    RAISE NOTICE '  - drawing_entities: %', paper_entities;
    RAISE NOTICE '  - drawing_text: %', paper_text;
    RAISE NOTICE '  - drawing_dimensions: %', paper_dimensions;
    RAISE NOTICE '  - drawing_hatches: %', paper_hatches;

    -- Delete any PAPER space data (should be none)
    IF paper_entities > 0 THEN
        DELETE FROM drawing_entities WHERE space_type = 'PAPER';
        RAISE NOTICE '✓ Deleted % PAPER space entities', paper_entities;
    END IF;

    IF paper_text > 0 THEN
        DELETE FROM drawing_text WHERE space_type = 'PAPER';
        RAISE NOTICE '✓ Deleted % PAPER space text', paper_text;
    END IF;

    IF paper_dimensions > 0 THEN
        DELETE FROM drawing_dimensions WHERE space_type = 'PAPER';
        RAISE NOTICE '✓ Deleted % PAPER space dimensions', paper_dimensions;
    END IF;

    IF paper_hatches > 0 THEN
        DELETE FROM drawing_hatches WHERE space_type = 'PAPER';
        RAISE NOTICE '✓ Deleted % PAPER space hatches', paper_hatches;
    END IF;
END $$;

-- ============================================================================
-- 1. DROP INDEXES ON space_type
-- ============================================================================

DROP INDEX IF EXISTS idx_drawingent_space;
RAISE NOTICE '✓ Dropped index idx_drawingent_space';

DROP INDEX IF EXISTS idx_drawingtext_space;
RAISE NOTICE '✓ Dropped index idx_drawingtext_space';

-- ============================================================================
-- 2. DROP space_type COLUMNS
-- ============================================================================

-- drawing_entities
ALTER TABLE drawing_entities DROP COLUMN IF EXISTS space_type;
RAISE NOTICE '✓ Removed space_type from drawing_entities';

-- drawing_text
ALTER TABLE drawing_text DROP COLUMN IF EXISTS space_type;
RAISE NOTICE '✓ Removed space_type from drawing_text';

-- drawing_dimensions
ALTER TABLE drawing_dimensions DROP COLUMN IF EXISTS space_type;
RAISE NOTICE '✓ Removed space_type from drawing_dimensions';

-- drawing_hatches
ALTER TABLE drawing_hatches DROP COLUMN IF EXISTS space_type;
RAISE NOTICE '✓ Removed space_type from drawing_hatches';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify columns were dropped
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'drawing_entities' AND column_name = 'space_type') THEN
        RAISE EXCEPTION 'ERROR: space_type still exists in drawing_entities!';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'drawing_text' AND column_name = 'space_type') THEN
        RAISE EXCEPTION 'ERROR: space_type still exists in drawing_text!';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'drawing_dimensions' AND column_name = 'space_type') THEN
        RAISE EXCEPTION 'ERROR: space_type still exists in drawing_dimensions!';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'drawing_hatches' AND column_name = 'space_type') THEN
        RAISE EXCEPTION 'ERROR: space_type still exists in drawing_hatches!';
    END IF;

    RAISE NOTICE '✓ All space_type columns successfully removed';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 010 Complete!';
    RAISE NOTICE 'Removed space_type column from:';
    RAISE NOTICE '  - drawing_entities';
    RAISE NOTICE '  - drawing_text';
    RAISE NOTICE '  - drawing_dimensions';
    RAISE NOTICE '  - drawing_hatches';
    RAISE NOTICE 'Dropped indexes:';
    RAISE NOTICE '  - idx_drawingent_space';
    RAISE NOTICE '  - idx_drawingtext_space';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
END $$;

COMMIT;
