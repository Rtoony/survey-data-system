-- ============================================================================
-- SPEC-GEOMETRY LINKING SYSTEM - DATABASE MIGRATION
-- ============================================================================
-- Version: 010
-- Date: 2025-11-18
-- Description: Creates tables and indexes for specification-to-geometry linking
--              with CSI MasterFormat integration, compliance rules, and auto-linking
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. CSI MASTERFORMAT HIERARCHY TABLE
-- ============================================================================
-- Industry-standard construction specification taxonomy
-- Supports full 50-division structure with hierarchical relationships

CREATE TABLE IF NOT EXISTS csi_masterformat (
    csi_code VARCHAR(10) PRIMARY KEY,
    csi_title TEXT NOT NULL,

    -- Hierarchical breakdown
    division INTEGER,          -- Level 1: 00-49 (e.g., 02 = Existing Conditions)
    section INTEGER,           -- Level 2: 00-99 (e.g., 66 = Utility Systems)
    subsection INTEGER,        -- Level 3: 00-99 (e.g., 13 = Storm Drainage)

    -- Tree structure
    parent_code VARCHAR(10) REFERENCES csi_masterformat(csi_code) ON DELETE SET NULL,
    level INTEGER NOT NULL,    -- 1=Division, 2=Section, 3=Subsection

    -- Documentation
    description TEXT,
    notes TEXT,

    -- Metadata
    is_civil_engineering BOOLEAN DEFAULT FALSE,  -- Flag for civil/survey divisions
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_level CHECK (level BETWEEN 1 AND 3),
    CONSTRAINT valid_division CHECK (division IS NULL OR (division >= 0 AND division <= 49))
);

-- Indexes for CSI hierarchy queries
CREATE INDEX idx_csi_masterformat_division ON csi_masterformat(division);
CREATE INDEX idx_csi_masterformat_parent ON csi_masterformat(parent_code);
CREATE INDEX idx_csi_masterformat_level ON csi_masterformat(level);
CREATE INDEX idx_csi_masterformat_civil ON csi_masterformat(is_civil_engineering) WHERE is_civil_engineering = TRUE;

COMMENT ON TABLE csi_masterformat IS 'CSI MasterFormat construction specification taxonomy';
COMMENT ON COLUMN csi_masterformat.csi_code IS 'Standard CSI code format: "02 66 13"';
COMMENT ON COLUMN csi_masterformat.is_civil_engineering IS 'TRUE for divisions 02, 33, 34 (civil/utilities)';

-- ============================================================================
-- 2. UPDATE SPEC_LIBRARY TABLE
-- ============================================================================
-- Add CSI code linkage to existing spec library

ALTER TABLE spec_library
ADD COLUMN IF NOT EXISTS csi_code VARCHAR(10) REFERENCES csi_masterformat(csi_code) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_spec_library_csi ON spec_library(csi_code);

COMMENT ON COLUMN spec_library.csi_code IS 'Links specification to CSI MasterFormat taxonomy';

-- ============================================================================
-- 3. SPEC-GEOMETRY LINKS TABLE
-- ============================================================================
-- Core linking table connecting specifications to CAD/GIS entities
-- Supports bi-directional navigation and compliance tracking

CREATE TABLE IF NOT EXISTS spec_geometry_links (
    link_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link endpoints
    spec_library_id UUID NOT NULL REFERENCES spec_library(spec_library_id) ON DELETE CASCADE,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'pipe', 'manhole', 'catch_basin', etc.
    entity_table VARCHAR(100),         -- Source table name for reference

    -- Project context
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Relationship semantics
    link_type VARCHAR(20) NOT NULL DEFAULT 'governs',
    relationship_notes TEXT,

    -- Compliance tracking
    compliance_status VARCHAR(20) DEFAULT 'pending',
    compliance_notes TEXT,
    last_checked TIMESTAMP,
    compliance_data JSONB,  -- Store detailed compliance check results

    -- Audit trail
    linked_by VARCHAR(100),
    linked_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Auto-linking metadata
    auto_linked BOOLEAN DEFAULT FALSE,
    auto_link_rule_id UUID,  -- Reference to rule that created this link
    link_confidence FLOAT,   -- 0.0-1.0 confidence score for auto-links

    -- Soft delete support
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_link_type CHECK (link_type IN ('governs', 'references', 'impacts', 'related')),
    CONSTRAINT valid_compliance_status CHECK (compliance_status IN ('compliant', 'warning', 'violation', 'pending', 'not_applicable', 'waived')),
    CONSTRAINT valid_confidence CHECK (link_confidence IS NULL OR (link_confidence >= 0.0 AND link_confidence <= 1.0)),
    CONSTRAINT unique_spec_entity_link UNIQUE (spec_library_id, entity_id, entity_type, project_id)
);

-- Indexes for performance
CREATE INDEX idx_spec_geometry_links_spec ON spec_geometry_links(spec_library_id);
CREATE INDEX idx_spec_geometry_links_entity ON spec_geometry_links(entity_id);
CREATE INDEX idx_spec_geometry_links_entity_type ON spec_geometry_links(entity_type);
CREATE INDEX idx_spec_geometry_links_project ON spec_geometry_links(project_id);
CREATE INDEX idx_spec_geometry_links_status ON spec_geometry_links(compliance_status);
CREATE INDEX idx_spec_geometry_links_type ON spec_geometry_links(link_type);
CREATE INDEX idx_spec_geometry_links_active ON spec_geometry_links(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_spec_geometry_links_auto ON spec_geometry_links(auto_linked, link_confidence);

COMMENT ON TABLE spec_geometry_links IS 'Bi-directional links between specifications and CAD/GIS entities';
COMMENT ON COLUMN spec_geometry_links.link_type IS 'governs=spec controls entity, references=spec mentions entity, impacts=spec affects entity';
COMMENT ON COLUMN spec_geometry_links.compliance_status IS 'Tracks whether entity meets spec requirements';
COMMENT ON COLUMN spec_geometry_links.auto_linked IS 'TRUE if created by auto-linking engine';
COMMENT ON COLUMN spec_geometry_links.link_confidence IS 'AI/ML confidence score for auto-generated links (0.0-1.0)';

-- ============================================================================
-- 4. COMPLIANCE RULES TABLE
-- ============================================================================
-- Define validation rules for spec-entity compliance checking
-- Uses JSONB for flexible rule expression

CREATE TABLE IF NOT EXISTS compliance_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL,
    rule_code VARCHAR(50) UNIQUE,  -- Short identifier like 'PIPE_DIA_CHECK'

    -- Rule scope
    csi_code VARCHAR(10) REFERENCES csi_masterformat(csi_code) ON DELETE SET NULL,
    spec_standard_id UUID REFERENCES spec_standards(spec_standard_id) ON DELETE SET NULL,
    spec_library_id UUID REFERENCES spec_library(spec_library_id) ON DELETE CASCADE,

    -- Rule definition
    rule_type VARCHAR(50) NOT NULL,
    rule_expression JSONB NOT NULL,

    -- Entity targeting
    entity_types TEXT[],  -- Array of entity types this rule applies to
    layer_patterns TEXT[], -- Array of regex patterns for layer matching

    -- Severity and messaging
    severity VARCHAR(20) DEFAULT 'warning',
    error_message TEXT NOT NULL,
    help_text TEXT,

    -- Automated checking
    auto_check BOOLEAN DEFAULT TRUE,
    check_on_link BOOLEAN DEFAULT TRUE,
    check_on_update BOOLEAN DEFAULT TRUE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,  -- Lower number = higher priority

    -- Metadata
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_severity CHECK (severity IN ('error', 'warning', 'info')),
    CONSTRAINT valid_rule_type CHECK (rule_type IN (
        'dimension_check', 'property_match', 'material_validation',
        'spatial_check', 'attribute_required', 'range_validation',
        'pattern_match', 'custom_expression'
    ))
);

-- Indexes for rule queries
CREATE INDEX idx_compliance_rules_csi ON compliance_rules(csi_code);
CREATE INDEX idx_compliance_rules_spec_standard ON compliance_rules(spec_standard_id);
CREATE INDEX idx_compliance_rules_spec_library ON compliance_rules(spec_library_id);
CREATE INDEX idx_compliance_rules_type ON compliance_rules(rule_type);
CREATE INDEX idx_compliance_rules_active ON compliance_rules(is_active, priority) WHERE is_active = TRUE;
CREATE INDEX idx_compliance_rules_entity_types ON compliance_rules USING GIN(entity_types);

COMMENT ON TABLE compliance_rules IS 'Validation rules for spec-entity compliance checking';
COMMENT ON COLUMN compliance_rules.rule_expression IS 'JSONB rule definition with conditions and parameters';
COMMENT ON COLUMN compliance_rules.entity_types IS 'Array of entity types (e.g., ["pipe", "manhole"]) this rule applies to';
COMMENT ON COLUMN compliance_rules.auto_check IS 'If TRUE, run this rule automatically on schedule';

-- ============================================================================
-- 5. AUTO-LINKING RULES TABLE
-- ============================================================================
-- Pattern-based rules for automatic spec-entity linking
-- Supports layer patterns, property matching, and AI classification

CREATE TABLE IF NOT EXISTS auto_link_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) NOT NULL,
    rule_code VARCHAR(50) UNIQUE,
    description TEXT,

    -- Rule priority (lower = higher priority)
    priority INTEGER DEFAULT 100,

    -- Match criteria
    match_type VARCHAR(50) NOT NULL,
    match_expression JSONB NOT NULL,

    -- Targeting
    entity_types TEXT[],
    layer_patterns TEXT[],  -- Regex patterns for layer names
    property_conditions JSONB,  -- Additional property filters

    -- Link target
    target_spec_id UUID REFERENCES spec_library(spec_library_id) ON DELETE CASCADE,
    target_csi_code VARCHAR(10) REFERENCES csi_masterformat(csi_code) ON DELETE SET NULL,

    -- Link properties
    link_type VARCHAR(20) DEFAULT 'governs',
    confidence_threshold FLOAT DEFAULT 0.8,

    -- Execution control
    is_active BOOLEAN DEFAULT TRUE,
    auto_apply BOOLEAN DEFAULT FALSE,  -- If TRUE, apply automatically; if FALSE, suggest only
    require_review BOOLEAN DEFAULT TRUE,  -- Require human review before applying

    -- Project scope
    apply_to_all_projects BOOLEAN DEFAULT TRUE,
    project_ids UUID[],  -- Specific projects if apply_to_all_projects = FALSE

    -- Statistics
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,
    last_applied TIMESTAMP,

    -- Metadata
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_match_type CHECK (match_type IN (
        'layer_pattern', 'property_match', 'spatial_proximity',
        'entity_classification', 'ml_classification', 'hybrid'
    )),
    CONSTRAINT valid_link_type_auto CHECK (link_type IN ('governs', 'references', 'impacts', 'related')),
    CONSTRAINT valid_confidence CHECK (confidence_threshold >= 0.0 AND confidence_threshold <= 1.0),
    CONSTRAINT has_target CHECK (target_spec_id IS NOT NULL OR target_csi_code IS NOT NULL)
);

-- Indexes for auto-linking
CREATE INDEX idx_auto_link_rules_priority ON auto_link_rules(priority DESC, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_auto_link_rules_match_type ON auto_link_rules(match_type);
CREATE INDEX idx_auto_link_rules_target_spec ON auto_link_rules(target_spec_id);
CREATE INDEX idx_auto_link_rules_target_csi ON auto_link_rules(target_csi_code);
CREATE INDEX idx_auto_link_rules_entity_types ON auto_link_rules USING GIN(entity_types);
CREATE INDEX idx_auto_link_rules_active_auto ON auto_link_rules(is_active, auto_apply) WHERE is_active = TRUE AND auto_apply = TRUE;

COMMENT ON TABLE auto_link_rules IS 'Pattern-based rules for automatic spec-entity linking';
COMMENT ON COLUMN auto_link_rules.match_expression IS 'JSONB pattern definition (regex, properties, spatial criteria)';
COMMENT ON COLUMN auto_link_rules.auto_apply IS 'If TRUE, apply automatically; if FALSE, suggest only';
COMMENT ON COLUMN auto_link_rules.require_review IS 'Require human review before applying auto-link';

-- ============================================================================
-- 6. COMPLIANCE HISTORY TABLE
-- ============================================================================
-- Audit trail for compliance status changes

CREATE TABLE IF NOT EXISTS compliance_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID NOT NULL REFERENCES spec_geometry_links(link_id) ON DELETE CASCADE,

    -- Status change
    old_status VARCHAR(20),
    new_status VARCHAR(20),

    -- Violation details
    rule_violations JSONB,  -- Array of rule violations found

    -- Timestamp and user
    checked_by VARCHAR(100),
    checked_at TIMESTAMP DEFAULT NOW(),

    -- Check metadata
    check_type VARCHAR(50),  -- 'manual', 'auto', 'scheduled'
    check_duration_ms INTEGER,  -- Performance tracking

    CONSTRAINT valid_old_status CHECK (old_status IN ('compliant', 'warning', 'violation', 'pending', 'not_applicable', 'waived')),
    CONSTRAINT valid_new_status CHECK (new_status IN ('compliant', 'warning', 'violation', 'pending', 'not_applicable', 'waived'))
);

CREATE INDEX idx_compliance_history_link ON compliance_history(link_id);
CREATE INDEX idx_compliance_history_timestamp ON compliance_history(checked_at DESC);
CREATE INDEX idx_compliance_history_status ON compliance_history(new_status);

COMMENT ON TABLE compliance_history IS 'Audit trail for compliance status changes over time';

-- ============================================================================
-- 7. SPEC LINK SUGGESTIONS TABLE
-- ============================================================================
-- Store AI/ML suggestions for spec-entity links before they're approved

CREATE TABLE IF NOT EXISTS spec_link_suggestions (
    suggestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Suggested link
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    suggested_spec_id UUID NOT NULL REFERENCES spec_library(spec_library_id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Suggestion metadata
    link_type VARCHAR(20) DEFAULT 'governs',
    confidence_score FLOAT NOT NULL,

    -- Source of suggestion
    suggestion_source VARCHAR(50) NOT NULL,  -- 'auto_link_rule', 'ml_model', 'similar_entity', 'user_pattern'
    source_rule_id UUID REFERENCES auto_link_rules(rule_id) ON DELETE SET NULL,
    reasoning TEXT,  -- Explanation for the suggestion

    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,

    -- User feedback
    user_action VARCHAR(20),  -- 'accepted', 'rejected', 'modified'
    feedback_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- Optional expiry for old suggestions

    CONSTRAINT valid_confidence_suggestion CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    CONSTRAINT valid_suggestion_status CHECK (status IN ('pending', 'accepted', 'rejected', 'expired')),
    CONSTRAINT valid_user_action CHECK (user_action IN ('accepted', 'rejected', 'modified', 'ignored'))
);

CREATE INDEX idx_spec_link_suggestions_entity ON spec_link_suggestions(entity_id, entity_type);
CREATE INDEX idx_spec_link_suggestions_spec ON spec_link_suggestions(suggested_spec_id);
CREATE INDEX idx_spec_link_suggestions_project ON spec_link_suggestions(project_id);
CREATE INDEX idx_spec_link_suggestions_status ON spec_link_suggestions(status) WHERE status = 'pending';
CREATE INDEX idx_spec_link_suggestions_confidence ON spec_link_suggestions(confidence_score DESC);

COMMENT ON TABLE spec_link_suggestions IS 'AI/ML-generated suggestions for spec-entity links awaiting review';
COMMENT ON COLUMN spec_link_suggestions.reasoning IS 'Human-readable explanation of why this link was suggested';

-- ============================================================================
-- 8. HELPER FUNCTIONS
-- ============================================================================

-- Function to get all child CSI codes (hierarchical query)
CREATE OR REPLACE FUNCTION get_csi_children(parent_code_input VARCHAR)
RETURNS TABLE(csi_code VARCHAR, csi_title TEXT, level INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE csi_tree AS (
        -- Base case: the parent code itself
        SELECT m.csi_code, m.csi_title, m.level, m.parent_code
        FROM csi_masterformat m
        WHERE m.csi_code = parent_code_input

        UNION ALL

        -- Recursive case: all children
        SELECT m.csi_code, m.csi_title, m.level, m.parent_code
        FROM csi_masterformat m
        INNER JOIN csi_tree t ON m.parent_code = t.csi_code
    )
    SELECT ct.csi_code, ct.csi_title, ct.level
    FROM csi_tree ct
    ORDER BY ct.csi_code;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_csi_children IS 'Returns all child CSI codes recursively for a given parent code';

-- Function to calculate compliance percentage for a project
CREATE OR REPLACE FUNCTION get_project_compliance_percentage(project_id_input UUID)
RETURNS TABLE(
    total_links BIGINT,
    compliant_count BIGINT,
    warning_count BIGINT,
    violation_count BIGINT,
    pending_count BIGINT,
    compliance_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_links,
        COUNT(*) FILTER (WHERE compliance_status = 'compliant')::BIGINT as compliant_count,
        COUNT(*) FILTER (WHERE compliance_status = 'warning')::BIGINT as warning_count,
        COUNT(*) FILTER (WHERE compliance_status = 'violation')::BIGINT as violation_count,
        COUNT(*) FILTER (WHERE compliance_status = 'pending')::BIGINT as pending_count,
        CASE
            WHEN COUNT(*) > 0 THEN
                ROUND((COUNT(*) FILTER (WHERE compliance_status = 'compliant')::NUMERIC / COUNT(*)::NUMERIC) * 100, 2)
            ELSE 0
        END as compliance_percentage
    FROM spec_geometry_links
    WHERE project_id = project_id_input
        AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_project_compliance_percentage IS 'Calculates compliance statistics for a project';

-- ============================================================================
-- 9. TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_csi_masterformat_timestamp
    BEFORE UPDATE ON csi_masterformat
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_spec_geometry_links_timestamp
    BEFORE UPDATE ON spec_geometry_links
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_compliance_rules_timestamp
    BEFORE UPDATE ON compliance_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_auto_link_rules_timestamp
    BEFORE UPDATE ON auto_link_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Trigger to log compliance status changes
CREATE OR REPLACE FUNCTION log_compliance_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.compliance_status IS DISTINCT FROM NEW.compliance_status THEN
        INSERT INTO compliance_history (link_id, old_status, new_status, checked_by, check_type)
        VALUES (NEW.link_id, OLD.compliance_status, NEW.compliance_status, NEW.updated_by, 'auto');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_spec_link_compliance_change
    AFTER UPDATE ON spec_geometry_links
    FOR EACH ROW
    WHEN (OLD.compliance_status IS DISTINCT FROM NEW.compliance_status)
    EXECUTE FUNCTION log_compliance_change();

-- ============================================================================
-- 10. GRANTS (Adjust based on your user roles)
-- ============================================================================

-- Grant permissions (modify based on your role structure)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Insert migration tracking record (if you have a migrations table)
-- INSERT INTO schema_migrations (version, description, applied_at)
-- VALUES ('010', 'Spec-Geometry Linking System', NOW());

-- Summary
DO $$
BEGIN
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Spec-Geometry Linking System Migration Complete';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Tables Created:';
    RAISE NOTICE '  - csi_masterformat (CSI code hierarchy)';
    RAISE NOTICE '  - spec_geometry_links (core linking table)';
    RAISE NOTICE '  - compliance_rules (validation rules)';
    RAISE NOTICE '  - auto_link_rules (auto-linking patterns)';
    RAISE NOTICE '  - compliance_history (audit trail)';
    RAISE NOTICE '  - spec_link_suggestions (AI suggestions)';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Modified:';
    RAISE NOTICE '  - spec_library (added csi_code column)';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions Created:';
    RAISE NOTICE '  - get_csi_children()';
    RAISE NOTICE '  - get_project_compliance_percentage()';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Run migration: 011_csi_masterformat_seed.sql (CSI data)';
    RAISE NOTICE '  2. Verify schema with: \d spec_geometry_links';
    RAISE NOTICE '  3. Test helper functions';
    RAISE NOTICE '============================================================================';
END $$;
