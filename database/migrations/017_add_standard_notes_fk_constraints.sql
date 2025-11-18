-- Migration 017: Add Standard Notes Category and Discipline FK Constraints
-- This fixes Critical Violations #2 and #3 from Truth-Driven Architecture Audit Report
-- Date: 2025-11-18
--
-- Purpose: Enforce truth-driven architecture by adding FK constraints
-- from standard_notes.category_id to category_codes.category_id
-- and standard_notes.discipline_id to discipline_codes.discipline_id
-- This eliminates free-text category/discipline entry in favor of controlled vocabulary

-- Step 1: Add category_id column to standard_notes if it doesn't exist
ALTER TABLE standard_notes
ADD COLUMN IF NOT EXISTS category_id INTEGER;

-- Step 2: Add discipline_id column to standard_notes if it doesn't exist
ALTER TABLE standard_notes
ADD COLUMN IF NOT EXISTS discipline_id INTEGER;

-- Step 3: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_standard_notes_category_id
ON standard_notes(category_id);

CREATE INDEX IF NOT EXISTS idx_standard_notes_discipline_id
ON standard_notes(discipline_id);

-- Step 4: Attempt to map existing note_category values to category_id
-- This performs fuzzy matching (case-insensitive, trimmed)
UPDATE standard_notes sn
SET category_id = (
    SELECT cc.category_id
    FROM category_codes cc
    WHERE LOWER(TRIM(sn.note_category)) = LOWER(TRIM(cc.category_code))
       OR LOWER(TRIM(sn.note_category)) = LOWER(TRIM(cc.category_name))
    LIMIT 1
)
WHERE sn.category_id IS NULL
  AND sn.note_category IS NOT NULL
  AND sn.note_category != '';

-- Step 5: Attempt to map existing discipline values to discipline_id
-- This performs fuzzy matching (case-insensitive, trimmed)
UPDATE standard_notes sn
SET discipline_id = (
    SELECT dc.discipline_id
    FROM discipline_codes dc
    WHERE LOWER(TRIM(sn.discipline)) = LOWER(TRIM(dc.discipline_code))
       OR LOWER(TRIM(sn.discipline)) = LOWER(TRIM(dc.discipline_name))
    LIMIT 1
)
WHERE sn.discipline_id IS NULL
  AND sn.discipline IS NOT NULL
  AND sn.discipline != '';

-- Step 6: Report unmapped categories that need manual review
DO $$
DECLARE
    unmapped_count INT;
BEGIN
    SELECT COUNT(DISTINCT note_category) INTO unmapped_count
    FROM standard_notes
    WHERE category_id IS NULL
      AND note_category IS NOT NULL
      AND note_category != '';

    IF unmapped_count > 0 THEN
        RAISE WARNING 'Found % distinct note_category values not mapped to category_codes', unmapped_count;
        RAISE NOTICE 'Run this query to see unmapped categories:';
        RAISE NOTICE 'SELECT DISTINCT note_category, COUNT(*) as note_count FROM standard_notes WHERE category_id IS NULL AND note_category IS NOT NULL AND note_category != '''' GROUP BY note_category ORDER BY note_count DESC;';
        RAISE NOTICE '';
        RAISE NOTICE 'To fix: Add missing categories to category_codes table via /data-manager/categories, then re-run this migration.';
    ELSE
        RAISE NOTICE 'SUCCESS: All existing note_category values successfully mapped to category_id';
    END IF;
END $$;

-- Step 7: Report unmapped disciplines that need manual review
DO $$
DECLARE
    unmapped_count INT;
BEGIN
    SELECT COUNT(DISTINCT discipline) INTO unmapped_count
    FROM standard_notes
    WHERE discipline_id IS NULL
      AND discipline IS NOT NULL
      AND discipline != '';

    IF unmapped_count > 0 THEN
        RAISE WARNING 'Found % distinct discipline values not mapped to discipline_codes', unmapped_count;
        RAISE NOTICE 'Run this query to see unmapped disciplines:';
        RAISE NOTICE 'SELECT DISTINCT discipline, COUNT(*) as note_count FROM standard_notes WHERE discipline_id IS NULL AND discipline IS NOT NULL AND discipline != '''' GROUP BY discipline ORDER BY note_count DESC;';
        RAISE NOTICE '';
        RAISE NOTICE 'To fix: Add missing disciplines to discipline_codes table via /data-manager/disciplines, then re-run this migration.';
    ELSE
        RAISE NOTICE 'SUCCESS: All existing discipline values successfully mapped to discipline_id';
    END IF;
END $$;

-- Step 8: Add FK constraint to standard_notes.category_id
-- NOTE: This allows NULL values (notes without categories are OK for now)
-- ON DELETE SET NULL: If a category is deleted, set note's category_id to NULL
-- ON UPDATE CASCADE: If category_id changes, update all note references
ALTER TABLE standard_notes
DROP CONSTRAINT IF EXISTS fk_standard_notes_category;

ALTER TABLE standard_notes
ADD CONSTRAINT fk_standard_notes_category
FOREIGN KEY (category_id) REFERENCES category_codes(category_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Step 9: Add FK constraint to standard_notes.discipline_id
ALTER TABLE standard_notes
DROP CONSTRAINT IF EXISTS fk_standard_notes_discipline;

ALTER TABLE standard_notes
ADD CONSTRAINT fk_standard_notes_discipline
FOREIGN KEY (discipline_id) REFERENCES discipline_codes(discipline_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Step 10: Add comments to document the new architecture
COMMENT ON COLUMN standard_notes.category_id IS 'Category ID - must match category_codes.category_id. Replaces free-text note_category field to enforce truth-driven architecture.';
COMMENT ON COLUMN standard_notes.discipline_id IS 'Discipline ID - must match discipline_codes.discipline_id. Replaces free-text discipline field to enforce truth-driven architecture.';
COMMENT ON COLUMN standard_notes.note_category IS 'DEPRECATED: Free-text category field. Use category_id instead. This column will be removed in a future migration after validation.';
COMMENT ON COLUMN standard_notes.discipline IS 'DEPRECATED: Free-text discipline field. Use discipline_id instead. This column will be removed in a future migration after validation.';

-- Step 11: Create a view for backward compatibility
-- This allows existing queries to continue working during migration period
CREATE OR REPLACE VIEW standard_notes_with_codes AS
SELECT
    sn.*,
    COALESCE(cc.category_code, sn.note_category) as resolved_category,
    COALESCE(cc.category_name, sn.note_category) as resolved_category_name,
    COALESCE(dc.discipline_code, sn.discipline) as resolved_discipline,
    COALESCE(dc.discipline_name, sn.discipline) as resolved_discipline_name
FROM standard_notes sn
LEFT JOIN category_codes cc ON sn.category_id = cc.category_id
LEFT JOIN discipline_codes dc ON sn.discipline_id = dc.discipline_id;

COMMENT ON VIEW standard_notes_with_codes IS 'Compatibility view that resolves category_id and discipline_id to their codes and names. Use this during migration period.';

-- Step 12: Verify constraints were added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_standard_notes_category'
          AND table_name = 'standard_notes'
    ) THEN
        RAISE NOTICE 'SUCCESS: FK constraint fk_standard_notes_category added';
    ELSE
        RAISE WARNING 'FAILED: FK constraint fk_standard_notes_category was not added';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_standard_notes_discipline'
          AND table_name = 'standard_notes'
    ) THEN
        RAISE NOTICE 'SUCCESS: FK constraint fk_standard_notes_discipline added';
    ELSE
        RAISE WARNING 'FAILED: FK constraint fk_standard_notes_discipline was not added';
    END IF;
END $$;

-- Step 13: Report statistics
DO $$
DECLARE
    total_notes INT;
    notes_with_category INT;
    notes_with_discipline INT;
    notes_without_category INT;
    notes_without_discipline INT;
BEGIN
    SELECT COUNT(*) INTO total_notes FROM standard_notes;
    SELECT COUNT(*) INTO notes_with_category FROM standard_notes WHERE category_id IS NOT NULL;
    SELECT COUNT(*) INTO notes_with_discipline FROM standard_notes WHERE discipline_id IS NOT NULL;
    SELECT COUNT(*) INTO notes_without_category FROM standard_notes WHERE category_id IS NULL;
    SELECT COUNT(*) INTO notes_without_discipline FROM standard_notes WHERE discipline_id IS NULL;

    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 017 Statistics ===';
    RAISE NOTICE 'Total standard notes: %', total_notes;
    RAISE NOTICE 'Notes with category_id: % (%%)', notes_with_category,
                 CASE WHEN total_notes > 0 THEN ROUND(notes_with_category::NUMERIC / total_notes * 100, 1) ELSE 0 END;
    RAISE NOTICE 'Notes without category_id: % (%%)', notes_without_category,
                 CASE WHEN total_notes > 0 THEN ROUND(notes_without_category::NUMERIC / total_notes * 100, 1) ELSE 0 END;
    RAISE NOTICE 'Notes with discipline_id: % (%%)', notes_with_discipline,
                 CASE WHEN total_notes > 0 THEN ROUND(notes_with_discipline::NUMERIC / total_notes * 100, 1) ELSE 0 END;
    RAISE NOTICE 'Notes without discipline_id: % (%%)', notes_without_discipline,
                 CASE WHEN total_notes > 0 THEN ROUND(notes_without_discipline::NUMERIC / total_notes * 100, 1) ELSE 0 END;
    RAISE NOTICE '================================';
END $$;

-- Migration complete
-- Next steps:
-- 1. Review unmapped categories and disciplines, add missing entries to respective tables
-- 2. Verify standard notes UI displays correctly with new dropdowns
-- 3. After validation period, run migration to drop note_category and discipline columns
