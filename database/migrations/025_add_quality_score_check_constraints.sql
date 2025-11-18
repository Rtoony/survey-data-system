-- Migration 025: Add CHECK Constraints to Quality Score Columns
-- This addresses MEDIUM Priority Issue #9-12 from Architecture Audit Report
-- Date: 2025-11-18
--
-- Purpose: Add CHECK constraints to all quality_score and confidence_score columns
-- to ensure values stay within valid 0.0-1.0 range. This prevents data integrity
-- issues and enforces validation at the database level instead of relying on
-- application code.
--
-- See: NUMERIC_TYPE_STANDARDIZATION_ANALYSIS.md for detailed analysis

-- ============================================================================
-- PHASE 1: Add CHECK Constraints (HIGH PRIORITY, LOW RISK)
-- ============================================================================

-- Step 1: Verify current data is within valid range
-- This query should return 0 rows for all tables if data is clean
DO $$
DECLARE
    invalid_count INTEGER := 0;
    table_name TEXT;
    invalid_rows INTEGER;
BEGIN
    RAISE NOTICE '=== Validating Existing Data ===';

    -- Check each table with quality_score column
    FOR table_name IN
        SELECT DISTINCT c.table_name
        FROM information_schema.columns c
        WHERE c.column_name = 'quality_score'
        AND c.table_schema = 'public'
        ORDER BY c.table_name
    LOOP
        EXECUTE format(
            'SELECT COUNT(*) FROM %I
             WHERE quality_score IS NOT NULL
             AND (quality_score < 0.0 OR quality_score > 1.0)',
            table_name
        ) INTO invalid_rows;

        IF invalid_rows > 0 THEN
            RAISE WARNING 'Table %.%: % rows with invalid quality_score (outside 0.0-1.0)',
                'public', table_name, invalid_rows;
            invalid_count := invalid_count + invalid_rows;
        ELSE
            RAISE NOTICE 'Table %.%: All quality_score values valid', 'public', table_name;
        END IF;
    END LOOP;

    -- Check confidence_score in entity_relationships
    SELECT COUNT(*) INTO invalid_rows
    FROM entity_relationships
    WHERE confidence_score IS NOT NULL
    AND (confidence_score < 0.0 OR confidence_score > 1.0);

    IF invalid_rows > 0 THEN
        RAISE WARNING 'Table public.entity_relationships: % rows with invalid confidence_score', invalid_rows;
        invalid_count := invalid_count + invalid_rows;
    ELSE
        RAISE NOTICE 'Table public.entity_relationships: All confidence_score values valid';
    END IF;

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Found % total rows with invalid scores. Fix data before adding constraints.', invalid_count;
    ELSE
        RAISE NOTICE '✓ All existing data is valid. Safe to add CHECK constraints.';
    END IF;
END $$;

-- Step 2: Add CHECK constraints to all quality_score columns
-- Using dynamic SQL to iterate through all tables with quality_score
DO $$
DECLARE
    table_rec RECORD;
    constraint_name TEXT;
    add_count INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Adding CHECK Constraints ===';

    FOR table_rec IN
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE column_name = 'quality_score'
        AND table_schema = 'public'
        ORDER BY table_name
    LOOP
        constraint_name := 'chk_' || table_rec.table_name || '_quality_score';

        -- Drop constraint if it already exists (idempotent)
        BEGIN
            EXECUTE format('ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I',
                table_rec.table_name, constraint_name);
        EXCEPTION WHEN OTHERS THEN
            -- Ignore errors from dropping non-existent constraints
            NULL;
        END;

        -- Add the CHECK constraint
        EXECUTE format(
            'ALTER TABLE %I ADD CONSTRAINT %I
             CHECK (quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0))',
            table_rec.table_name,
            constraint_name
        );

        RAISE NOTICE '✓ Added constraint % to table %', constraint_name, table_rec.table_name;
        add_count := add_count + 1;
    END LOOP;

    RAISE NOTICE 'Added CHECK constraints to % tables', add_count;
END $$;

-- Step 3: Add CHECK constraint to entity_relationships.confidence_score
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Adding Confidence Score Constraint ===';

    -- Drop if exists (idempotent)
    ALTER TABLE entity_relationships DROP CONSTRAINT IF EXISTS chk_confidence_score;

    -- Add CHECK constraint
    ALTER TABLE entity_relationships
    ADD CONSTRAINT chk_confidence_score
    CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0));

    RAISE NOTICE '✓ Added constraint chk_confidence_score to entity_relationships';
END $$;

-- Step 4: Add schema comments documenting the constraints
DO $$
DECLARE
    table_rec RECORD;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Adding Schema Comments ===';

    -- Add comments to all quality_score columns
    FOR table_rec IN
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE column_name = 'quality_score'
        AND table_schema = 'public'
        ORDER BY table_name
    LOOP
        EXECUTE format(
            'COMMENT ON COLUMN %I.quality_score IS
             ''Data quality score (0.0-1.0). Calculated based on completeness (70%%),
             embedding presence (15%% bonus), and relationship presence (15%% bonus).
             See compute_quality_score() function for calculation logic.''',
            table_rec.table_name
        );

        RAISE NOTICE '✓ Added comment to %.quality_score', table_rec.table_name;
    END LOOP;

    -- Add comment to confidence_score
    COMMENT ON COLUMN entity_relationships.confidence_score IS
    'AI confidence in relationship detection (0.0-1.0).
    1.0 = explicit/manual relationship, <1.0 = AI-inferred with confidence level.';

    RAISE NOTICE '✓ Added comment to entity_relationships.confidence_score';
END $$;

-- Step 5: Test the constraints
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Testing CHECK Constraints ===';

    -- Test that invalid values are rejected
    BEGIN
        -- This should fail
        INSERT INTO utility_lines (line_id, project_id, utility_system, geometry, quality_score)
        VALUES (gen_random_uuid(), gen_random_uuid(), 'test', ST_GeomFromText('LINESTRING(0 0 0, 1 1 1)', 2226), 1.5);

        RAISE EXCEPTION 'TEST FAILED: Invalid quality_score was accepted!';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE '✓ Test passed: Invalid quality_score (1.5) correctly rejected';
            ROLLBACK;
    END;

    -- Test that valid values are accepted
    BEGIN
        INSERT INTO utility_lines (line_id, project_id, utility_system, geometry, quality_score)
        VALUES (gen_random_uuid(), gen_random_uuid(), 'test', ST_GeomFromText('LINESTRING(0 0 0, 1 1 1)', 2226), 0.85);

        RAISE NOTICE '✓ Test passed: Valid quality_score (0.85) accepted';
        ROLLBACK;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'TEST FAILED: Valid quality_score was rejected! Error: %', SQLERRM;
    END;
END $$;

-- Step 6: Verify all constraints were added
DO $$
DECLARE
    constraint_count INTEGER;
    expected_count INTEGER;
    table_count INTEGER;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Verification ===';

    -- Count tables with quality_score column
    SELECT COUNT(DISTINCT table_name) INTO table_count
    FROM information_schema.columns
    WHERE column_name = 'quality_score'
    AND table_schema = 'public';

    -- Count quality_score CHECK constraints
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
        ON tc.constraint_name = ccu.constraint_name
    WHERE tc.constraint_type = 'CHECK'
    AND ccu.column_name = 'quality_score'
    AND tc.table_schema = 'public';

    RAISE NOTICE 'Tables with quality_score column: %', table_count;
    RAISE NOTICE 'CHECK constraints on quality_score: %', constraint_count;

    IF constraint_count = table_count THEN
        RAISE NOTICE '✓ All quality_score columns have CHECK constraints';
    ELSE
        RAISE WARNING 'Expected % constraints, found %', table_count, constraint_count;
    END IF;

    -- Verify confidence_score constraint
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
        ON tc.constraint_name = ccu.constraint_name
    WHERE tc.constraint_type = 'CHECK'
    AND ccu.column_name = 'confidence_score'
    AND tc.table_name = 'entity_relationships'
    AND tc.table_schema = 'public';

    IF constraint_count = 1 THEN
        RAISE NOTICE '✓ confidence_score has CHECK constraint';
    ELSE
        RAISE WARNING 'confidence_score CHECK constraint not found';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 025 Complete ===';
    RAISE NOTICE 'Added CHECK constraints to enforce 0.0-1.0 range on all quality scores';
    RAISE NOTICE 'See NUMERIC_TYPE_STANDARDIZATION_ANALYSIS.md for details';
END $$;

-- Migration complete
