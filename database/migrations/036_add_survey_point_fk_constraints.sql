-- Migration 036: Add FK Constraints for Survey Points and Coordinate Systems
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Enforce referential integrity for survey point descriptions and coordinate systems
-- This migration adds 2 FK constraints (projects.default_coordinate_system_id already exists)

-- ============================================================================
-- PRE-MIGRATION CHECKS
-- ============================================================================

-- Verify prerequisite tables exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'survey_point_description_standards') THEN
        RAISE EXCEPTION 'Table survey_point_description_standards does not exist. Run migration 035 first.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'coordinate_systems') THEN
        RAISE EXCEPTION 'Table coordinate_systems does not exist. Check database schema.';
    END IF;

    RAISE NOTICE 'Prerequisite tables verified';
END $$;

-- ============================================================================
-- ADD COLUMNS TO SURVEY_POINTS
-- ============================================================================

-- Add coord_system_id for FK to coordinate_systems
ALTER TABLE survey_points
ADD COLUMN IF NOT EXISTS coord_system_id UUID;

COMMENT ON COLUMN survey_points.coord_system_id IS 'FK to coordinate_systems table - replaces text coordinate_system column';

-- Add description_code for FK to survey_point_description_standards
ALTER TABLE survey_points
ADD COLUMN IF NOT EXISTS description_code VARCHAR(20);

COMMENT ON COLUMN survey_points.description_code IS 'FK to survey_point_description_standards - replaces text point_description column';

-- ============================================================================
-- DATA MIGRATION - Map Existing Data to Standards
-- ============================================================================

-- Step 1: Map coordinate system text to coordinate_systems.system_id
-- Try to match by epsg_code first, then by system name

UPDATE survey_points sp
SET coord_system_id = cs.system_id
FROM coordinate_systems cs
WHERE sp.coord_system_id IS NULL
  AND sp.epsg_code IS NOT NULL
  AND cs.epsg_code = sp.epsg_code;

-- Report migration results
DO $$
DECLARE
    mapped_count INTEGER;
    unmapped_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO mapped_count FROM survey_points WHERE coord_system_id IS NOT NULL;
    SELECT COUNT(*) INTO unmapped_count FROM survey_points WHERE coord_system_id IS NULL;

    RAISE NOTICE 'Coordinate system mapping: % points mapped, % unmapped', mapped_count, unmapped_count;

    IF unmapped_count > 0 THEN
        RAISE NOTICE 'Unmapped points will have NULL coord_system_id (no match found)';
    END IF;
END $$;

-- Step 2: Map point_description text to description_code
-- Common mappings for survey point descriptions

-- Direct code matches (if point_description is already a code like "EP", "TW", etc.)
UPDATE survey_points
SET description_code = UPPER(TRIM(point_description))
WHERE description_code IS NULL
  AND point_description IS NOT NULL
  AND UPPER(TRIM(point_description)) IN (
      SELECT description_code FROM survey_point_description_standards WHERE is_active = true
  );

-- Common text to code mappings
UPDATE survey_points SET description_code = 'EP'
WHERE description_code IS NULL AND point_description ILIKE '%edge%pave%';

UPDATE survey_points SET description_code = 'CL'
WHERE description_code IS NULL AND point_description ILIKE '%center%line%';

UPDATE survey_points SET description_code = 'TW'
WHERE description_code IS NULL AND point_description ILIKE '%top%wall%';

UPDATE survey_points SET description_code = 'BW'
WHERE description_code IS NULL AND point_description ILIKE '%bottom%wall%';

UPDATE survey_points SET description_code = 'FW'
WHERE description_code IS NULL AND point_description ILIKE '%face%wall%';

UPDATE survey_points SET description_code = 'FG'
WHERE description_code IS NULL AND point_description ILIKE '%face%curb%';

UPDATE survey_points SET description_code = 'BC'
WHERE description_code IS NULL AND point_description ILIKE '%back%curb%';

UPDATE survey_points SET description_code = 'TG'
WHERE description_code IS NULL AND point_description ILIKE '%top%gutter%';

UPDATE survey_points SET description_code = 'FL'
WHERE description_code IS NULL AND (point_description ILIKE '%flow%line%' OR point_description ILIKE '%flowline%');

UPDATE survey_points SET description_code = 'MH'
WHERE description_code IS NULL AND point_description ILIKE '%manhole%';

UPDATE survey_points SET description_code = 'CB'
WHERE description_code IS NULL AND point_description ILIKE '%catch%basin%';

UPDATE survey_points SET description_code = 'HYDRANT'
WHERE description_code IS NULL AND point_description ILIKE '%hydrant%';

UPDATE survey_points SET description_code = 'WV'
WHERE description_code IS NULL AND point_description ILIKE '%water%valve%';

UPDATE survey_points SET description_code = 'POLE'
WHERE description_code IS NULL AND (point_description ILIKE '%pole%' OR point_description ILIKE '%power%pole%');

UPDATE survey_points SET description_code = 'TREE'
WHERE description_code IS NULL AND point_description ILIKE '%tree%';

UPDATE survey_points SET description_code = 'BENCHMARK'
WHERE description_code IS NULL AND (point_description ILIKE '%bench%mark%' OR point_description ILIKE '%BM%');

UPDATE survey_points SET description_code = 'CONTROL'
WHERE description_code IS NULL AND point_description ILIKE '%control%point%';

UPDATE survey_points SET description_code = 'MONUMENT'
WHERE description_code IS NULL AND point_description ILIKE '%monument%';

UPDATE survey_points SET description_code = 'TOPO'
WHERE description_code IS NULL AND point_description ILIKE '%topo%';

UPDATE survey_points SET description_code = 'TOB'
WHERE description_code IS NULL AND point_description ILIKE '%top%bank%';

UPDATE survey_points SET description_code = 'BOB'
WHERE description_code IS NULL AND point_description ILIKE '%bottom%bank%';

UPDATE survey_points SET description_code = 'TOS'
WHERE description_code IS NULL AND point_description ILIKE '%top%slope%';

UPDATE survey_points SET description_code = 'BOS'
WHERE description_code IS NULL AND point_description ILIKE '%bottom%slope%';

UPDATE survey_points SET description_code = 'SIGN'
WHERE description_code IS NULL AND point_description ILIKE '%sign%';

UPDATE survey_points SET description_code = 'LP'
WHERE description_code IS NULL AND point_description ILIKE '%light%';

UPDATE survey_points SET description_code = 'INLET'
WHERE description_code IS NULL AND point_description ILIKE '%inlet%';

-- Report description mapping results
DO $$
DECLARE
    mapped_count INTEGER;
    unmapped_count INTEGER;
    unmapped_samples TEXT;
BEGIN
    SELECT COUNT(*) INTO mapped_count FROM survey_points WHERE description_code IS NOT NULL;
    SELECT COUNT(*) INTO unmapped_count FROM survey_points WHERE description_code IS NULL AND point_description IS NOT NULL;

    -- Get sample of unmapped descriptions
    SELECT STRING_AGG(DISTINCT point_description, ', ')
    INTO unmapped_samples
    FROM (
        SELECT point_description
        FROM survey_points
        WHERE description_code IS NULL AND point_description IS NOT NULL
        LIMIT 10
    ) AS samples;

    RAISE NOTICE 'Description mapping: % points mapped, % unmapped', mapped_count, unmapped_count;

    IF unmapped_count > 0 THEN
        RAISE NOTICE 'Unmapped descriptions (sample): %', unmapped_samples;
        RAISE NOTICE 'These will have NULL description_code. Consider adding them to survey_point_description_standards.';
    END IF;
END $$;

-- ============================================================================
-- ADD FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Constraint 1: survey_points.coord_system_id → coordinate_systems.system_id
ALTER TABLE survey_points
DROP CONSTRAINT IF EXISTS fk_survey_points_coord_system;

ALTER TABLE survey_points
ADD CONSTRAINT fk_survey_points_coord_system
FOREIGN KEY (coord_system_id) REFERENCES coordinate_systems(system_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_survey_points_coord_system ON survey_points IS 'FK constraint enforcing survey_points.coord_system_id must match coordinate_systems.system_id';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_survey_points_coord_system_id ON survey_points(coord_system_id);

-- Constraint 2: survey_points.description_code → survey_point_description_standards.description_code
ALTER TABLE survey_points
DROP CONSTRAINT IF EXISTS fk_survey_points_description;

ALTER TABLE survey_points
ADD CONSTRAINT fk_survey_points_description
FOREIGN KEY (description_code) REFERENCES survey_point_description_standards(description_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_survey_points_description ON survey_points IS 'FK constraint enforcing survey_points.description_code must match survey_point_description_standards.description_code';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_survey_points_description_code ON survey_points(description_code);

-- ============================================================================
-- VERIFY EXISTING CONSTRAINT (projects.default_coordinate_system_id)
-- ============================================================================

-- This constraint should already exist from earlier migrations
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'projects_default_coordinate_system_id_fkey'
    ) THEN
        RAISE NOTICE '✓ Verified: projects.default_coordinate_system_id FK constraint already exists';
    ELSE
        RAISE WARNING 'projects.default_coordinate_system_id FK constraint does not exist. It should have been created earlier.';
    END IF;
END $$;

-- ============================================================================
-- VERIFY ALL CONSTRAINTS WERE ADDED
-- ============================================================================

DO $$
DECLARE
    constraint_count INT;
BEGIN
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE constraint_name IN (
        'fk_survey_points_coord_system',
        'fk_survey_points_description'
    ) AND constraint_type = 'FOREIGN KEY';

    IF constraint_count = 2 THEN
        RAISE NOTICE '✓ SUCCESS: 2 new FK constraints added for Phase 2';
        RAISE NOTICE '  - fk_survey_points_coord_system';
        RAISE NOTICE '  - fk_survey_points_description';
        RAISE NOTICE '  + projects.default_coordinate_system_id_fkey (already existed)';
        RAISE NOTICE 'Total Phase 2 FK constraints: 3';
    ELSE
        RAISE WARNING 'Only % of 2 expected FK constraints were added', constraint_count;
    END IF;
END $$;

-- ============================================================================
-- TESTING - Verify constraints work correctly
-- ============================================================================

-- Test 1: Try to insert survey point with invalid coord_system_id (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO survey_points (point_number, coord_system_id, geometry)
        VALUES ('TEST-001', gen_random_uuid(), ST_GeomFromText('POINT Z (0 0 0)', 2226));
        RAISE EXCEPTION 'TEST FAILED: Invalid coord_system_id was accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ TEST PASSED: Invalid coord_system_id correctly rejected';
    END;
END $$;

-- Test 2: Try to insert survey point with invalid description_code (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO survey_points (point_number, description_code, geometry)
        VALUES ('TEST-002', 'INVALID_CODE', ST_GeomFromText('POINT Z (0 0 0)', 2226));
        RAISE EXCEPTION 'TEST FAILED: Invalid description_code was accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ TEST PASSED: Invalid description_code correctly rejected';
    END;
END $$;

-- Test 3: Insert valid survey point (should succeed)
DO $$
DECLARE
    test_point_id UUID;
    valid_coord_system_id UUID;
BEGIN
    -- Get a valid coordinate system
    SELECT system_id INTO valid_coord_system_id FROM coordinate_systems LIMIT 1;

    IF valid_coord_system_id IS NOT NULL THEN
        INSERT INTO survey_points (point_number, coord_system_id, description_code, geometry)
        VALUES ('TEST-003', valid_coord_system_id, 'EP', ST_GeomFromText('POINT Z (0 0 0)', 2226))
        RETURNING point_id INTO test_point_id;

        -- Clean up test record
        DELETE FROM survey_points WHERE point_id = test_point_id;

        RAISE NOTICE '✓ TEST PASSED: Valid FK values correctly accepted';
    ELSE
        RAISE NOTICE '⚠ TEST SKIPPED: No coordinate systems in database to test with';
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'TEST FAILED: Valid FK values were rejected: %', SQLERRM;
END $$;

-- Migration complete
RAISE NOTICE '';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Migration 036 Complete - Phase 2 FK Constraints';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Added 2 new FK constraints:';
RAISE NOTICE '  1. survey_points.coord_system_id → coordinate_systems';
RAISE NOTICE '  2. survey_points.description_code → survey_point_description_standards';
RAISE NOTICE '';
RAISE NOTICE 'Existing FK constraint verified:';
RAISE NOTICE '  3. projects.default_coordinate_system_id → coordinate_systems';
RAISE NOTICE '=====================================================';
