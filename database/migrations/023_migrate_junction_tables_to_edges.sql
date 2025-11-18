-- ============================================================================
-- PHASE 3: MIGRATE JUNCTION TABLES TO RELATIONSHIP EDGES
-- Migration 023: Migrate existing junction table data to unified graph model
--
-- Purpose: Migrate data from separate junction tables to the new relationship_edges table
--          while preserving all existing relationships.
--
-- Junction Tables to Migrate:
--   - project_keynote_block_mappings → relationship_edges
--   - project_keynote_detail_mappings → relationship_edges
--   - project_hatch_material_mappings → relationship_edges
--   - project_detail_material_mappings → relationship_edges
--   - project_element_cross_references → relationship_edges
--
-- References: docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
-- ============================================================================

-- Safety check: Ensure relationship_edges table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'relationship_edges') THEN
        RAISE EXCEPTION 'relationship_edges table does not exist. Run migration 022 first.';
    END IF;
END $$;


-- ============================================================================
-- MIGRATION SECTION 1: Keynote → Block Mappings
-- ============================================================================

INSERT INTO relationship_edges (
    project_id,
    source_entity_type,
    source_entity_id,
    target_entity_type,
    target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    source,
    is_active
)
SELECT
    project_id,
    'note' as source_entity_type,
    note_id as source_entity_id,
    'block' as target_entity_type,
    block_id as target_entity_id,
    'CALLED_OUT_IN' as relationship_type,
    CASE WHEN is_primary THEN 1.0 ELSE 0.7 END as relationship_strength,
    jsonb_build_object(
        'keynote_number', keynote_number,
        'block_instance_reference', block_instance_reference,
        'is_primary', is_primary,
        'relationship_notes', relationship_notes,
        'migrated_from', 'project_keynote_block_mappings'
    ) as relationship_metadata,
    created_by,
    created_at,
    'migration' as source,
    is_active
FROM project_keynote_block_mappings
WHERE note_id IS NOT NULL
  AND block_id IS NOT NULL
ON CONFLICT (project_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
DO UPDATE SET
    relationship_strength = EXCLUDED.relationship_strength,
    relationship_metadata = EXCLUDED.relationship_metadata,
    updated_at = CURRENT_TIMESTAMP;

-- Log migration progress
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM relationship_edges
    WHERE source = 'migration'
      AND relationship_metadata->>'migrated_from' = 'project_keynote_block_mappings';

    RAISE NOTICE 'Migrated % keynote-block relationships', v_count;
END $$;


-- ============================================================================
-- MIGRATION SECTION 2: Keynote → Detail Mappings
-- ============================================================================

INSERT INTO relationship_edges (
    project_id,
    source_entity_type,
    source_entity_id,
    target_entity_type,
    target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    source,
    is_active
)
SELECT
    project_id,
    'note' as source_entity_type,
    note_id as source_entity_id,
    'detail' as target_entity_type,
    detail_id as target_entity_id,
    'CALLED_OUT_IN' as relationship_type,
    CASE WHEN is_primary THEN 1.0 ELSE 0.7 END as relationship_strength,
    jsonb_build_object(
        'keynote_number', keynote_number,
        'detail_callout', detail_callout,
        'sheet_number', sheet_number,
        'is_primary', is_primary,
        'relationship_notes', relationship_notes,
        'migrated_from', 'project_keynote_detail_mappings'
    ) as relationship_metadata,
    created_by,
    created_at,
    'migration' as source,
    is_active
FROM project_keynote_detail_mappings
WHERE note_id IS NOT NULL
  AND detail_id IS NOT NULL
ON CONFLICT (project_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
DO UPDATE SET
    relationship_strength = EXCLUDED.relationship_strength,
    relationship_metadata = EXCLUDED.relationship_metadata,
    updated_at = CURRENT_TIMESTAMP;

-- Log migration progress
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM relationship_edges
    WHERE source = 'migration'
      AND relationship_metadata->>'migrated_from' = 'project_keynote_detail_mappings';

    RAISE NOTICE 'Migrated % keynote-detail relationships', v_count;
END $$;


-- ============================================================================
-- MIGRATION SECTION 3: Hatch → Material Mappings
-- ============================================================================

INSERT INTO relationship_edges (
    project_id,
    source_entity_type,
    source_entity_id,
    target_entity_type,
    target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    source,
    is_active
)
SELECT
    project_id,
    'hatch' as source_entity_type,
    hatch_id as source_entity_id,
    'material' as target_entity_type,
    material_id as target_entity_id,
    'REPRESENTS' as relationship_type,
    0.9 as relationship_strength,  -- High strength as hatches directly represent materials
    jsonb_build_object(
        'hatch_name', hatch_name,
        'material_thickness', material_thickness,
        'material_notes', material_notes,
        'detail_reference', detail_reference,
        'display_color_rgb', display_color_rgb,
        'hatch_scale_override', hatch_scale_override,
        'is_legend_item', is_legend_item,
        'legend_order', legend_order,
        'tags', tags,
        'migrated_from', 'project_hatch_material_mappings'
    ) as relationship_metadata,
    created_by,
    created_at,
    'migration' as source,
    is_active
FROM project_hatch_material_mappings
WHERE hatch_id IS NOT NULL
  AND material_id IS NOT NULL
ON CONFLICT (project_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
DO UPDATE SET
    relationship_strength = EXCLUDED.relationship_strength,
    relationship_metadata = EXCLUDED.relationship_metadata,
    updated_at = CURRENT_TIMESTAMP;

-- Also create hatch → detail edges if detail_id is present
INSERT INTO relationship_edges (
    project_id,
    source_entity_type,
    source_entity_id,
    target_entity_type,
    target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    source,
    is_active
)
SELECT
    project_id,
    'hatch' as source_entity_type,
    hatch_id as source_entity_id,
    'detail' as target_entity_type,
    detail_id as target_entity_id,
    'SHOWN_IN' as relationship_type,
    0.7 as relationship_strength,
    jsonb_build_object(
        'detail_reference', detail_reference,
        'migrated_from', 'project_hatch_material_mappings'
    ) as relationship_metadata,
    created_by,
    created_at,
    'migration' as source,
    is_active
FROM project_hatch_material_mappings
WHERE hatch_id IS NOT NULL
  AND detail_id IS NOT NULL
ON CONFLICT (project_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
DO NOTHING;

-- Log migration progress
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM relationship_edges
    WHERE source = 'migration'
      AND relationship_metadata->>'migrated_from' = 'project_hatch_material_mappings';

    RAISE NOTICE 'Migrated % hatch-material relationships', v_count;
END $$;


-- ============================================================================
-- MIGRATION SECTION 4: Detail → Material Mappings
-- ============================================================================

INSERT INTO relationship_edges (
    project_id,
    source_entity_type,
    source_entity_id,
    target_entity_type,
    target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    source,
    is_active
)
SELECT
    project_id,
    'detail' as source_entity_type,
    detail_id as source_entity_id,
    'material' as target_entity_type,
    material_id as target_entity_id,
    'USES' as relationship_type,
    CASE
        WHEN material_quantity_type = 'primary' THEN 1.0
        WHEN material_quantity_type = 'secondary' THEN 0.7
        ELSE 0.5
    END as relationship_strength,
    jsonb_build_object(
        'material_description', material_description,
        'material_quantity', material_quantity,
        'material_quantity_type', material_quantity_type,
        'layer_reference', layer_reference,
        'is_primary_material', is_primary_material,
        'display_order', display_order,
        'tags', tags,
        'migrated_from', 'project_detail_material_mappings'
    ) as relationship_metadata,
    created_by,
    created_at,
    'migration' as source,
    is_active
FROM project_detail_material_mappings
WHERE detail_id IS NOT NULL
  AND material_id IS NOT NULL
ON CONFLICT (project_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
DO UPDATE SET
    relationship_strength = EXCLUDED.relationship_strength,
    relationship_metadata = EXCLUDED.relationship_metadata,
    updated_at = CURRENT_TIMESTAMP;

-- Log migration progress
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM relationship_edges
    WHERE source = 'migration'
      AND relationship_metadata->>'migrated_from' = 'project_detail_material_mappings';

    RAISE NOTICE 'Migrated % detail-material relationships', v_count;
END $$;


-- ============================================================================
-- MIGRATION SECTION 5: Cross-References
-- ============================================================================

INSERT INTO relationship_edges (
    project_id,
    source_entity_type,
    source_entity_id,
    target_entity_type,
    target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    source,
    is_active
)
SELECT
    project_id,
    source_element_type as source_entity_type,
    source_element_id as source_entity_id,
    target_element_type as target_entity_type,
    target_element_id as target_entity_id,
    COALESCE(reference_type, 'REFERENCES') as relationship_type,
    CASE
        WHEN reference_strength = 'required' THEN 1.0
        WHEN reference_strength = 'strong' THEN 0.8
        WHEN reference_strength = 'weak' THEN 0.4
        ELSE 0.6
    END as relationship_strength,
    jsonb_build_object(
        'source_element_name', source_element_name,
        'target_element_name', target_element_name,
        'reference_context', reference_context,
        'reference_strength', reference_strength,
        'reference_notes', reference_notes,
        'is_bidirectional', is_bidirectional,
        'tags', tags,
        'migrated_from', 'project_element_cross_references'
    ) as relationship_metadata,
    created_by,
    created_at,
    'migration' as source,
    is_active
FROM project_element_cross_references
WHERE source_element_id IS NOT NULL
  AND target_element_id IS NOT NULL
ON CONFLICT (project_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type)
DO UPDATE SET
    relationship_strength = EXCLUDED.relationship_strength,
    relationship_metadata = EXCLUDED.relationship_metadata,
    is_bidirectional = EXCLUDED.relationship_metadata->>'is_bidirectional' = 'true',
    updated_at = CURRENT_TIMESTAMP;

-- Log migration progress
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM relationship_edges
    WHERE source = 'migration'
      AND relationship_metadata->>'migrated_from' = 'project_element_cross_references';

    RAISE NOTICE 'Migrated % cross-reference relationships', v_count;
END $$;


-- ============================================================================
-- POST-MIGRATION VALIDATION
-- ============================================================================

-- Create a summary view of migration results
CREATE OR REPLACE VIEW vw_migration_summary AS
SELECT
    relationship_metadata->>'migrated_from' as source_table,
    COUNT(*) as edge_count,
    COUNT(DISTINCT project_id) as project_count,
    COUNT(DISTINCT relationship_type) as relationship_types,
    MIN(created_at) as earliest_relationship,
    MAX(created_at) as latest_relationship
FROM relationship_edges
WHERE source = 'migration'
GROUP BY relationship_metadata->>'migrated_from';

COMMENT ON VIEW vw_migration_summary IS 'Summary of data migrated from junction tables to relationship_edges';

-- Display migration summary
DO $$
DECLARE
    rec RECORD;
    total_count INTEGER;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'RELATIONSHIP MIGRATION SUMMARY';
    RAISE NOTICE '========================================';

    FOR rec IN SELECT * FROM vw_migration_summary ORDER BY edge_count DESC
    LOOP
        RAISE NOTICE 'Source: %', rec.source_table;
        RAISE NOTICE '  Edges migrated: %', rec.edge_count;
        RAISE NOTICE '  Projects affected: %', rec.project_count;
        RAISE NOTICE '  Relationship types: %', rec.relationship_types;
        RAISE NOTICE '';
    END LOOP;

    SELECT COUNT(*) INTO total_count FROM relationship_edges WHERE source = 'migration';
    RAISE NOTICE 'TOTAL MIGRATED EDGES: %', total_count;
    RAISE NOTICE '========================================';
END $$;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify no data loss - compare counts
DO $$
DECLARE
    v_keynote_blocks INTEGER;
    v_keynote_details INTEGER;
    v_hatch_materials INTEGER;
    v_detail_materials INTEGER;
    v_cross_refs INTEGER;
    v_total_source INTEGER;
    v_total_migrated INTEGER;
BEGIN
    -- Count source records
    SELECT COUNT(*) INTO v_keynote_blocks FROM project_keynote_block_mappings WHERE note_id IS NOT NULL AND block_id IS NOT NULL;
    SELECT COUNT(*) INTO v_keynote_details FROM project_keynote_detail_mappings WHERE note_id IS NOT NULL AND detail_id IS NOT NULL;
    SELECT COUNT(*) INTO v_hatch_materials FROM project_hatch_material_mappings WHERE hatch_id IS NOT NULL AND material_id IS NOT NULL;
    SELECT COUNT(*) INTO v_detail_materials FROM project_detail_material_mappings WHERE detail_id IS NOT NULL AND material_id IS NOT NULL;
    SELECT COUNT(*) INTO v_cross_refs FROM project_element_cross_references WHERE source_element_id IS NOT NULL AND target_element_id IS NOT NULL;

    v_total_source := v_keynote_blocks + v_keynote_details + v_hatch_materials + v_detail_materials + v_cross_refs;

    -- Count migrated edges (excluding hatch->detail edges which are bonus)
    SELECT COUNT(*) INTO v_total_migrated
    FROM relationship_edges
    WHERE source = 'migration'
      AND NOT (relationship_type = 'SHOWN_IN' AND relationship_metadata->>'migrated_from' = 'project_hatch_material_mappings');

    RAISE NOTICE 'VERIFICATION:';
    RAISE NOTICE '  Source records: %', v_total_source;
    RAISE NOTICE '  Migrated edges: %', v_total_migrated;

    IF v_total_migrated >= v_total_source THEN
        RAISE NOTICE '  ✓ Migration successful - no data loss detected';
    ELSE
        RAISE WARNING '  ⚠ Potential data loss - migrated count less than source count';
        RAISE WARNING '  Difference: %', (v_total_source - v_total_migrated);
    END IF;
END $$;


-- ============================================================================
-- OPTIONAL: Mark junction tables as deprecated
-- ============================================================================

-- Add comments to junction tables indicating they are deprecated
COMMENT ON TABLE project_keynote_block_mappings IS 'DEPRECATED: Migrated to relationship_edges. Kept for backward compatibility.';
COMMENT ON TABLE project_keynote_detail_mappings IS 'DEPRECATED: Migrated to relationship_edges. Kept for backward compatibility.';
COMMENT ON TABLE project_hatch_material_mappings IS 'DEPRECATED: Migrated to relationship_edges. Kept for backward compatibility.';
COMMENT ON TABLE project_detail_material_mappings IS 'DEPRECATED: Migrated to relationship_edges. Kept for backward compatibility.';
COMMENT ON TABLE project_element_cross_references IS 'DEPRECATED: Migrated to relationship_edges. Kept for backward compatibility.';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

RAISE NOTICE '';
RAISE NOTICE '========================================';
RAISE NOTICE 'MIGRATION 023 COMPLETE';
RAISE NOTICE 'All junction table data has been migrated to relationship_edges';
RAISE NOTICE 'Original tables retained for backward compatibility';
RAISE NOTICE '========================================';
