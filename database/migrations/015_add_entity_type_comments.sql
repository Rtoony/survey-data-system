-- Migration 015: Add Clarifying Comments for Entity Type Columns
-- This addresses High Priority Issue #7 from Architecture Audit Report
-- Date: 2025-11-17
--
-- Purpose: Add database comments to clarify the three different meanings of "entity_type"
-- across different tables to prevent developer confusion

-- Three different entity_type systems:
-- 1. standards_entities.entity_type - Type of standardized entity (layer, block, survey_point, utility_line, etc.)
-- 2. cad_entities.entity_type - DXF primitive type (LINE, POLYLINE, ARC, CIRCLE, etc.)
-- 3. project_context_mappings.source_type/target_type - Context mapping types (keynote, block, detail, etc.)

-- Add comment to standards_entities.entity_type
COMMENT ON COLUMN standards_entities.entity_type IS
'Type of standardized entity in the system (e.g., ''layer'', ''block'', ''survey_point'', ''utility_line'').
This represents the SEMANTIC entity type in the standards library, NOT the DXF primitive type.
For DXF primitive types, see cad_entities.entity_type.';

-- Add comment to cad_entities.entity_type (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cad_entities') THEN
        EXECUTE 'COMMENT ON COLUMN cad_entities.entity_type IS
''DXF primitive type from AutoCAD (e.g., ''''LINE'''', ''''POLYLINE'''', ''''ARC'''', ''''CIRCLE'''', ''''TEXT'''').
This represents the CAD drawing primitive, NOT the semantic entity type.
For semantic entity types, see standards_entities.entity_type.''';
    END IF;
END $$;

-- Add comments to project_context_mappings source_type and target_type (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'project_context_mappings') THEN
        EXECUTE 'COMMENT ON COLUMN project_context_mappings.source_type IS
''Source entity type in context mapping (e.g., ''''keynote'''', ''''block'''', ''''detail'''', ''''material'''').
This represents the type being mapped FROM in the standards context system.''';

        EXECUTE 'COMMENT ON COLUMN project_context_mappings.target_type IS
''Target entity type in context mapping (e.g., ''''keynote'''', ''''block'''', ''''detail'''', ''''material'''').
This represents the type being mapped TO in the standards context system.''';
    END IF;
END $$;

-- Add general table comments for context
COMMENT ON TABLE standards_entities IS
'Unified entity registry storing all standardized entities (layers, blocks, survey points, utilities, etc.).
The entity_type column here refers to SEMANTIC entity types in the standards library.';

-- Verification
DO $$
BEGIN
    RAISE NOTICE '✓ Migration 015 Complete: Added clarifying comments to entity_type columns';
    RAISE NOTICE '  - standards_entities.entity_type: Semantic entity types (layer, block, etc.)';
    RAISE NOTICE '  - cad_entities.entity_type: DXF primitive types (LINE, POLYLINE, etc.)';
    RAISE NOTICE '  - project_context_mappings: Context mapping types (keynote, detail, etc.)';
END $$;
