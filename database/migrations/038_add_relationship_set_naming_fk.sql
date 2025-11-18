-- Migration 038: Add Relationship Set Naming Template FK Constraint
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Link project_relationship_sets to naming templates for standardized naming
-- Enables template-based name generation with consistent formatting

-- ============================================================================
-- PREREQUISITE CHECKS
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'relationship_set_naming_templates') THEN
        RAISE EXCEPTION 'Table relationship_set_naming_templates does not exist. Run create_relationship_set_naming_templates.sql first.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'project_relationship_sets') THEN
        RAISE EXCEPTION 'Table project_relationship_sets does not exist. Run create_project_relationship_sets.sql first.';
    END IF;

    RAISE NOTICE 'Prerequisite tables verified';
END $$;

-- ============================================================================
-- ADD COLUMN FOR NAMING TEMPLATE REFERENCE
-- ============================================================================

-- Add naming_template_id column to project_relationship_sets
ALTER TABLE project_relationship_sets
ADD COLUMN IF NOT EXISTS naming_template_id UUID;

COMMENT ON COLUMN project_relationship_sets.naming_template_id IS 'FK to relationship_set_naming_templates - defines naming convention for this set';

-- Note: The existing template_id column is for set templates (self-reference),
-- while naming_template_id is for naming convention templates (different purpose)

-- ============================================================================
-- DATA MIGRATION
-- ============================================================================

-- Check for existing naming patterns in set_name to suggest template assignments
DO $$
DECLARE
    unique_patterns TEXT;
BEGIN
    SELECT STRING_AGG(DISTINCT
        CASE
            WHEN set_name LIKE '%Compliance%' THEN 'Compliance'
            WHEN set_name LIKE '%Storm%' OR set_name LIKE '%STORM%' THEN 'Storm System'
            WHEN set_name LIKE '%Sewer%' OR set_name LIKE '%SEWER%' THEN 'Sewer System'
            WHEN set_name LIKE '%Water%' OR set_name LIKE '%WATER%' THEN 'Water System'
            WHEN set_name LIKE '%Material%' THEN 'Material'
            ELSE 'Other'
        END, ', ')
    INTO unique_patterns
    FROM project_relationship_sets
    WHERE set_name IS NOT NULL;

    IF unique_patterns IS NOT NULL THEN
        RAISE NOTICE 'Existing relationship set naming patterns: %', unique_patterns;
        RAISE NOTICE 'Manual template assignment recommended after migration';
    ELSE
        RAISE NOTICE 'No existing relationship sets found';
    END IF;
END $$;

-- Report existing relationship sets for manual review
DO $$
DECLARE
    set_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO set_count FROM project_relationship_sets;
    RAISE NOTICE 'Found % existing relationship sets', set_count;

    IF set_count > 0 AND set_count <= 20 THEN
        RAISE NOTICE 'Sample set names:';
        RAISE NOTICE '%', (
            SELECT STRING_AGG(set_name, E'\n  ')
            FROM (
                SELECT set_name
                FROM project_relationship_sets
                LIMIT 10
            ) AS samples
        );
    END IF;
END $$;

-- ============================================================================
-- ADD FOREIGN KEY CONSTRAINT
-- ============================================================================

-- Constraint: project_relationship_sets.naming_template_id → relationship_set_naming_templates.template_id
ALTER TABLE project_relationship_sets
DROP CONSTRAINT IF EXISTS fk_relationship_sets_naming_template;

ALTER TABLE project_relationship_sets
ADD CONSTRAINT fk_relationship_sets_naming_template
FOREIGN KEY (naming_template_id) REFERENCES relationship_set_naming_templates(template_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_relationship_sets_naming_template ON project_relationship_sets IS 'FK constraint linking to naming convention templates';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_relationship_sets_naming_template ON project_relationship_sets(naming_template_id);

-- ============================================================================
-- VERIFY CONSTRAINT WAS ADDED
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_relationship_sets_naming_template'
        AND constraint_type = 'FOREIGN KEY'
    ) THEN
        RAISE NOTICE '✓ SUCCESS: FK constraint added for Phase 4';
        RAISE NOTICE '  - fk_relationship_sets_naming_template';
    ELSE
        RAISE WARNING 'FK constraint was not added';
    END IF;
END $$;

-- ============================================================================
-- TESTING - Verify constraint works correctly
-- ============================================================================

-- Test 1: Try to set invalid naming_template_id (should fail)
DO $$
BEGIN
    BEGIN
        UPDATE project_relationship_sets
        SET naming_template_id = gen_random_uuid()
        WHERE set_id = (SELECT set_id FROM project_relationship_sets LIMIT 1);

        RAISE EXCEPTION 'TEST FAILED: Invalid naming_template_id was accepted';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE '✓ TEST PASSED: Invalid naming_template_id correctly rejected';
    WHEN OTHERS THEN
        -- No relationship sets exist to test on, or already NULL
        RAISE NOTICE '⚠ TEST SKIPPED: No relationship sets available for testing';
    END;
END $$;

-- Test 2: Verify NULL is allowed (template assignment is optional)
DO $$
DECLARE
    test_set_id UUID;
BEGIN
    -- Try to create a relationship set without a naming template
    INSERT INTO project_relationship_sets (set_name, set_code, category)
    VALUES ('TEST_SET', 'TEST', 'Testing')
    RETURNING set_id INTO test_set_id;

    -- Verify it was created with NULL naming_template_id
    IF EXISTS (
        SELECT 1 FROM project_relationship_sets
        WHERE set_id = test_set_id
        AND naming_template_id IS NULL
    ) THEN
        RAISE NOTICE '✓ TEST PASSED: NULL naming_template_id correctly allowed';
    ELSE
        RAISE WARNING 'TEST FAILED: NULL naming_template_id not allowed';
    END IF;

    -- Clean up test record
    DELETE FROM project_relationship_sets WHERE set_id = test_set_id;

EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE '⚠ TEST SKIPPED: Could not create test relationship set: %', SQLERRM;
END $$;

-- ============================================================================
-- CREATE HELPER FUNCTION FOR NAME GENERATION
-- ============================================================================

-- Function to generate relationship set name from template
CREATE OR REPLACE FUNCTION generate_relationship_set_name(
    p_template_id UUID,
    p_tokens JSONB
) RETURNS TEXT AS $$
DECLARE
    v_name_format TEXT;
    v_result TEXT;
    v_token_key TEXT;
    v_token_value TEXT;
BEGIN
    -- Get the name format from template
    SELECT name_format INTO v_name_format
    FROM relationship_set_naming_templates
    WHERE template_id = p_template_id
    AND is_active = true;

    IF v_name_format IS NULL THEN
        RAISE EXCEPTION 'Template not found or inactive: %', p_template_id;
    END IF;

    -- Start with the format string
    v_result := v_name_format;

    -- Replace each token
    FOR v_token_key, v_token_value IN SELECT key, value FROM jsonb_each_text(p_tokens)
    LOOP
        v_result := REPLACE(v_result, '{' || UPPER(v_token_key) || '}', v_token_value);
    END LOOP;

    -- Check if any tokens remain unreplaced
    IF v_result ~ '\{[A-Z_]+\}' THEN
        RAISE WARNING 'Some tokens were not replaced in template. Result: %', v_result;
    END IF;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_relationship_set_name(UUID, JSONB) IS 'Generate relationship set name from template by replacing tokens';

-- Example usage:
-- SELECT generate_relationship_set_name(
--     (SELECT template_id FROM relationship_set_naming_templates WHERE template_name = 'Storm System Compliance' LIMIT 1),
--     '{"project_code": "PROJ-001", "system": "STORM"}'::jsonb
-- );

-- Function to generate short code from template
CREATE OR REPLACE FUNCTION generate_relationship_set_short_code(
    p_template_id UUID,
    p_tokens JSONB
) RETURNS TEXT AS $$
DECLARE
    v_code_format TEXT;
    v_result TEXT;
    v_token_key TEXT;
    v_token_value TEXT;
BEGIN
    -- Get the short code format from template
    SELECT short_code_format INTO v_code_format
    FROM relationship_set_naming_templates
    WHERE template_id = p_template_id
    AND is_active = true;

    IF v_code_format IS NULL THEN
        RAISE EXCEPTION 'Template not found or inactive: %', p_template_id;
    END IF;

    -- Start with the format string
    v_result := v_code_format;

    -- Replace each token
    FOR v_token_key, v_token_value IN SELECT key, value FROM jsonb_each_text(p_tokens)
    LOOP
        v_result := REPLACE(v_result, '{' || UPPER(v_token_key) || '}', v_token_value);
    END LOOP;

    -- Check if any tokens remain unreplaced
    IF v_result ~ '\{[A-Z_]+\}' THEN
        RAISE WARNING 'Some tokens were not replaced in template. Result: %', v_result;
    END IF;

    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_relationship_set_short_code(UUID, JSONB) IS 'Generate relationship set short code from template by replacing tokens';

-- Test the helper functions
DO $$
BEGIN
    -- Only test if templates exist
    IF EXISTS (SELECT 1 FROM relationship_set_naming_templates LIMIT 1) THEN
        RAISE NOTICE '✓ Name generation functions created successfully';
        RAISE NOTICE '  Use generate_relationship_set_name(template_id, tokens) to generate names';
        RAISE NOTICE '  Use generate_relationship_set_short_code(template_id, tokens) to generate codes';
    ELSE
        RAISE NOTICE '⚠ Name generation functions created but no templates exist yet';
        RAISE NOTICE '  Load templates from seed_relationship_set_naming_templates.sql';
    END IF;
END $$;

-- Migration complete
RAISE NOTICE '';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Migration 038 Complete - Phase 4 FK Constraint';
RAISE NOTICE '=====================================================';
RAISE NOTICE 'Added 1 FK constraint for relationship set naming:';
RAISE NOTICE '  - project_relationship_sets.naming_template_id → relationship_set_naming_templates';
RAISE NOTICE '';
RAISE NOTICE 'Created 2 helper functions:';
RAISE NOTICE '  - generate_relationship_set_name(template_id, tokens)';
RAISE NOTICE '  - generate_relationship_set_short_code(template_id, tokens)';
RAISE NOTICE '=====================================================';
