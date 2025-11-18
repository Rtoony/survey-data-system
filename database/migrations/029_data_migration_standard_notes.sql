-- Data Migration for Migration 029: Map standard_notes VARCHAR to FK IDs
-- This must run BEFORE adding FK constraints

-- Step 1: Add the new FK columns (already in 029_add_standard_notes_fk_constraints.sql)
-- We're just doing the data migration here

-- Step 2: Map note_category VARCHAR to category_id INT
-- Mapping logic:
-- "Utilities" -> category_codes where code='UTIL' and discipline_id=1
-- "Grading" -> category_codes where code='GRAD' and discipline_id=1
-- "General" -> category_codes where code='UTIL' (treating as general utility)

UPDATE standard_notes sn
SET category_id = cc.category_id
FROM category_codes cc
WHERE sn.note_category = 'Utilities'
  AND cc.code = 'UTIL'
  AND cc.discipline_id = 1;

UPDATE standard_notes sn
SET category_id = cc.category_id
FROM category_codes cc
WHERE sn.note_category = 'Grading'
  AND cc.code = 'GRAD'
  AND cc.discipline_id = 1;

-- Map "General" to UTIL for now (could also add a new category if needed)
UPDATE standard_notes sn
SET category_id = cc.category_id
FROM category_codes cc
WHERE sn.note_category = 'General'
  AND cc.code = 'UTIL'
  AND cc.discipline_id = 1;

-- Step 3: Map discipline VARCHAR to discipline_id INT
-- "CIV" -> discipline_codes where code='CIV'
-- "SITE" -> discipline_codes where code='SITE'
-- "UTIL" -> discipline_codes where code='UTIL'

UPDATE standard_notes sn
SET discipline_id = dc.discipline_id
FROM discipline_codes dc
WHERE sn.discipline = 'CIV'
  AND dc.code = 'CIV';

UPDATE standard_notes sn
SET discipline_id = dc.discipline_id
FROM discipline_codes dc
WHERE sn.discipline = 'SITE'
  AND dc.code = 'SITE';

UPDATE standard_notes sn
SET discipline_id = dc.discipline_id
FROM discipline_codes dc
WHERE sn.discipline = 'UTIL'
  AND dc.code = 'UTIL';

-- Step 4: Verify the migration
SELECT 
    'Unmapped note_category values' as check_type,
    COUNT(*) as count
FROM standard_notes
WHERE note_category IS NOT NULL 
  AND category_id IS NULL

UNION ALL

SELECT 
    'Unmapped discipline values' as check_type,
    COUNT(*) as count
FROM standard_notes
WHERE discipline IS NOT NULL 
  AND discipline_id IS NULL;

-- Step 5: Summary
SELECT 
    'Total records' as metric,
    COUNT(*) as count
FROM standard_notes

UNION ALL

SELECT 
    'Records with category_id' as metric,
    COUNT(*) as count
FROM standard_notes
WHERE category_id IS NOT NULL

UNION ALL

SELECT 
    'Records with discipline_id' as metric,
    COUNT(*) as count
FROM standard_notes
WHERE discipline_id IS NOT NULL;
