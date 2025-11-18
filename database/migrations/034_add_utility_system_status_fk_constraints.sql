-- Migration 034: Add FK Constraints for Utility Systems and Status
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Enforce referential integrity for utility_system and status columns
-- This migration adds 5 FK constraints to complete Phase 1

-- ============================================================================
-- PRE-MIGRATION DATA VALIDATION
-- ============================================================================

-- Step 1: Check for non-conforming utility_system values in utility_lines
DO $$
DECLARE
    non_conforming_count INT;
    non_conforming_values TEXT;
BEGIN
    SELECT COUNT(DISTINCT utility_system), STRING_AGG(DISTINCT utility_system, ', ')
    INTO non_conforming_count, non_conforming_values
    FROM utility_lines
    WHERE utility_system IS NOT NULL
    AND utility_system NOT IN (SELECT system_code FROM utility_system_standards WHERE is_active = true);

    IF non_conforming_count > 0 THEN
        RAISE WARNING 'Found % non-conforming utility_system values in utility_lines: %', non_conforming_count, non_conforming_values;
        RAISE NOTICE 'Run this query to see details: SELECT DISTINCT utility_system, COUNT(*) FROM utility_lines WHERE utility_system NOT IN (SELECT system_code FROM utility_system_standards) GROUP BY utility_system;';
    ELSE
        RAISE NOTICE 'All utility_lines.utility_system values conform to utility_system_standards';
    END IF;
END $$;

-- Step 2: Check for non-conforming utility_system values in utility_structures
DO $$
DECLARE
    non_conforming_count INT;
    non_conforming_values TEXT;
BEGIN
    SELECT COUNT(DISTINCT utility_system), STRING_AGG(DISTINCT utility_system, ', ')
    INTO non_conforming_count, non_conforming_values
    FROM utility_structures
    WHERE utility_system IS NOT NULL
    AND utility_system NOT IN (SELECT system_code FROM utility_system_standards WHERE is_active = true);

    IF non_conforming_count > 0 THEN
        RAISE WARNING 'Found % non-conforming utility_system values in utility_structures: %', non_conforming_count, non_conforming_values;
    ELSE
        RAISE NOTICE 'All utility_structures.utility_system values conform to utility_system_standards';
    END IF;
END $$;

-- ============================================================================
-- DATA MIGRATION - Map Non-Conforming Values to Standards
-- ============================================================================

-- Common mappings for utility systems
-- This handles various spellings and abbreviations

-- Update utility_lines to use standard codes
UPDATE utility_lines SET utility_system = 'STORM' WHERE utility_system IN ('SD', 'Storm', 'storm', 'Storm Drain', 'STORM DRAIN');
UPDATE utility_lines SET utility_system = 'SEWER' WHERE utility_system IN ('SS', 'Sewer', 'sewer', 'Sanitary', 'SANITARY');
UPDATE utility_lines SET utility_system = 'WATER' WHERE utility_system IN ('W', 'Water', 'water', 'POTABLE');
UPDATE utility_lines SET utility_system = 'RECLAIM' WHERE utility_system IN ('R', 'RW', 'Reclaim', 'reclaim', 'Reclaimed');
UPDATE utility_lines SET utility_system = 'GAS' WHERE utility_system IN ('G', 'Gas', 'gas', 'NG', 'NATURAL GAS');
UPDATE utility_lines SET utility_system = 'ELECTRIC' WHERE utility_system IN ('E', 'Electric', 'electric', 'ELEC', 'Power');
UPDATE utility_lines SET utility_system = 'TELECOM' WHERE utility_system IN ('T', 'Tel', 'Telecom', 'telecom', 'Phone');
UPDATE utility_lines SET utility_system = 'CABLE' WHERE utility_system IN ('C', 'Cable', 'cable', 'CATV');
UPDATE utility_lines SET utility_system = 'FIBER' WHERE utility_system IN ('F', 'Fiber', 'fiber', 'FO');
UPDATE utility_lines SET utility_system = 'IRRIGATION' WHERE utility_system IN ('I', 'IRR', 'Irrigation', 'irrigation');

-- Update utility_structures to use standard codes (same mappings)
UPDATE utility_structures SET utility_system = 'STORM' WHERE utility_system IN ('SD', 'Storm', 'storm', 'Storm Drain', 'STORM DRAIN');
UPDATE utility_structures SET utility_system = 'SEWER' WHERE utility_system IN ('SS', 'Sewer', 'sewer', 'Sanitary', 'SANITARY');
UPDATE utility_structures SET utility_system = 'WATER' WHERE utility_system IN ('W', 'Water', 'water', 'POTABLE');
UPDATE utility_structures SET utility_system = 'RECLAIM' WHERE utility_system IN ('R', 'RW', 'Reclaim', 'reclaim', 'Reclaimed');
UPDATE utility_structures SET utility_system = 'GAS' WHERE utility_system IN ('G', 'Gas', 'gas', 'NG', 'NATURAL GAS');
UPDATE utility_structures SET utility_system = 'ELECTRIC' WHERE utility_system IN ('E', 'Electric', 'electric', 'ELEC', 'Power');
UPDATE utility_structures SET utility_system = 'TELECOM' WHERE utility_system IN ('T', 'Tel', 'Telecom', 'telecom', 'Phone');
UPDATE utility_structures SET utility_system = 'CABLE' WHERE utility_system IN ('C', 'Cable', 'cable', 'CATV');
UPDATE utility_structures SET utility_system = 'FIBER' WHERE utility_system IN ('F', 'Fiber', 'fiber', 'FO');
UPDATE utility_structures SET utility_system = 'IRRIGATION' WHERE utility_system IN ('I', 'IRR', 'Irrigation', 'irrigation');

-- Set remaining non-conforming values to 'UNKNOWN'
UPDATE utility_lines
SET utility_system = 'UNKNOWN'
WHERE utility_system IS NOT NULL
AND utility_system NOT IN (SELECT system_code FROM utility_system_standards);

UPDATE utility_structures
SET utility_system = 'UNKNOWN'
WHERE utility_system IS NOT NULL
AND utility_system NOT IN (SELECT system_code FROM utility_system_standards);

-- Report migration results
DO $$
DECLARE
    lines_migrated INT;
    structures_migrated INT;
BEGIN
    SELECT COUNT(*) INTO lines_migrated FROM utility_lines WHERE utility_system IS NOT NULL;
    SELECT COUNT(*) INTO structures_migrated FROM utility_structures WHERE utility_system IS NOT NULL;
    RAISE NOTICE 'Data migration complete: % utility_lines, % utility_structures', lines_migrated, structures_migrated;
END $$;

-- ============================================================================
-- ADD FOREIGN KEY CONSTRAINTS - Utility Systems
-- ============================================================================

-- Constraint 1: utility_lines.utility_system → utility_system_standards.system_code
ALTER TABLE utility_lines
DROP CONSTRAINT IF EXISTS fk_utility_lines_system;

ALTER TABLE utility_lines
ADD CONSTRAINT fk_utility_lines_system
FOREIGN KEY (utility_system) REFERENCES utility_system_standards(system_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_utility_lines_system ON utility_lines IS 'FK constraint enforcing utility_lines.utility_system must match utility_system_standards.system_code';

-- Constraint 2: utility_structures.utility_system → utility_system_standards.system_code
ALTER TABLE utility_structures
DROP CONSTRAINT IF EXISTS fk_utility_structures_system;

ALTER TABLE utility_structures
ADD CONSTRAINT fk_utility_structures_system
FOREIGN KEY (utility_system) REFERENCES utility_system_standards(system_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_utility_structures_system ON utility_structures IS 'FK constraint enforcing utility_structures.utility_system must match utility_system_standards.system_code';

-- ============================================================================
-- ADD FOREIGN KEY CONSTRAINTS - Status
-- ============================================================================

-- Constraint 3: utility_lines.status → status_standards.status_code
ALTER TABLE utility_lines
DROP CONSTRAINT IF EXISTS fk_utility_lines_status;

ALTER TABLE utility_lines
ADD CONSTRAINT fk_utility_lines_status
FOREIGN KEY (status) REFERENCES status_standards(status_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_utility_lines_status ON utility_lines IS 'FK constraint enforcing utility_lines.status must match status_standards.status_code';

-- Constraint 4: utility_structures.status → status_standards.status_code
ALTER TABLE utility_structures
DROP CONSTRAINT IF EXISTS fk_utility_structures_status;

ALTER TABLE utility_structures
ADD CONSTRAINT fk_utility_structures_status
FOREIGN KEY (status) REFERENCES status_standards(status_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_utility_structures_status ON utility_structures IS 'FK constraint enforcing utility_structures.status must match status_standards.status_code';

-- ============================================================================
-- ADD PROJECT STATUS COLUMN AND FK CONSTRAINT
-- ============================================================================

-- Add project_status column to projects table if it doesn't exist
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS project_status VARCHAR(20) DEFAULT 'ACTIVE';

-- Set default status for existing projects
UPDATE projects
SET project_status = 'ACTIVE'
WHERE project_status IS NULL;

COMMENT ON COLUMN projects.project_status IS 'Status of project - must match status_standards.status_code where applies_to IN (PROJECT, ALL)';

-- Constraint 5: projects.project_status → status_standards.status_code
ALTER TABLE projects
DROP CONSTRAINT IF EXISTS fk_projects_status;

ALTER TABLE projects
ADD CONSTRAINT fk_projects_status
FOREIGN KEY (project_status) REFERENCES status_standards(status_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_projects_status ON projects IS 'FK constraint enforcing projects.project_status must match status_standards.status_code';

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
        'fk_utility_lines_system',
        'fk_utility_structures_system',
        'fk_utility_lines_status',
        'fk_utility_structures_status',
        'fk_projects_status'
    ) AND constraint_type = 'FOREIGN KEY';

    IF constraint_count = 5 THEN
        RAISE NOTICE '✓ SUCCESS: All 5 FK constraints added for Phase 1';
        RAISE NOTICE '  - fk_utility_lines_system';
        RAISE NOTICE '  - fk_utility_structures_system';
        RAISE NOTICE '  - fk_utility_lines_status';
        RAISE NOTICE '  - fk_utility_structures_status';
        RAISE NOTICE '  - fk_projects_status';
    ELSE
        RAISE WARNING 'Only % of 5 expected FK constraints were added', constraint_count;
    END IF;
END $$;

-- ============================================================================
-- TESTING - Verify constraints work correctly
-- ============================================================================

-- Test 1: Try to insert invalid utility_system (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO utility_lines (utility_system, geometry)
        VALUES ('INVALID_SYSTEM', ST_GeomFromText('LINESTRING Z (0 0 0, 1 1 1)', 2226));
        RAISE EXCEPTION 'TEST FAILED: Invalid utility_system was accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ TEST PASSED: Invalid utility_system correctly rejected';
    END;
END $$;

-- Test 2: Try to insert valid utility_system (should succeed)
DO $$
DECLARE
    new_line_id UUID;
BEGIN
    INSERT INTO utility_lines (utility_system, geometry)
    VALUES ('STORM', ST_GeomFromText('LINESTRING Z (0 0 0, 1 1 1)', 2226))
    RETURNING line_id INTO new_line_id;

    -- Clean up test record
    DELETE FROM utility_lines WHERE line_id = new_line_id;

    RAISE NOTICE '✓ TEST PASSED: Valid utility_system correctly accepted';
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'TEST FAILED: Valid utility_system was rejected: %', SQLERRM;
END $$;

-- Test 3: Try to insert invalid status (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO utility_lines (utility_system, status, geometry)
        VALUES ('STORM', 'INVALID_STATUS', ST_GeomFromText('LINESTRING Z (0 0 0, 1 1 1)', 2226));
        RAISE EXCEPTION 'TEST FAILED: Invalid status was accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ TEST PASSED: Invalid status correctly rejected';
    END;
END $$;

-- Test 4: Try to insert valid status (should succeed)
DO $$
DECLARE
    new_line_id UUID;
BEGIN
    INSERT INTO utility_lines (utility_system, status, geometry)
    VALUES ('STORM', 'EXISTING', ST_GeomFromText('LINESTRING Z (0 0 0, 1 1 1)', 2226))
    RETURNING line_id INTO new_line_id;

    -- Clean up test record
    DELETE FROM utility_lines WHERE line_id = new_line_id;

    RAISE NOTICE '✓ TEST PASSED: Valid status correctly accepted';
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'TEST FAILED: Valid status was rejected: %', SQLERRM;
END $$;

-- Migration complete
RAISE NOTICE '';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Migration 034 Complete - Phase 1 FK Constraints';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Added 5 FK constraints:';
RAISE NOTICE '  1. utility_lines.utility_system → utility_system_standards';
RAISE NOTICE '  2. utility_structures.utility_system → utility_system_standards';
RAISE NOTICE '  3. utility_lines.status → status_standards';
RAISE NOTICE '  4. utility_structures.status → status_standards';
RAISE NOTICE '  5. projects.project_status → status_standards';
RAISE NOTICE '=====================================================';
