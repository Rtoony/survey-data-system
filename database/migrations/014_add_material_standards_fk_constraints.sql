-- Migration 014: Add Material Standards FK Constraints
-- This fixes Critical Issue #1 from Architecture Audit Report
-- Date: 2025-11-17
--
-- Purpose: Enforce truth-driven architecture by adding FK constraints
-- from utility_lines.material and utility_structures.material to material_standards

-- Step 1: Add material_code column to material_standards if it doesn't exist
ALTER TABLE material_standards
ADD COLUMN IF NOT EXISTS material_code VARCHAR(50);

-- Step 2: Create an index and unique constraint on material_code
CREATE UNIQUE INDEX IF NOT EXISTS idx_material_standards_code
ON material_standards(material_code)
WHERE material_code IS NOT NULL;

-- Step 3: Populate material_code with normalized values from material_name
-- This is a one-time operation to standardize existing data
-- Common materials mapping:
-- 'PVC', 'pvc', 'P.V.C.' -> 'PVC'
-- 'Concrete', 'CONCRETE', 'concrete' -> 'CONCRETE'
-- etc.
UPDATE material_standards
SET material_code = UPPER(REGEXP_REPLACE(SPLIT_PART(material_name, ' ', 1), '[^A-Za-z0-9]', '', 'g'))
WHERE material_code IS NULL AND material_name IS NOT NULL;

-- Step 4: Check for materials in utility_lines that don't match material_standards
-- This query will show non-conforming values that need to be added or corrected
DO $$
DECLARE
    non_conforming_count INT;
BEGIN
    SELECT COUNT(DISTINCT material) INTO non_conforming_count
    FROM utility_lines
    WHERE material IS NOT NULL
    AND material NOT IN (SELECT material_code FROM material_standards WHERE material_code IS NOT NULL);

    IF non_conforming_count > 0 THEN
        RAISE NOTICE 'Warning: Found % distinct material values in utility_lines not in material_standards', non_conforming_count;
        RAISE NOTICE 'Run this query to see them: SELECT DISTINCT material FROM utility_lines WHERE material NOT IN (SELECT material_code FROM material_standards WHERE material_code IS NOT NULL) ORDER BY material;';
    ELSE
        RAISE NOTICE 'All utility_lines.material values conform to material_standards.material_code';
    END IF;
END $$;

-- Step 5: Check for materials in utility_structures that don't match material_standards
DO $$
DECLARE
    non_conforming_count INT;
BEGIN
    SELECT COUNT(DISTINCT material) INTO non_conforming_count
    FROM utility_structures
    WHERE material IS NOT NULL
    AND material NOT IN (SELECT material_code FROM material_standards WHERE material_code IS NOT NULL);

    IF non_conforming_count > 0 THEN
        RAISE NOTICE 'Warning: Found % distinct material values in utility_structures not in material_standards', non_conforming_count;
        RAISE NOTICE 'Run this query to see them: SELECT DISTINCT material FROM utility_structures WHERE material NOT IN (SELECT material_code FROM material_standards WHERE material_code IS NOT NULL) ORDER BY material;';
    ELSE
        RAISE NOTICE 'All utility_structures.material values conform to material_standards.material_code';
    END IF;
END $$;

-- Step 6: Add FK constraint to utility_lines.material
-- NOTE: This will fail if there are non-conforming values
-- If it fails, you need to either:
-- 1. Add the missing materials to material_standards, or
-- 2. Update the non-conforming values in utility_lines
ALTER TABLE utility_lines
DROP CONSTRAINT IF EXISTS fk_utility_lines_material;

ALTER TABLE utility_lines
ADD CONSTRAINT fk_utility_lines_material
FOREIGN KEY (material) REFERENCES material_standards(material_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Step 7: Add FK constraint to utility_structures.material
ALTER TABLE utility_structures
DROP CONSTRAINT IF EXISTS fk_utility_structures_material;

ALTER TABLE utility_structures
ADD CONSTRAINT fk_utility_structures_material
FOREIGN KEY (material) REFERENCES material_standards(material_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Step 8: Add comment to document the constraints
COMMENT ON COLUMN utility_lines.material IS 'Material type code - must match material_standards.material_code';
COMMENT ON COLUMN utility_structures.material IS 'Material type code - must match material_standards.material_code';
COMMENT ON COLUMN material_standards.material_code IS 'Short material code (e.g., PVC, CONCRETE, STEEL) - referenced by utility tables';

-- Step 9: Verify constraints were added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_utility_lines_material'
    ) THEN
        RAISE NOTICE 'SUCCESS: FK constraint fk_utility_lines_material added';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_utility_structures_material'
    ) THEN
        RAISE NOTICE 'SUCCESS: FK constraint fk_utility_structures_material added';
    END IF;
END $$;

-- Migration complete
