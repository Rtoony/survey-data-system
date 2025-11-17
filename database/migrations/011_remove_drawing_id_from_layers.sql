-- Migration 011: Remove drawing_id Column from layers Table
-- Date: 2025-11-17
-- Purpose: Remove drawing_id column from layers table
--
-- Background:
-- This application has migrated from "Projects → Drawings → Entities" to "Projects → Entities" architecture.
-- The layers table previously supported both project-level and drawing-level layers.
-- All layers are now project-level only, making drawing_id obsolete.
--
-- Phase 3: drawing_id Column Removal from layers
-- - Drop unique index idx_layers_project_layer_unique (has WHERE drawing_id IS NULL clause)
-- - Recreate unique index without WHERE clause
-- - Remove drawing_id column from layers table

-- ============================================================================
-- BACKUP RECOMMENDATION
-- ============================================================================
-- Before running this migration, create a backup:
-- pg_dump survey_data > backup_before_drawing_id_removal_$(date +%Y%m%d).sql
-- ============================================================================

BEGIN;

-- Log migration start
DO $$
BEGIN
    RAISE NOTICE 'Starting Migration 011: Remove drawing_id from layers';
    RAISE NOTICE 'Time: %', NOW();
END $$;

-- ============================================================================
-- VALIDATION: Ensure no drawing-level layers exist
-- ============================================================================

DO $$
DECLARE
    drawing_layers INTEGER := 0;
BEGIN
    -- Count drawing-level layers (where drawing_id IS NOT NULL)
    SELECT COUNT(*) INTO drawing_layers
    FROM layers
    WHERE drawing_id IS NOT NULL;

    RAISE NOTICE 'Drawing-level layers found: %', drawing_layers;

    -- Delete any drawing-level layers (should be none after code changes)
    IF drawing_layers > 0 THEN
        RAISE WARNING 'Found % drawing-level layers - these will be deleted!', drawing_layers;
        DELETE FROM layers WHERE drawing_id IS NOT NULL;
        RAISE NOTICE '✓ Deleted % drawing-level layers', drawing_layers;
    ELSE
        RAISE NOTICE '✓ No drawing-level layers found (expected)';
    END IF;
END $$;

-- ============================================================================
-- 1. DROP EXISTING UNIQUE INDEX
-- ============================================================================
-- The current index has a WHERE clause: WHERE (drawing_id IS NULL)
-- This was used to allow multiple drawing-level layers with the same name
-- but ensure project-level layers (drawing_id IS NULL) are unique per project

DROP INDEX IF EXISTS idx_layers_project_layer_unique;
RAISE NOTICE '✓ Dropped index idx_layers_project_layer_unique';

-- ============================================================================
-- 2. DROP drawing_id COLUMN
-- ============================================================================

ALTER TABLE layers DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id column from layers table';

-- ============================================================================
-- 3. RECREATE UNIQUE INDEX (without WHERE clause)
-- ============================================================================
-- Now that drawing_id is gone, we can have a simple unique constraint
-- on (project_id, layer_name) without any WHERE clause

CREATE UNIQUE INDEX idx_layers_project_layer_unique
ON layers (project_id, layer_name);
RAISE NOTICE '✓ Created new unique index idx_layers_project_layer_unique';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify column was dropped
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'layers' AND column_name = 'drawing_id') THEN
        RAISE EXCEPTION 'ERROR: drawing_id column still exists in layers table!';
    END IF;

    -- Verify new index exists
    IF NOT EXISTS (SELECT 1 FROM pg_indexes
                   WHERE tablename = 'layers' AND indexname = 'idx_layers_project_layer_unique') THEN
        RAISE EXCEPTION 'ERROR: Index idx_layers_project_layer_unique was not created!';
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
    RAISE NOTICE 'Migration 011 Complete!';
    RAISE NOTICE 'Removed drawing_id from layers table';
    RAISE NOTICE 'Recreated unique index without WHERE clause';
    RAISE NOTICE 'All layers are now project-level only';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
END $$;

COMMIT;
