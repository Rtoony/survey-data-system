-- ============================================================================
-- Migration: Update survey_points to use survey standards FKs
-- Part of Truth-Driven Architecture enforcement
-- ============================================================================
-- IMPORTANT: Run create_survey_standards.sql FIRST
-- IMPORTANT: Run seed_survey_standards.sql SECOND
-- Then run this migration
-- ============================================================================

-- Step 1: Add new columns for FKs to survey standards
ALTER TABLE survey_points
ADD COLUMN IF NOT EXISTS point_description_id UUID
REFERENCES survey_point_description_standards(description_id) ON DELETE SET NULL;

ALTER TABLE survey_points
ADD COLUMN IF NOT EXISTS survey_method_id UUID
REFERENCES survey_method_types(method_id) ON DELETE SET NULL;

-- Step 2: Create mapping functions

-- Map point description text to standards
CREATE OR REPLACE FUNCTION map_point_description_to_standard(old_desc TEXT)
RETURNS UUID AS $$
DECLARE
    mapped_id UUID;
BEGIN
    IF old_desc IS NULL OR TRIM(old_desc) = '' THEN
        RETURN NULL;
    END IF;

    -- Normalize input (uppercase, trim whitespace)
    old_desc := UPPER(TRIM(old_desc));

    -- Try exact code or text match first
    SELECT description_id INTO mapped_id
    FROM survey_point_description_standards
    WHERE is_active = true
      AND (
        description_code = old_desc
        OR UPPER(description_text) = old_desc
      )
    LIMIT 1;

    -- If no exact match, try fuzzy matching
    IF mapped_id IS NULL THEN
        SELECT description_id INTO mapped_id
        FROM survey_point_description_standards
        WHERE is_active = true
          AND (
            old_desc LIKE '%' || description_code || '%'
            OR old_desc LIKE '%EDGE%' AND old_desc LIKE '%PAVEMENT%' AND description_code = 'EP'
            OR old_desc LIKE '%EDGE%' AND old_desc LIKE '%PAVE%' AND description_code = 'EP'
            OR old_desc LIKE '%CENTER%' AND description_code = 'CL'
            OR old_desc LIKE '%TOP%' AND old_desc LIKE '%WALL%' AND description_code = 'TW'
            OR old_desc LIKE '%BOTTOM%' AND old_desc LIKE '%WALL%' AND description_code = 'BW'
            OR old_desc LIKE '%FACE%' AND old_desc LIKE '%CURB%' AND description_code = 'FG'
            OR old_desc LIKE '%BACK%' AND old_desc LIKE '%CURB%' AND description_code = 'BC'
            OR old_desc LIKE '%FLOW%' AND description_code = 'FL'
            OR old_desc LIKE '%CATCH%' AND description_code = 'CB'
            OR old_desc LIKE '%MANHOLE%' AND description_code = 'MH'
            OR old_desc LIKE '%HYDRANT%' AND description_code = 'HYDRANT'
            OR old_desc LIKE '%TREE%' AND description_code = 'TREE'
            OR old_desc LIKE '%BENCH%' AND description_code = 'BENCHMARK'
            OR old_desc LIKE '%CONTROL%' AND description_code = 'CONTROL'
            OR old_desc LIKE '%MONUMENT%' AND description_code = 'MONUMENT'
            OR old_desc LIKE '%TOPO%' AND description_code = 'TOPO'
          )
        LIMIT 1;
    END IF;

    RETURN mapped_id;
END;
$$ LANGUAGE plpgsql;

-- Map survey method text to standards
CREATE OR REPLACE FUNCTION map_survey_method_to_standard(old_method TEXT)
RETURNS UUID AS $$
DECLARE
    mapped_id UUID;
BEGIN
    IF old_method IS NULL OR TRIM(old_method) = '' THEN
        RETURN NULL;
    END IF;

    -- Normalize input (uppercase, trim whitespace)
    old_method := UPPER(TRIM(old_method));

    -- Try exact code or name match first
    SELECT method_id INTO mapped_id
    FROM survey_method_types
    WHERE is_active = true
      AND (
        method_code = old_method
        OR UPPER(method_name) = old_method
      )
    LIMIT 1;

    -- If no exact match, try fuzzy matching
    IF mapped_id IS NULL THEN
        SELECT method_id INTO mapped_id
        FROM survey_method_types
        WHERE is_active = true
          AND (
            old_method LIKE '%RTK%' AND old_method LIKE '%GPS%' AND method_code = 'RTK-GPS'
            OR old_method LIKE '%RTK%' AND method_code = 'RTK-GPS'
            OR old_method LIKE '%PPK%' AND method_code = 'PPK-GPS'
            OR old_method LIKE '%STATIC%' AND method_code = 'GPS-STATIC'
            OR old_method LIKE '%TOTAL%' AND old_method LIKE '%STATION%' AND method_code = 'TS-MANUAL'
            OR old_method LIKE '%ROBOTIC%' AND method_code = 'TS-ROBOTIC'
            OR old_method LIKE '%LEVEL%' AND old_method LIKE '%DIGI%' AND method_code = 'LEVEL-DIGI'
            OR old_method LIKE '%LEVEL%' AND method_code = 'LEVEL-AUTO'
            OR old_method LIKE '%DRONE%' AND old_method LIKE '%RTK%' AND method_code = 'DRONE-RTK'
            OR old_method LIKE '%DRONE%' AND method_code = 'DRONE-PPK'
            OR old_method LIKE '%UAV%' AND method_code = 'DRONE-PPK'
            OR old_method LIKE '%SCANNER%' AND method_code = 'SCANNER-3D'
            OR old_method LIKE '%LASER%' AND old_method LIKE '%SCAN%' AND method_code = 'SCANNER-3D'
            OR old_method LIKE '%GPS%' AND NOT old_method LIKE '%RTK%' AND method_code = 'GPS-NAV'
            OR old_method LIKE '%GNSS%' AND method_code = 'RTK-GPS'
          )
        LIMIT 1;
    END IF;

    RETURN mapped_id;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Migrate existing data
-- Update point_description_id based on existing point_description text values
UPDATE survey_points
SET point_description_id = map_point_description_to_standard(point_description)
WHERE point_description IS NOT NULL
  AND point_description_id IS NULL;

-- Update survey_method_id based on existing survey_method text values
UPDATE survey_points
SET survey_method_id = map_survey_method_to_standard(survey_method)
WHERE survey_method IS NOT NULL
  AND survey_method_id IS NULL;

-- Step 4: Report on unmapped points
DO $$
DECLARE
    unmapped_desc_count INTEGER;
    unmapped_method_count INTEGER;
    unmapped_descs TEXT;
    unmapped_methods TEXT;
BEGIN
    -- Check descriptions
    SELECT COUNT(DISTINCT point_description), STRING_AGG(DISTINCT point_description, ', ')
    INTO unmapped_desc_count, unmapped_descs
    FROM survey_points
    WHERE point_description IS NOT NULL
      AND point_description_id IS NULL;

    -- Check methods
    SELECT COUNT(DISTINCT survey_method), STRING_AGG(DISTINCT survey_method, ', ')
    INTO unmapped_method_count, unmapped_methods
    FROM survey_points
    WHERE survey_method IS NOT NULL
      AND survey_method_id IS NULL;

    IF unmapped_desc_count > 0 THEN
        RAISE NOTICE 'WARNING: % unique point descriptions could not be automatically mapped:', unmapped_desc_count;
        RAISE NOTICE 'Unmapped descriptions: %', unmapped_descs;
    ELSE
        RAISE NOTICE 'SUCCESS: All point descriptions successfully mapped!';
    END IF;

    IF unmapped_method_count > 0 THEN
        RAISE NOTICE 'WARNING: % unique survey methods could not be automatically mapped:', unmapped_method_count;
        RAISE NOTICE 'Unmapped methods: %', unmapped_methods;
    ELSE
        RAISE NOTICE 'SUCCESS: All survey methods successfully mapped!';
    END IF;
END $$;

-- Step 5: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_survey_points_description_id
ON survey_points(point_description_id);

CREATE INDEX IF NOT EXISTS idx_survey_points_method_id
ON survey_points(survey_method_id);

-- Step 6: Add comments
COMMENT ON COLUMN survey_points.point_description_id IS 'FK to survey_point_description_standards - enforces truth-driven architecture (replaces free-text point_description)';
COMMENT ON COLUMN survey_points.survey_method_id IS 'FK to survey_method_types - enforces truth-driven architecture (replaces free-text survey_method)';

-- Step 7: (OPTIONAL - uncomment after verifying migration)
-- Drop old text columns after confirming all data is migrated
-- IMPORTANT: Only run this after verifying all points are mapped!

-- ALTER TABLE survey_points DROP COLUMN point_description;
-- ALTER TABLE survey_points DROP COLUMN survey_method;

-- Cleanup
DROP FUNCTION IF EXISTS map_point_description_to_standard(TEXT);
DROP FUNCTION IF EXISTS map_survey_method_to_standard(TEXT);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these queries to verify the migration:

-- 1. Check description mapping coverage
-- SELECT
--     COUNT(*) as total_points,
--     COUNT(point_description_id) as mapped_descriptions,
--     COUNT(*) - COUNT(point_description_id) as unmapped_descriptions,
--     ROUND(100.0 * COUNT(point_description_id) / NULLIF(COUNT(*), 0), 2) as mapping_percentage
-- FROM survey_points
-- WHERE point_description IS NOT NULL;

-- 2. Check method mapping coverage
-- SELECT
--     COUNT(*) as total_points,
--     COUNT(survey_method_id) as mapped_methods,
--     COUNT(*) - COUNT(survey_method_id) as unmapped_methods,
--     ROUND(100.0 * COUNT(survey_method_id) / NULLIF(COUNT(*), 0), 2) as mapping_percentage
-- FROM survey_points
-- WHERE survey_method IS NOT NULL;

-- 3. View description distribution
-- SELECT
--     spd.description_code,
--     spd.description_text,
--     spd.category,
--     COUNT(sp.point_id) as usage_count
-- FROM survey_point_description_standards spd
-- LEFT JOIN survey_points sp ON sp.point_description_id = spd.description_id
-- GROUP BY spd.description_id, spd.description_code, spd.description_text, spd.category
-- ORDER BY usage_count DESC;

-- 4. View method distribution
-- SELECT
--     sm.method_code,
--     sm.method_name,
--     sm.category,
--     COUNT(sp.point_id) as usage_count
-- FROM survey_method_types sm
-- LEFT JOIN survey_points sp ON sp.survey_method_id = sm.method_id
-- GROUP BY sm.method_id, sm.method_code, sm.method_name, sm.category
-- ORDER BY usage_count DESC;
