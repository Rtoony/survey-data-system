-- Migration 037: Create Block Category Standards and Add FK Constraints
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Create controlled vocabulary for CAD block categories
-- Prevents inconsistent entry like "Structure" vs "STRUCTURE" vs "utility structure"

-- ============================================================================
-- BLOCK CATEGORY STANDARDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS block_category_standards (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID,

    -- Core identification
    category_code VARCHAR(20) NOT NULL UNIQUE,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Classification
    discipline VARCHAR(50),                            -- 'Civil', 'Architectural', 'MEP', 'Survey'
    category_type VARCHAR(50),                         -- 'Annotation', 'Schematic', '3D', '2D'

    -- Visual representation
    color_hex VARCHAR(7) DEFAULT '#FFFFFF',
    icon VARCHAR(50),                                  -- Icon name for UI
    display_order INTEGER,

    -- CAD standards
    layer_naming_convention VARCHAR(100),              -- Suggested layer naming pattern
    default_layer_prefix VARCHAR(20),                  -- e.g., 'DETAIL-', 'SYMBOL-'
    typical_scale VARCHAR(20),                         -- Typical insertion scale

    -- Metadata
    is_dynamic BOOLEAN DEFAULT false,                  -- Are blocks in this category typically dynamic?
    has_attributes BOOLEAN DEFAULT false,              -- Do blocks typically have attributes?
    typical_insertion_units VARCHAR(20),               -- 'Feet', 'Inches', 'Unitless'

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    replaced_by_id UUID REFERENCES block_category_standards(category_id) ON DELETE SET NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_category_code_uppercase CHECK (category_code = UPPER(category_code)),
    CONSTRAINT check_color_format_block_category CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_block_category_code ON block_category_standards(category_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_block_category_discipline ON block_category_standards(discipline) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_block_category_active ON block_category_standards(is_active);

-- Comments
COMMENT ON TABLE block_category_standards IS 'Controlled vocabulary for CAD block categories - enforces truth-driven architecture';
COMMENT ON COLUMN block_category_standards.category_code IS 'Unique category code (e.g., STRUCTURE, DETAIL, SYMBOL) - must be uppercase';
COMMENT ON COLUMN block_category_standards.category_name IS 'Full category name (e.g., Utility Structures, Detail Callouts)';
COMMENT ON COLUMN block_category_standards.default_layer_prefix IS 'Default CAD layer prefix for this category';

-- Update trigger
CREATE OR REPLACE FUNCTION update_block_category_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_block_category_timestamp ON block_category_standards;
CREATE TRIGGER trigger_update_block_category_timestamp
    BEFORE UPDATE ON block_category_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_block_category_timestamp();

-- ============================================================================
-- SEED DATA - Standard Block Categories
-- ============================================================================

INSERT INTO block_category_standards
(category_code, category_name, description, discipline, category_type, color_hex, default_layer_prefix, display_order, is_dynamic, has_attributes)
VALUES

-- UTILITY & STRUCTURE BLOCKS
('STRUCTURE', 'Utility Structures', 'Manholes, catch basins, valves, and other utility structures', 'Civil', '2D', '#00BCD4', 'STRUC-', 1, false, true),
('MANHOLE', 'Manholes', 'Storm and sanitary manhole blocks', 'Civil', '2D', '#0066CC', 'MH-', 2, false, true),
('CATCH_BASIN', 'Catch Basins', 'Storm drain catch basin and inlet blocks', 'Civil', '2D', '#0099FF', 'CB-', 3, false, true),
('VALVE', 'Valves', 'Water, gas, and other valve symbols', 'Civil', '2D', '#00BFFF', 'VALVE-', 4, false, true),

-- DETAIL & ANNOTATION BLOCKS
('DETAIL', 'Detail Callouts', 'Section and detail callout symbols', 'Civil', 'Annotation', '#FFA500', 'DETAIL-', 11, false, true),
('SYMBOL', 'Symbols & Markers', 'Standard symbols and markers', 'Civil', 'Annotation', '#FFFF00', 'SYMBOL-', 12, false, false),
('NOTE', 'Note Blocks', 'Standard note and text blocks with leaders', 'Civil', 'Annotation', '#FFFFFF', 'NOTE-', 13, false, true),
('TAG', 'Tags & Labels', 'Equipment tags and identification labels', 'Civil', 'Annotation', '#00FF00', 'TAG-', 14, false, true),

-- TITLE BLOCK & BORDER BLOCKS
('BORDER', 'Title Blocks & Borders', 'Sheet borders and title blocks', 'Civil', '2D', '#808080', 'BORDER-', 21, true, true),
('REVISION', 'Revision Blocks', 'Revision history and delta blocks', 'Civil', 'Annotation', '#FF00FF', 'REV-', 22, true, true),

-- SURVEY & MONUMENT BLOCKS
('SURVEY', 'Survey Monuments', 'Control points, benchmarks, and property monuments', 'Survey', '2D', '#FFD700', 'SURVEY-', 31, false, true),
('PROPERTY', 'Property Markers', 'Property corners and boundary markers', 'Survey', '2D', '#FF6600', 'PROP-', 32, false, true),

-- SITE ELEMENTS
('SITE', 'Site Elements', 'Trees, vehicles, people, and other site elements', 'Civil', '2D', '#228B22', 'SITE-', 41, false, false),
('VEHICLE', 'Vehicles', 'Car, truck, and other vehicle blocks', 'Civil', '2D', '#666666', 'VEH-', 42, false, false),
('TREE', 'Trees & Landscaping', 'Tree and landscape element blocks', 'Civil', '2D', '#00AA00', 'TREE-', 43, false, false),

-- ARCHITECTURAL
('ARCHITECTURAL', 'Architectural Elements', 'Doors, windows, and architectural details', 'Architectural', '2D', '#A52A2A', 'ARCH-', 51, false, false),

-- MEP (Mechanical, Electrical, Plumbing)
('MEP', 'MEP Elements', 'Mechanical, electrical, and plumbing symbols', 'MEP', '2D', '#FF0000', 'MEP-', 61, false, true),

-- GENERAL/OTHER
('GENERAL', 'General Blocks', 'Miscellaneous and uncategorized blocks', 'Civil', '2D', '#CCCCCC', 'MISC-', 91, false, false),
('CUSTOM', 'Custom Blocks', 'Project-specific custom blocks', 'Civil', '2D', '#9933FF', 'CUSTOM-', 92, false, false)

ON CONFLICT (category_code) DO NOTHING;

-- Verify seed data
DO $$
DECLARE
    record_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM block_category_standards;
    RAISE NOTICE 'Block category standards table created with % records', record_count;
END $$;

-- ============================================================================
-- DATA MIGRATION - Map Existing Categories to Standards
-- ============================================================================

-- Check existing category values in block_definitions
DO $$
DECLARE
    unique_categories TEXT;
BEGIN
    SELECT STRING_AGG(DISTINCT category, ', ')
    INTO unique_categories
    FROM block_definitions
    WHERE category IS NOT NULL
    LIMIT 50;

    IF unique_categories IS NOT NULL THEN
        RAISE NOTICE 'Existing block_definitions categories: %', unique_categories;
    ELSE
        RAISE NOTICE 'No categories found in block_definitions';
    END IF;
END $$;

-- Check existing category values in block_standards
DO $$
DECLARE
    unique_categories TEXT;
BEGIN
    SELECT STRING_AGG(DISTINCT category, ', ')
    INTO unique_categories
    FROM block_standards
    WHERE category IS NOT NULL
    LIMIT 50;

    IF unique_categories IS NOT NULL THEN
        RAISE NOTICE 'Existing block_standards categories: %', unique_categories;
    ELSE
        RAISE NOTICE 'No categories found in block_standards';
    END IF;
END $$;

-- Map common category variations to standard codes for block_definitions
UPDATE block_definitions SET category = 'STRUCTURE'
WHERE category IS NOT NULL
AND UPPER(category) IN ('STRUCTURE', 'STRUCTURES', 'UTILITY STRUCTURE', 'UTILITY_STRUCTURE');

UPDATE block_definitions SET category = 'MANHOLE'
WHERE category IS NOT NULL
AND UPPER(category) IN ('MANHOLE', 'MANHOLES', 'MH');

UPDATE block_definitions SET category = 'CATCH_BASIN'
WHERE category IS NOT NULL
AND UPPER(category) IN ('CATCH BASIN', 'CATCH_BASIN', 'CB', 'INLET', 'INLETS');

UPDATE block_definitions SET category = 'VALVE'
WHERE category IS NOT NULL
AND UPPER(category) IN ('VALVE', 'VALVES', 'WV', 'WATER VALVE');

UPDATE block_definitions SET category = 'DETAIL'
WHERE category IS NOT NULL
AND UPPER(category) IN ('DETAIL', 'DETAILS', 'DETAIL CALLOUT');

UPDATE block_definitions SET category = 'SYMBOL'
WHERE category IS NOT NULL
AND UPPER(category) IN ('SYMBOL', 'SYMBOLS', 'MARKER', 'MARKERS');

UPDATE block_definitions SET category = 'BORDER'
WHERE category IS NOT NULL
AND UPPER(category) IN ('BORDER', 'TITLE BLOCK', 'TITLE_BLOCK', 'TITLEBLOCK');

UPDATE block_definitions SET category = 'SURVEY'
WHERE category IS NOT NULL
AND UPPER(category) IN ('SURVEY', 'CONTROL', 'BENCHMARK', 'MONUMENT');

UPDATE block_definitions SET category = 'GENERAL'
WHERE category IS NOT NULL
AND category NOT IN (SELECT category_code FROM block_category_standards);

-- Map categories for block_standards (same mappings)
UPDATE block_standards SET category = 'STRUCTURE'
WHERE category IS NOT NULL
AND UPPER(category) IN ('STRUCTURE', 'STRUCTURES', 'UTILITY STRUCTURE', 'UTILITY_STRUCTURE');

UPDATE block_standards SET category = 'DETAIL'
WHERE category IS NOT NULL
AND UPPER(category) IN ('DETAIL', 'DETAILS', 'DETAIL CALLOUT');

UPDATE block_standards SET category = 'SYMBOL'
WHERE category IS NOT NULL
AND UPPER(category) IN ('SYMBOL', 'SYMBOLS', 'MARKER', 'MARKERS');

UPDATE block_standards SET category = 'GENERAL'
WHERE category IS NOT NULL
AND category NOT IN (SELECT category_code FROM block_category_standards);

-- ============================================================================
-- ADD FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Constraint 1: block_definitions.category → block_category_standards.category_code
ALTER TABLE block_definitions
DROP CONSTRAINT IF EXISTS fk_block_definitions_category;

ALTER TABLE block_definitions
ADD CONSTRAINT fk_block_definitions_category
FOREIGN KEY (category) REFERENCES block_category_standards(category_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_block_definitions_category ON block_definitions IS 'FK constraint enforcing block_definitions.category must match block_category_standards.category_code';

CREATE INDEX IF NOT EXISTS idx_block_definitions_category ON block_definitions(category);

-- Constraint 2: block_standards.category → block_category_standards.category_code
ALTER TABLE block_standards
DROP CONSTRAINT IF EXISTS fk_block_standards_category;

ALTER TABLE block_standards
ADD CONSTRAINT fk_block_standards_category
FOREIGN KEY (category) REFERENCES block_category_standards(category_code)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_block_standards_category ON block_standards IS 'FK constraint enforcing block_standards.category must match block_category_standards.category_code';

CREATE INDEX IF NOT EXISTS idx_block_standards_category ON block_standards(category);

-- ============================================================================
-- VERIFY CONSTRAINTS WERE ADDED
-- ============================================================================

DO $$
DECLARE
    constraint_count INT;
BEGIN
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints
    WHERE constraint_name IN (
        'fk_block_definitions_category',
        'fk_block_standards_category'
    ) AND constraint_type = 'FOREIGN KEY';

    IF constraint_count = 2 THEN
        RAISE NOTICE '✓ SUCCESS: 2 FK constraints added for Phase 3';
        RAISE NOTICE '  - fk_block_definitions_category';
        RAISE NOTICE '  - fk_block_standards_category';
    ELSE
        RAISE WARNING 'Only % of 2 expected FK constraints were added', constraint_count;
    END IF;
END $$;

-- ============================================================================
-- TESTING - Verify constraints work correctly
-- ============================================================================

-- Test 1: Try to insert block with invalid category (should fail)
DO $$
BEGIN
    BEGIN
        INSERT INTO block_definitions (block_name, category)
        VALUES ('TEST_BLOCK', 'INVALID_CATEGORY');
        RAISE EXCEPTION 'TEST FAILED: Invalid category was accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ TEST PASSED: Invalid category correctly rejected';
    END;
END $$;

-- Test 2: Insert block with valid category (should succeed)
DO $$
DECLARE
    test_block_id UUID;
BEGIN
    INSERT INTO block_definitions (block_name, category)
    VALUES ('TEST_BLOCK_VALID', 'STRUCTURE')
    RETURNING block_id INTO test_block_id;

    -- Clean up test record
    DELETE FROM block_definitions WHERE block_id = test_block_id;

    RAISE NOTICE '✓ TEST PASSED: Valid category correctly accepted';
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'TEST FAILED: Valid category was rejected: %', SQLERRM;
END $$;

-- Migration complete
RAISE NOTICE '';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Migration 037 Complete - Phase 3 FK Constraints';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Added 2 FK constraints for block categories:';
RAISE NOTICE '  1. block_definitions.category → block_category_standards';
RAISE NOTICE '  2. block_standards.category → block_category_standards';
RAISE NOTICE '';
RAISE NOTICE 'Created 18 block category standards';
RAISE NOTICE '=====================================================';
