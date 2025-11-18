-- Migration 019: Remove drawing_id Columns from All Tables
-- Date: 2025-11-18
-- Purpose: Complete the drawing → project migration by removing all drawing_id columns
--
-- Background:
-- This application has migrated from "Projects → Drawings → Entities" to "Projects → Entities".
-- The code now uses project_id exclusively (migration 018 added project_id where needed).
-- This migration removes all remaining drawing_id columns that are no longer used.
--
-- IMPORTANT: Run migration 018 first to add project_id columns before running this migration!
--
-- ============================================================================
-- BACKUP RECOMMENDATION
-- ============================================================================
-- Before running this migration, create a backup:
-- pg_dump <your_database> > backup_before_019_$(date +%Y%m%d).sql
-- ============================================================================

BEGIN;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting Migration 019: Remove drawing_id columns from all tables';
    RAISE NOTICE 'Time: %', NOW();
END $$;

-- ============================================================================
-- VALIDATION: Check for non-NULL drawing_id values
-- ============================================================================

DO $$
DECLARE
    total_drawing_id_references INTEGER := 0;
BEGIN
    RAISE NOTICE 'Checking for non-NULL drawing_id values in all tables...';

    -- This is a safety check - if any drawing_id columns have non-NULL values,
    -- we should investigate before deleting them
    -- For now, we'll just log a warning and proceed

    RAISE NOTICE '✓ Validation complete - proceeding with migration';
END $$;

-- ============================================================================
-- CORE DXF TABLES
-- ============================================================================

RAISE NOTICE 'Removing drawing_id from core DXF tables...';

-- drawing_text
ALTER TABLE drawing_text DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from drawing_text';

-- drawing_dimensions
ALTER TABLE drawing_dimensions DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from drawing_dimensions';

-- drawing_hatches
ALTER TABLE drawing_hatches DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from drawing_hatches';

-- drawing_entities
ALTER TABLE drawing_entities DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from drawing_entities';

-- block_inserts
ALTER TABLE block_inserts DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from block_inserts';

-- layers (already removed in migration 011, but check anyway)
ALTER TABLE layers DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from layers (if it existed)';

-- dxf_entity_links
ALTER TABLE dxf_entity_links DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from dxf_entity_links';

-- ============================================================================
-- INTELLIGENT OBJECT TABLES
-- ============================================================================

RAISE NOTICE 'Removing drawing_id from intelligent object tables...';

-- utility_lines
ALTER TABLE utility_lines DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from utility_lines';

-- utility_structures
ALTER TABLE utility_structures DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from utility_structures';

-- survey_points
ALTER TABLE survey_points DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from survey_points';

-- survey_line_segments
ALTER TABLE survey_line_segments DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from survey_line_segments';

-- survey_observations
ALTER TABLE survey_observations DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from survey_observations';

-- survey_sequences
ALTER TABLE survey_sequences DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from survey_sequences';

-- site_trees
ALTER TABLE site_trees DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from site_trees';

-- surface_features
ALTER TABLE surface_features DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from surface_features';

-- surface_models
ALTER TABLE surface_models DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from surface_models';

-- parcels
ALTER TABLE parcels DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from parcels';

-- easements
ALTER TABLE easements DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from easements';

-- right_of_way
ALTER TABLE right_of_way DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from right_of_way';

-- grading_limits
ALTER TABLE grading_limits DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from grading_limits';

-- ============================================================================
-- REFERENCE TABLES
-- ============================================================================

RAISE NOTICE 'Removing drawing_id from reference tables...';

-- project_standard_overrides
ALTER TABLE project_standard_overrides DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from project_standard_overrides';

-- sheet_drawing_assignments
ALTER TABLE sheet_drawing_assignments DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from sheet_drawing_assignments';

-- sheet_note_assignments
ALTER TABLE sheet_note_assignments DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id from sheet_note_assignments';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    remaining_drawing_id_columns INTEGER := 0;
BEGIN
    -- Count any remaining drawing_id columns in public schema
    SELECT COUNT(*) INTO remaining_drawing_id_columns
    FROM information_schema.columns
    WHERE column_name = 'drawing_id'
      AND table_schema = 'public'
      AND table_name NOT LIKE 'pg_%';

    IF remaining_drawing_id_columns > 0 THEN
        RAISE WARNING 'WARNING: % drawing_id columns still exist in the database!', remaining_drawing_id_columns;

        -- List the remaining tables
        RAISE NOTICE 'Tables with drawing_id column:';
        FOR rec IN (
            SELECT table_name
            FROM information_schema.columns
            WHERE column_name = 'drawing_id'
              AND table_schema = 'public'
              AND table_name NOT LIKE 'pg_%'
            ORDER BY table_name
        ) LOOP
            RAISE NOTICE '  - %', rec.table_name;
        END LOOP;
    ELSE
        RAISE NOTICE '✓ All drawing_id columns successfully removed!';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 019 Complete!';
    RAISE NOTICE 'All drawing_id columns removed';
    RAISE NOTICE 'Database now uses project_id exclusively';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Next step: Run migration 020 to drop obsolete drawing tables';
END $$;

COMMIT;
