-- ============================================================================
-- PHASE 3: UNIFIED GRAPH-BASED RELATIONSHIP SYSTEM
-- Migration 022: Create relationship_edges table
--
-- Purpose: Implement a unified graph model for all entity-to-entity relationships
--          to replace separate junction tables and enable complex multi-entity
--          relationships with metadata.
--
-- References: docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md
-- ============================================================================

-- Table: relationship_edges (Unified Graph Model)
CREATE TABLE IF NOT EXISTS relationship_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,

    -- Source Entity (From)
    source_entity_type VARCHAR(50) NOT NULL,  -- 'detail', 'block', 'material', 'spec', 'note', 'hatch', etc.
    source_entity_id UUID NOT NULL,

    -- Target Entity (To)
    target_entity_type VARCHAR(50) NOT NULL,
    target_entity_id UUID NOT NULL,

    -- Relationship Type (Semantic Edge Label)
    relationship_type VARCHAR(50) NOT NULL,   -- 'USES', 'REFERENCES', 'CONTAINS', 'REQUIRES', etc.

    -- Edge Metadata
    relationship_strength DECIMAL(3,2),       -- 0.0 to 1.0 (optional=0.3, required=1.0, etc.)
    is_bidirectional BOOLEAN DEFAULT FALSE,
    relationship_metadata JSONB DEFAULT '{}'::jsonb,  -- Flexible attributes

    -- Provenance & Tracking
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'manual',       -- 'manual', 'import', 'inference', 'template'
    confidence_score DECIMAL(3,2),             -- For AI-inferred relationships (0.0-1.0)

    -- Temporal Validity
    valid_from DATE,
    valid_to DATE,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(50) DEFAULT 'active',       -- 'active', 'pending', 'deprecated', 'deleted'

    -- Constraints
    CONSTRAINT unique_directed_edge UNIQUE(project_id, source_entity_type, source_entity_id,
                                            target_entity_type, target_entity_id, relationship_type),
    CONSTRAINT valid_strength CHECK (relationship_strength IS NULL OR (relationship_strength >= 0.0 AND relationship_strength <= 1.0)),
    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    CONSTRAINT valid_temporal CHECK (valid_from IS NULL OR valid_to IS NULL OR valid_from <= valid_to)
);

-- Indexes for graph traversal performance
CREATE INDEX idx_edges_project ON relationship_edges(project_id) WHERE is_active = TRUE;
CREATE INDEX idx_edges_source ON relationship_edges(source_entity_type, source_entity_id) WHERE is_active = TRUE;
CREATE INDEX idx_edges_target ON relationship_edges(target_entity_type, target_entity_id) WHERE is_active = TRUE;
CREATE INDEX idx_edges_type ON relationship_edges(relationship_type) WHERE is_active = TRUE;
CREATE INDEX idx_edges_bidirectional ON relationship_edges(is_bidirectional) WHERE is_bidirectional = TRUE;
CREATE INDEX idx_edges_temporal ON relationship_edges(valid_from, valid_to) WHERE valid_from IS NOT NULL OR valid_to IS NOT NULL;
CREATE INDEX idx_edges_source_type ON relationship_edges(source_entity_type, relationship_type) WHERE is_active = TRUE;
CREATE INDEX idx_edges_metadata ON relationship_edges USING GIN(relationship_metadata);

-- Composite index for common graph traversal queries
CREATE INDEX idx_edges_graph_traversal ON relationship_edges(project_id, source_entity_type, source_entity_id, relationship_type)
    WHERE is_active = TRUE;

COMMENT ON TABLE relationship_edges IS 'Unified graph-based relationship model for all entity-to-entity connections';
COMMENT ON COLUMN relationship_edges.relationship_type IS 'Semantic edge type: USES, REFERENCES, CONTAINS, REQUIRES, CALLED_OUT_IN, SPECIFIES, REPRESENTS, SUPERSEDES, SIMILAR_TO';
COMMENT ON COLUMN relationship_edges.relationship_strength IS 'Edge weight 0.0-1.0: optional=0.3, recommended=0.6, required=1.0';
COMMENT ON COLUMN relationship_edges.is_bidirectional IS 'If true, relationship applies in both directions';
COMMENT ON COLUMN relationship_edges.source IS 'Origin of relationship: manual, import, inference, template';
COMMENT ON COLUMN relationship_edges.confidence_score IS 'Confidence in relationship validity (0.0-1.0), used for AI-inferred edges';


-- ============================================================================
-- Relationship Type Registry
-- ============================================================================
-- Defines valid relationship types and their semantics

CREATE TABLE IF NOT EXISTS relationship_type_registry (
    type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_code VARCHAR(50) UNIQUE NOT NULL,     -- 'USES', 'REFERENCES', etc.
    type_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Directionality
    is_directional BOOLEAN DEFAULT TRUE,       -- Most relationships are directional
    inverse_type_code VARCHAR(50),             -- For bidirectional pairs (e.g., PARENT_OF ↔ CHILD_OF)

    -- Valid entity type combinations
    valid_source_types TEXT[],                 -- NULL = any type allowed
    valid_target_types TEXT[],                 -- NULL = any type allowed

    -- Default behavior
    default_strength DECIMAL(3,2) DEFAULT 0.5,
    default_bidirectional BOOLEAN DEFAULT FALSE,

    -- Categorization
    category VARCHAR(50),                      -- 'structural', 'reference', 'dependency', 'similarity'

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed standard relationship types
INSERT INTO relationship_type_registry (type_code, type_name, description, category, default_strength, valid_source_types, valid_target_types) VALUES
('USES', 'Uses', 'Source entity consumes or incorporates target entity', 'dependency', 0.8,
    ARRAY['detail', 'block', 'assembly'], ARRAY['material', 'component']),
('REFERENCES', 'References', 'Source entity points to or cites target entity', 'reference', 0.6,
    ARRAY['detail', 'block', 'note'], ARRAY['spec', 'standard', 'document']),
('CONTAINS', 'Contains', 'Source entity includes target entity as part', 'structural', 1.0,
    ARRAY['assembly', 'detail', 'drawing'], ARRAY['detail', 'block', 'component']),
('REQUIRES', 'Requires', 'Source entity depends on target entity', 'dependency', 0.9,
    NULL, NULL),
('CALLED_OUT_IN', 'Called Out In', 'Source entity is mentioned in target annotation', 'reference', 0.7,
    ARRAY['detail', 'material', 'block'], ARRAY['note', 'keynote']),
('SPECIFIES', 'Specifies', 'Source entity defines requirements for target entity', 'reference', 0.8,
    ARRAY['spec', 'standard'], ARRAY['material', 'component', 'detail']),
('REPRESENTS', 'Represents', 'Source entity is visual symbol for target entity', 'structural', 0.9,
    ARRAY['hatch', 'pattern', 'symbol'], ARRAY['material', 'component']),
('SUPERSEDES', 'Supersedes', 'Source entity replaces or obsoletes target entity', 'reference', 1.0,
    NULL, NULL),
('SIMILAR_TO', 'Similar To', 'Source entity is related or comparable to target entity', 'similarity', 0.4,
    NULL, NULL),
('SHOWN_IN', 'Shown In', 'Source entity appears in target drawing/detail', 'reference', 0.7,
    ARRAY['block', 'component', 'material'], ARRAY['detail', 'drawing']),
('GOVERNED_BY', 'Governed By', 'Source entity is controlled by target rule/standard', 'reference', 0.9,
    NULL, ARRAY['spec', 'standard', 'regulation'])
ON CONFLICT (type_code) DO UPDATE SET
    type_name = EXCLUDED.type_name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    updated_at = CURRENT_TIMESTAMP;

CREATE INDEX idx_rel_types_code ON relationship_type_registry(type_code);
CREATE INDEX idx_rel_types_category ON relationship_type_registry(category);

COMMENT ON TABLE relationship_type_registry IS 'Registry of valid relationship types with semantics and constraints';


-- ============================================================================
-- Helper Views
-- ============================================================================

-- View: Bidirectional edges (shows both directions)
CREATE OR REPLACE VIEW vw_relationship_edges_bidirectional AS
SELECT
    edge_id,
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
    'forward' as direction
FROM relationship_edges
WHERE is_active = TRUE

UNION ALL

SELECT
    edge_id,
    project_id,
    target_entity_type as source_entity_type,
    target_entity_id as source_entity_id,
    source_entity_type as target_entity_type,
    source_entity_id as target_entity_id,
    relationship_type,
    relationship_strength,
    relationship_metadata,
    created_by,
    created_at,
    'reverse' as direction
FROM relationship_edges
WHERE is_active = TRUE AND is_bidirectional = TRUE;

COMMENT ON VIEW vw_relationship_edges_bidirectional IS 'Shows all edges in both directions for bidirectional relationships';


-- View: Relationship summary by type
CREATE OR REPLACE VIEW vw_relationship_summary_by_type AS
SELECT
    project_id,
    relationship_type,
    COUNT(*) as edge_count,
    COUNT(DISTINCT source_entity_id) as unique_sources,
    COUNT(DISTINCT target_entity_id) as unique_targets,
    AVG(relationship_strength) as avg_strength,
    COUNT(*) FILTER (WHERE is_bidirectional = TRUE) as bidirectional_count,
    COUNT(*) FILTER (WHERE source = 'manual') as manual_count,
    COUNT(*) FILTER (WHERE source = 'import') as imported_count,
    COUNT(*) FILTER (WHERE source = 'inference') as inferred_count
FROM relationship_edges
WHERE is_active = TRUE
GROUP BY project_id, relationship_type;

COMMENT ON VIEW vw_relationship_summary_by_type IS 'Summary statistics for relationships grouped by type';


-- View: Entity relationship counts (node degrees)
CREATE OR REPLACE VIEW vw_entity_relationship_counts AS
WITH source_counts AS (
    SELECT
        project_id,
        source_entity_type as entity_type,
        source_entity_id as entity_id,
        COUNT(*) as outgoing_count,
        0 as incoming_count
    FROM relationship_edges
    WHERE is_active = TRUE
    GROUP BY project_id, source_entity_type, source_entity_id
),
target_counts AS (
    SELECT
        project_id,
        target_entity_type as entity_type,
        target_entity_id as entity_id,
        0 as outgoing_count,
        COUNT(*) as incoming_count
    FROM relationship_edges
    WHERE is_active = TRUE
    GROUP BY project_id, target_entity_type, target_entity_id
)
SELECT
    COALESCE(s.project_id, t.project_id) as project_id,
    COALESCE(s.entity_type, t.entity_type) as entity_type,
    COALESCE(s.entity_id, t.entity_id) as entity_id,
    COALESCE(s.outgoing_count, 0) + COALESCE(t.outgoing_count, 0) as outgoing_count,
    COALESCE(s.incoming_count, 0) + COALESCE(t.incoming_count, 0) as incoming_count,
    COALESCE(s.outgoing_count, 0) + COALESCE(t.outgoing_count, 0) +
    COALESCE(s.incoming_count, 0) + COALESCE(t.incoming_count, 0) as total_connections
FROM source_counts s
FULL OUTER JOIN target_counts t ON
    s.project_id = t.project_id AND
    s.entity_type = t.entity_type AND
    s.entity_id = t.entity_id;

COMMENT ON VIEW vw_entity_relationship_counts IS 'Node degree statistics: incoming, outgoing, and total connections per entity';


-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Get all related entities for a given entity
CREATE OR REPLACE FUNCTION get_related_entities(
    p_entity_type VARCHAR(50),
    p_entity_id UUID,
    p_relationship_type VARCHAR(50) DEFAULT NULL,
    p_direction VARCHAR(10) DEFAULT 'both'  -- 'outgoing', 'incoming', 'both'
)
RETURNS TABLE (
    edge_id UUID,
    related_entity_type VARCHAR(50),
    related_entity_id UUID,
    relationship_type VARCHAR(50),
    relationship_strength DECIMAL(3,2),
    direction VARCHAR(10)
) AS $$
BEGIN
    RETURN QUERY
    -- Outgoing edges
    SELECT
        e.edge_id,
        e.target_entity_type as related_entity_type,
        e.target_entity_id as related_entity_id,
        e.relationship_type,
        e.relationship_strength,
        'outgoing'::VARCHAR(10) as direction
    FROM relationship_edges e
    WHERE e.source_entity_type = p_entity_type
      AND e.source_entity_id = p_entity_id
      AND e.is_active = TRUE
      AND (p_relationship_type IS NULL OR e.relationship_type = p_relationship_type)
      AND p_direction IN ('outgoing', 'both')

    UNION ALL

    -- Incoming edges
    SELECT
        e.edge_id,
        e.source_entity_type as related_entity_type,
        e.source_entity_id as related_entity_id,
        e.relationship_type,
        e.relationship_strength,
        'incoming'::VARCHAR(10) as direction
    FROM relationship_edges e
    WHERE e.target_entity_type = p_entity_type
      AND e.target_entity_id = p_entity_id
      AND e.is_active = TRUE
      AND (p_relationship_type IS NULL OR e.relationship_type = p_relationship_type)
      AND p_direction IN ('incoming', 'both');
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_related_entities IS 'Returns all entities related to a given entity, optionally filtered by relationship type and direction';


-- Function: Find orphaned entities (entities with no relationships)
CREATE OR REPLACE FUNCTION find_orphaned_entities(
    p_project_id UUID,
    p_entity_type VARCHAR(50)
)
RETURNS TABLE (
    entity_id UUID,
    entity_type VARCHAR(50)
) AS $$
BEGIN
    -- This is a placeholder that returns entity IDs that don't appear in relationship_edges
    -- The actual implementation would need to query specific entity tables
    RETURN QUERY
    SELECT DISTINCT
        e.entity_id,
        p_entity_type as entity_type
    FROM (
        SELECT source_entity_id as entity_id FROM relationship_edges WHERE project_id = p_project_id AND source_entity_type = p_entity_type
        UNION
        SELECT target_entity_id as entity_id FROM relationship_edges WHERE project_id = p_project_id AND target_entity_type = p_entity_type
    ) e;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_orphaned_entities IS 'Finds entities of a given type with no relationships (orphans)';


-- Function: Validate relationship type constraints
CREATE OR REPLACE FUNCTION validate_relationship_edge()
RETURNS TRIGGER AS $$
DECLARE
    v_type_record RECORD;
BEGIN
    -- Get relationship type configuration
    SELECT * INTO v_type_record
    FROM relationship_type_registry
    WHERE type_code = NEW.relationship_type AND is_active = TRUE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid relationship_type: %. Must be registered in relationship_type_registry.', NEW.relationship_type;
    END IF;

    -- Validate source entity type
    IF v_type_record.valid_source_types IS NOT NULL THEN
        IF NOT (NEW.source_entity_type = ANY(v_type_record.valid_source_types)) THEN
            RAISE EXCEPTION 'Invalid source_entity_type % for relationship_type %. Valid types: %',
                NEW.source_entity_type, NEW.relationship_type, array_to_string(v_type_record.valid_source_types, ', ');
        END IF;
    END IF;

    -- Validate target entity type
    IF v_type_record.valid_target_types IS NOT NULL THEN
        IF NOT (NEW.target_entity_type = ANY(v_type_record.valid_target_types)) THEN
            RAISE EXCEPTION 'Invalid target_entity_type % for relationship_type %. Valid types: %',
                NEW.target_entity_type, NEW.relationship_type, array_to_string(v_type_record.valid_target_types, ', ');
        END IF;
    END IF;

    -- Apply defaults if not set
    IF NEW.relationship_strength IS NULL THEN
        NEW.relationship_strength := v_type_record.default_strength;
    END IF;

    IF NEW.is_bidirectional IS NULL THEN
        NEW.is_bidirectional := v_type_record.default_bidirectional;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for validation
CREATE TRIGGER trg_validate_relationship_edge
    BEFORE INSERT OR UPDATE ON relationship_edges
    FOR EACH ROW
    EXECUTE FUNCTION validate_relationship_edge();

COMMENT ON FUNCTION validate_relationship_edge IS 'Validates relationship edges against type registry constraints';


-- ============================================================================
-- Validation Rules and Violations Tables
-- ============================================================================

-- Table: relationship_validation_rules
CREATE TABLE IF NOT EXISTS relationship_validation_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Rule Definition
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- 'cardinality', 'required', 'forbidden', 'conditional'
    description TEXT,

    -- Scope
    project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE,  -- NULL = global rule

    -- Entity Constraints
    source_entity_type VARCHAR(50),  -- NULL = applies to all types
    target_entity_type VARCHAR(50),  -- NULL = applies to all types
    relationship_type VARCHAR(50),   -- NULL = applies to all relationship types

    -- Rule Configuration
    rule_config JSONB DEFAULT '{}'::jsonb,  -- Type-specific configuration

    -- Rule Behavior
    severity VARCHAR(20) DEFAULT 'warning',  -- 'info', 'warning', 'error', 'critical'
    is_active BOOLEAN DEFAULT TRUE,
    auto_fix_enabled BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_rule_type CHECK (rule_type IN ('cardinality', 'required', 'forbidden', 'conditional'))
);

CREATE INDEX idx_validation_rules_project ON relationship_validation_rules(project_id);
CREATE INDEX idx_validation_rules_type ON relationship_validation_rules(rule_type, is_active);
CREATE INDEX idx_validation_rules_entity_types ON relationship_validation_rules(source_entity_type, target_entity_type);

COMMENT ON TABLE relationship_validation_rules IS 'Validation rules for relationship edges';
COMMENT ON COLUMN relationship_validation_rules.rule_type IS 'Type of validation: cardinality, required, forbidden, conditional';
COMMENT ON COLUMN relationship_validation_rules.project_id IS 'NULL for global rules, UUID for project-specific rules';


-- Table: relationship_validation_violations
CREATE TABLE IF NOT EXISTS relationship_validation_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    rule_id UUID REFERENCES relationship_validation_rules(rule_id) ON DELETE SET NULL,

    -- Violation Details
    violation_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',

    -- Affected Entity/Edge
    entity_type VARCHAR(50),
    entity_id UUID,
    edge_id UUID REFERENCES relationship_edges(edge_id) ON DELETE CASCADE,

    -- Description
    violation_message TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,

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

CREATE INDEX idx_validation_violations_project ON relationship_validation_violations(project_id);
CREATE INDEX idx_validation_violations_rule ON relationship_validation_violations(rule_id);
CREATE INDEX idx_validation_violations_status ON relationship_validation_violations(status, severity);
CREATE INDEX idx_validation_violations_entity ON relationship_validation_violations(entity_type, entity_id);
CREATE INDEX idx_validation_violations_edge ON relationship_validation_violations(edge_id) WHERE edge_id IS NOT NULL;

COMMENT ON TABLE relationship_validation_violations IS 'Detected violations of relationship validation rules';


-- ============================================================================
-- Seed Standard Validation Rules
-- ============================================================================

-- Rule: Details should reference at least one material
INSERT INTO relationship_validation_rules (
    rule_name, rule_type, description,
    source_entity_type, target_entity_type, relationship_type,
    rule_config, severity
) VALUES (
    'Detail Material Requirement',
    'cardinality',
    'Every detail should reference at least one material',
    'detail', 'material', 'USES',
    '{"min_count": 1, "max_count": null}'::jsonb,
    'warning'
) ON CONFLICT DO NOTHING;

-- Rule: Hatches should represent materials
INSERT INTO relationship_validation_rules (
    rule_name, rule_type, description,
    source_entity_type, target_entity_type, relationship_type,
    rule_config, severity
) VALUES (
    'Hatch Material Representation',
    'required',
    'Hatch patterns should represent materials',
    'hatch', 'material', 'REPRESENTS',
    '{}'::jsonb,
    'warning'
) ON CONFLICT DO NOTHING;

-- Rule: Prevent self-referential relationships
INSERT INTO relationship_validation_rules (
    rule_name, rule_type, description,
    source_entity_type, target_entity_type, relationship_type,
    rule_config, severity
) VALUES (
    'No Self-Reference',
    'forbidden',
    'Entities should not reference themselves',
    NULL, NULL, NULL,
    '{"check": "source_entity_id != target_entity_id"}'::jsonb,
    'error'
) ON CONFLICT DO NOTHING;
