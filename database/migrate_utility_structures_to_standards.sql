-- ============================================================================
-- Migration: Update utility_structures to use structure_type_standards FK
-- Part of Truth-Driven Architecture enforcement
-- ============================================================================
-- IMPORTANT: Run create_structure_type_standards.sql FIRST
-- IMPORTANT: Run seed_structure_type_standards.sql SECOND
-- Then run this migration
-- ============================================================================

-- Step 1: Add new column for FK to structure_type_standards
ALTER TABLE utility_structures
ADD COLUMN IF NOT EXISTS structure_type_id UUID
REFERENCES structure_type_standards(type_id) ON DELETE RESTRICT;

-- Step 2: Create mapping function to migrate existing free-text values
-- This maps common variations to standardized type codes
CREATE OR REPLACE FUNCTION map_structure_type_to_standard(old_type TEXT)
RETURNS UUID AS $$
DECLARE
    mapped_id UUID;
BEGIN
    -- Normalize input (uppercase, trim whitespace)
    old_type := UPPER(TRIM(old_type));

    -- Map common variations to standard type codes
    SELECT type_id INTO mapped_id
    FROM structure_type_standards
    WHERE is_active = true
      AND (
        type_code = old_type
        OR type_name = old_type
        OR (old_type LIKE '%MANHOLE%' AND type_code = 'MH')
        OR (old_type LIKE '%MH%' AND category = 'Storm Drainage' AND type_code = 'MH')
        OR (old_type LIKE '%SMH%' AND category = 'Sanitary Sewer' AND type_code = 'SMH')
        OR (old_type LIKE '%CATCH%' AND type_code = 'CB')
        OR (old_type LIKE '%CB%' AND type_code = 'CB')
        OR (old_type LIKE '%INLET%' AND type_code = 'INLET')
        OR (old_type LIKE '%CLEANOUT%' AND type_code = 'CLNOUT')
        OR (old_type LIKE '%CLNOUT%' AND type_code = 'CLNOUT')
        OR (old_type LIKE '%JUNCTION%' AND type_code = 'JBOX')
        OR (old_type LIKE '%JBOX%' AND type_code = 'JBOX')
        OR (old_type LIKE '%VALVE%' AND old_type NOT LIKE '%AIR%' AND type_code = 'VALVE')
        OR (old_type LIKE '%AIR%' AND old_type LIKE '%VALVE%' AND type_code = 'AIR_VALVE')
        OR (old_type LIKE '%HYDRANT%' AND type_code = 'HYDRANT')
        OR (old_type LIKE '%METER%' AND type_code = 'METER')
        OR (old_type LIKE '%LIFT%' AND type_code = 'LIFTSTATION')
        OR (old_type LIKE '%PUMP%' AND type_code = 'LIFTSTATION')
        OR (old_type LIKE '%BIO%' AND type_code = 'BIORET')
        OR (old_type LIKE '%FILTER%' AND type_code = 'FILTER')
        OR (old_type LIKE '%SEPARATOR%' AND type_code = 'SEPARATOR')
        OR (old_type LIKE '%OIL%' AND type_code = 'SEPARATOR')
        OR (old_type LIKE '%VAULT%' AND type_code = 'VAULT')
        OR (old_type LIKE '%PULL%' AND type_code = 'PULLBOX')
        OR (old_type LIKE '%HAND%' AND type_code = 'HANDHOLE')
      )
    LIMIT 1;

    RETURN mapped_id;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Migrate existing data
-- Update structure_type_id based on existing structure_type text values
UPDATE utility_structures
SET structure_type_id = map_structure_type_to_standard(structure_type)
WHERE structure_type IS NOT NULL
  AND structure_type_id IS NULL;

-- Step 4: Report on unmapped structures (need manual review)
DO $$
DECLARE
    unmapped_count INTEGER;
    unmapped_types TEXT;
BEGIN
    SELECT COUNT(DISTINCT structure_type), STRING_AGG(DISTINCT structure_type, ', ')
    INTO unmapped_count, unmapped_types
    FROM utility_structures
    WHERE structure_type IS NOT NULL
      AND structure_type_id IS NULL;

    IF unmapped_count > 0 THEN
        RAISE NOTICE 'WARNING: % unique structure types could not be automatically mapped:', unmapped_count;
        RAISE NOTICE 'Unmapped types: %', unmapped_types;
        RAISE NOTICE 'These will need manual mapping or new structure_type_standards entries';
    ELSE
        RAISE NOTICE 'SUCCESS: All existing structure types successfully mapped!';
    END IF;
END $$;

-- Step 5: Create index for performance
CREATE INDEX IF NOT EXISTS idx_utility_structures_type_id
ON utility_structures(structure_type_id);

-- Step 6: Add comment
COMMENT ON COLUMN utility_structures.structure_type_id IS 'FK to structure_type_standards - enforces truth-driven architecture (replaces free-text structure_type)';

-- Step 7: (OPTIONAL - uncomment after verifying migration)
-- Make structure_type_id required and drop old structure_type column
-- IMPORTANT: Only run this after verifying all structures are mapped!

-- ALTER TABLE utility_structures
-- ALTER COLUMN structure_type_id SET NOT NULL;

-- ALTER TABLE utility_structures
-- DROP COLUMN structure_type;

-- Step 8: Create usage tracking trigger (now that FK exists)
DROP TRIGGER IF EXISTS trigger_track_structure_type_usage ON utility_structures;

CREATE TRIGGER trigger_track_structure_type_usage
    AFTER INSERT ON utility_structures
    FOR EACH ROW
    WHEN (NEW.structure_type_id IS NOT NULL)
    EXECUTE FUNCTION increment_structure_type_usage();

-- Cleanup
DROP FUNCTION IF EXISTS map_structure_type_to_standard(TEXT);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these queries to verify the migration:

-- 1. Check mapping coverage
-- SELECT
--     COUNT(*) as total_structures,
--     COUNT(structure_type_id) as mapped_structures,
--     COUNT(*) - COUNT(structure_type_id) as unmapped_structures,
--     ROUND(100.0 * COUNT(structure_type_id) / NULLIF(COUNT(*), 0), 2) as mapping_percentage
-- FROM utility_structures;

-- 2. See unmapped structures
-- SELECT DISTINCT structure_type, COUNT(*) as count
-- FROM utility_structures
-- WHERE structure_type IS NOT NULL
--   AND structure_type_id IS NULL
-- GROUP BY structure_type
-- ORDER BY count DESC;

-- 3. View mapping distribution
-- SELECT
--     sts.type_code,
--     sts.type_name,
--     sts.category,
--     COUNT(us.structure_id) as usage_count
-- FROM structure_type_standards sts
-- LEFT JOIN utility_structures us ON us.structure_type_id = sts.type_id
-- GROUP BY sts.type_id, sts.type_code, sts.type_name, sts.category
-- ORDER BY usage_count DESC;
