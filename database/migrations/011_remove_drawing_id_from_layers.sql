-- Migration 011: Remove drawing_id from layers Table
-- Date: 2025-11-17
-- Purpose: Remove drawing_id column from layers table
--
-- Background:
-- The system has migrated to "Projects Only" architecture where entities link
-- directly to projects, not to drawings. The drawing_id column in the layers
-- table is no longer needed as layers are now project-level only.
--
-- Phase 3: drawing_id Removal from layers
-- - Verify all layer records have drawing_id IS NULL
-- - Drop the unique constraint that includes drawing_id
-- - Remove drawing_id column from layers
-- - Recreate unique constraint without drawing_id

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
-- VALIDATION: Ensure all layers have drawing_id IS NULL
-- ============================================================================

DO $$
DECLARE
    layers_with_drawing_id INTEGER := 0;
BEGIN
    -- Count layers with non-NULL drawing_id
    SELECT COUNT(*) INTO layers_with_drawing_id
    FROM layers
    WHERE drawing_id IS NOT NULL;

    RAISE NOTICE 'Layers with non-NULL drawing_id: %', layers_with_drawing_id;

    -- If any exist, this indicates data that may need review
    IF layers_with_drawing_id > 0 THEN
        RAISE WARNING 'Found % layers with drawing_id set. Setting to NULL...', layers_with_drawing_id;

        -- Set all drawing_id values to NULL
        UPDATE layers SET drawing_id = NULL WHERE drawing_id IS NOT NULL;

        RAISE NOTICE '✓ Set drawing_id to NULL for % layers', layers_with_drawing_id;
    END IF;
END $$;

-- ============================================================================
-- 1. DROP EXISTING UNIQUE INDEX
-- ============================================================================

DROP INDEX IF EXISTS idx_layers_project_layer_unique;
RAISE NOTICE '✓ Dropped index idx_layers_project_layer_unique';

-- ============================================================================
-- 2. DROP drawing_id COLUMN
-- ============================================================================

ALTER TABLE layers DROP COLUMN IF EXISTS drawing_id;
RAISE NOTICE '✓ Removed drawing_id column from layers table';

-- ============================================================================
-- 3. RECREATE UNIQUE INDEX WITHOUT drawing_id
-- ============================================================================

-- Create unique constraint on project_id + layer_name only
-- This ensures each layer name is unique within a project
CREATE UNIQUE INDEX idx_layers_project_layer_unique
ON layers (project_id, layer_name);

RAISE NOTICE '✓ Created new unique index on (project_id, layer_name)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Verify drawing_id column was dropped
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'layers' AND column_name = 'drawing_id') THEN
        RAISE EXCEPTION 'ERROR: drawing_id still exists in layers table!';
    END IF;

    -- Verify new unique index exists
    IF NOT EXISTS (SELECT 1 FROM pg_indexes
                   WHERE tablename = 'layers'
                   AND indexname = 'idx_layers_project_layer_unique') THEN
        RAISE EXCEPTION 'ERROR: New unique index was not created!';
    END IF;

    RAISE NOTICE '✓ Verification successful - drawing_id removed, unique index recreated';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 011 Complete!';
    RAISE NOTICE 'Removed drawing_id column from layers';
    RAISE NOTICE 'Recreated unique index on (project_id, layer_name)';
    RAISE NOTICE 'Time: %', NOW();
    RAISE NOTICE '========================================';
END $$;

COMMIT;
