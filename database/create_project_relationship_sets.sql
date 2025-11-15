-- ============================================================================
-- PROJECT RELATIONSHIP SETS SYSTEM
-- 
-- Purpose: Track dependencies and relationships between project elements
--          (CAD geometry, specs, details, notes, hatches, materials, etc.)
--          to enable audit/compliance checking and change impact analysis.
--
-- Core Concept: A "Relationship Set" groups multiple related items together
--               with optional metadata filtering and sync rules.
--
-- Example: "Pavement Material Compliance Set" might link:
--          - Spec Section 02741 (material: AC)
--          - Detail D-12 (pavement section)
--          - Note N-8 (material callout)
--          - Hatch PAVE-AC
--          - Utility pipes WHERE material='AC' AND diameter>=12
-- ============================================================================

-- Table 1: Relationship Sets (The Container)
CREATE TABLE IF NOT EXISTS project_relationship_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,
    
    -- Identification
    set_name VARCHAR(255) NOT NULL,
    set_code VARCHAR(50),  -- Optional short code
    description TEXT,
    
    -- Categorization
    category VARCHAR(100),  -- e.g., 'material_compliance', 'utility_standards', 'municipal_requirements'
    tags TEXT[],
    
    -- Template / Instance
    is_template BOOLEAN DEFAULT FALSE,  -- Template sets can be applied to multiple projects
    template_id UUID REFERENCES project_relationship_sets(set_id),  -- If created from template
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'draft',  -- 'draft', 'active', 'reviewing', 'archived'
    
    -- Compliance Tracking
    requires_all_members BOOLEAN DEFAULT TRUE,  -- Flag if missing members = violation
    sync_status VARCHAR(50) DEFAULT 'unknown',  -- 'in_sync', 'out_of_sync', 'unknown', 'incomplete'
    last_checked_at TIMESTAMP,
    violation_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(project_id, set_name),
    CHECK (NOT (is_template = TRUE AND project_id IS NOT NULL))  -- Templates are project-agnostic
);

CREATE INDEX idx_relationship_sets_project ON project_relationship_sets(project_id);
CREATE INDEX idx_relationship_sets_template ON project_relationship_sets(is_template, template_id);
CREATE INDEX idx_relationship_sets_status ON project_relationship_sets(sync_status, is_active);

COMMENT ON TABLE project_relationship_sets IS 'Groups related project elements for dependency tracking and compliance checking';
COMMENT ON COLUMN project_relationship_sets.requires_all_members IS 'If true, missing members trigger violations';
COMMENT ON COLUMN project_relationship_sets.sync_status IS 'Current sync state: in_sync, out_of_sync, unknown, incomplete';


-- Table 2: Relationship Set Members (The Elements)
CREATE TABLE IF NOT EXISTS project_relationship_members (
    member_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES project_relationship_sets(set_id) ON DELETE CASCADE,
    
    -- Entity Reference (Polymorphic)
    entity_type VARCHAR(100) NOT NULL,  -- 'detail', 'note', 'hatch', 'material', 'utility_line', 'spec_section', etc.
    entity_table VARCHAR(100) NOT NULL,  -- Database table name
    entity_id UUID,  -- Specific entity ID (NULL for template members or filtered queries)
    
    -- Metadata Filtering (for conditional relationships)
    filter_conditions JSONB,  -- e.g., {"material": "AC", "diameter_gte": 12}
    filter_sql TEXT,  -- Generated SQL WHERE clause for dynamic queries
    
    -- Member Properties
    member_role VARCHAR(100),  -- 'source', 'dependent', 'reference', 'governed_by', etc.
    is_required BOOLEAN DEFAULT TRUE,  -- If true, missing element = violation
    display_order INTEGER DEFAULT 0,
    
    -- Status
    exists BOOLEAN DEFAULT NULL,  -- NULL = unknown, TRUE = found, FALSE = missing
    last_verified_at TIMESTAMP,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CHECK (entity_id IS NOT NULL OR filter_conditions IS NOT NULL)  -- Must have ID or filter
);

CREATE INDEX idx_relationship_members_set ON project_relationship_members(set_id);
CREATE INDEX idx_relationship_members_entity ON project_relationship_members(entity_type, entity_table, entity_id);
CREATE INDEX idx_relationship_members_filter ON project_relationship_members USING GIN(filter_conditions);

COMMENT ON TABLE project_relationship_members IS 'Individual elements within a relationship set';
COMMENT ON COLUMN project_relationship_members.filter_conditions IS 'JSONB conditions for metadata-based filtering (e.g., WHERE material=AC)';
COMMENT ON COLUMN project_relationship_members.entity_id IS 'Specific entity ID or NULL for filtered queries';


-- Table 3: Relationship Set Rules (Sync/Compliance Rules)
CREATE TABLE IF NOT EXISTS project_relationship_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES project_relationship_sets(set_id) ON DELETE CASCADE,
    
    -- Rule Definition
    rule_type VARCHAR(50) NOT NULL,  -- 'existence', 'link_integrity', 'metadata_consistency', 'version_check', 'dependency'
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Rule Configuration
    check_attribute VARCHAR(100),  -- Attribute to check (e.g., 'material', 'revision_date')
    expected_value TEXT,  -- Expected value or expression
    operator VARCHAR(20),  -- 'equals', 'contains', 'greater_than', 'less_than', 'matches_regex'
    
    -- Advanced Configuration
    rule_config JSONB,  -- Flexible config for complex rules
    custom_sql TEXT,  -- Custom SQL for advanced checks
    
    -- Rule Behavior
    severity VARCHAR(20) DEFAULT 'warning',  -- 'info', 'warning', 'error', 'critical'
    is_active BOOLEAN DEFAULT TRUE,
    auto_fix_enabled BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_relationship_rules_set ON project_relationship_rules(set_id);
CREATE INDEX idx_relationship_rules_type ON project_relationship_rules(rule_type, is_active);

COMMENT ON TABLE project_relationship_rules IS 'Sync and compliance rules for relationship sets';
COMMENT ON COLUMN project_relationship_rules.rule_type IS 'Type: existence, link_integrity, metadata_consistency, version_check, dependency';


-- Table 4: Relationship Violations (Detected Issues)
CREATE TABLE IF NOT EXISTS project_relationship_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES project_relationship_sets(set_id) ON DELETE CASCADE,
    rule_id UUID REFERENCES project_relationship_rules(rule_id) ON DELETE SET NULL,
    member_id UUID REFERENCES project_relationship_members(member_id) ON DELETE SET NULL,
    
    -- Violation Details
    violation_type VARCHAR(50) NOT NULL,  -- 'missing_element', 'broken_link', 'metadata_mismatch', etc.
    severity VARCHAR(20) DEFAULT 'warning',
    
    -- Description
    violation_message TEXT NOT NULL,
    details JSONB,  -- Structured details about the violation
    
    -- Affected Entity
    entity_type VARCHAR(100),
    entity_table VARCHAR(100),
    entity_id UUID,
    
    -- Resolution
    status VARCHAR(50) DEFAULT 'open',  -- 'open', 'acknowledged', 'resolved', 'ignored'
    resolution_notes TEXT,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    
    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_relationship_violations_set ON project_relationship_violations(set_id);
CREATE INDEX idx_relationship_violations_status ON project_relationship_violations(status, severity);
CREATE INDEX idx_relationship_violations_entity ON project_relationship_violations(entity_type, entity_id);
CREATE INDEX idx_relationship_violations_detected ON project_relationship_violations(detected_at DESC);

COMMENT ON TABLE project_relationship_violations IS 'Detected out-of-sync conditions and compliance violations';
COMMENT ON COLUMN project_relationship_violations.status IS 'Status: open, acknowledged, resolved, ignored';


-- Helper View: Relationship Set Summary
CREATE OR REPLACE VIEW vw_relationship_set_summary AS
SELECT 
    s.set_id,
    s.project_id,
    s.set_name,
    s.set_code,
    s.category,
    s.status,
    s.sync_status,
    s.is_template,
    COUNT(DISTINCT m.member_id) as member_count,
    COUNT(DISTINCT m.member_id) FILTER (WHERE m.is_required = TRUE) as required_member_count,
    COUNT(DISTINCT m.member_id) FILTER (WHERE m.exists = TRUE) as found_member_count,
    COUNT(DISTINCT m.member_id) FILTER (WHERE m.exists = FALSE AND m.is_required = TRUE) as missing_required_count,
    COUNT(DISTINCT r.rule_id) as rule_count,
    COUNT(DISTINCT r.rule_id) FILTER (WHERE r.is_active = TRUE) as active_rule_count,
    COUNT(DISTINCT v.violation_id) as total_violations,
    COUNT(DISTINCT v.violation_id) FILTER (WHERE v.status = 'open') as open_violations,
    COUNT(DISTINCT v.violation_id) FILTER (WHERE v.severity = 'critical') as critical_violations,
    s.last_checked_at,
    s.created_at,
    s.updated_at
FROM project_relationship_sets s
LEFT JOIN project_relationship_members m ON s.set_id = m.set_id
LEFT JOIN project_relationship_rules r ON s.set_id = r.set_id
LEFT JOIN project_relationship_violations v ON s.set_id = v.set_id
GROUP BY s.set_id, s.project_id, s.set_name, s.set_code, s.category, 
         s.status, s.sync_status, s.is_template, s.last_checked_at, 
         s.created_at, s.updated_at;

COMMENT ON VIEW vw_relationship_set_summary IS 'Summary statistics for each relationship set';


-- Helper Function: Update Set Sync Status
CREATE OR REPLACE FUNCTION update_relationship_set_sync_status(p_set_id UUID)
RETURNS VOID AS $$
DECLARE
    v_open_violations INTEGER;
    v_missing_required INTEGER;
    v_total_required INTEGER;
    v_new_status VARCHAR(50);
BEGIN
    -- Count open violations
    SELECT COUNT(*) INTO v_open_violations
    FROM project_relationship_violations
    WHERE set_id = p_set_id AND status = 'open';
    
    -- Count missing required members
    SELECT 
        COUNT(*) FILTER (WHERE exists = FALSE AND is_required = TRUE),
        COUNT(*) FILTER (WHERE is_required = TRUE)
    INTO v_missing_required, v_total_required
    FROM project_relationship_members
    WHERE set_id = p_set_id;
    
    -- Determine sync status
    IF v_total_required = 0 THEN
        v_new_status := 'incomplete';  -- No required members defined
    ELSIF v_missing_required > 0 THEN
        v_new_status := 'incomplete';  -- Missing required elements
    ELSIF v_open_violations > 0 THEN
        v_new_status := 'out_of_sync';  -- Has open violations
    ELSE
        v_new_status := 'in_sync';  -- All good
    END IF;
    
    -- Update set
    UPDATE project_relationship_sets
    SET 
        sync_status = v_new_status,
        violation_count = v_open_violations,
        last_checked_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE set_id = p_set_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_relationship_set_sync_status IS 'Recalculates and updates the sync status of a relationship set';


-- Trigger: Auto-update sync status when violations change
CREATE OR REPLACE FUNCTION trg_update_set_sync_status()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM update_relationship_set_sync_status(OLD.set_id);
    ELSE
        PERFORM update_relationship_set_sync_status(NEW.set_id);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_violations_update_sync
AFTER INSERT OR UPDATE OR DELETE ON project_relationship_violations
FOR EACH ROW EXECUTE FUNCTION trg_update_set_sync_status();

CREATE TRIGGER trg_members_update_sync
AFTER INSERT OR UPDATE OR DELETE ON project_relationship_members
FOR EACH ROW EXECUTE FUNCTION trg_update_set_sync_status();
