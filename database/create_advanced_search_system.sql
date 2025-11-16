-- ============================================================================
-- Advanced Search & Filtering System
-- Enables faceted search across all entity types with saved templates
-- ============================================================================

-- Saved Search Templates
-- Stores user-defined search configurations for reuse
CREATE TABLE IF NOT EXISTS saved_search_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(255) NOT NULL,
    template_description TEXT,

    -- Search Configuration
    entity_type VARCHAR(100) NOT NULL, -- 'utility_structures', 'survey_points', 'utility_lines', 'projects', etc.
    filter_config JSONB NOT NULL, -- Complete filter configuration as JSON

    -- Facet Configuration
    enabled_facets JSONB, -- Which facets to show: ['category', 'material', 'date_range', etc.]
    default_sort VARCHAR(100), -- Default sort field and direction

    -- Display Configuration
    visible_columns JSONB, -- Which columns to show in results
    results_per_page INTEGER DEFAULT 50,

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,

    -- Sharing and Access
    is_public BOOLEAN DEFAULT FALSE,
    is_system_template BOOLEAN DEFAULT FALSE, -- Pre-built templates

    -- Organization
    category VARCHAR(100), -- 'Quality Control', 'Inventory', 'Compliance', etc.
    tags JSONB, -- ['qa', 'spatial', 'temporal']

    is_active BOOLEAN DEFAULT TRUE
);

-- Search History
-- Tracks all search executions for analytics and quick re-run
CREATE TABLE IF NOT EXISTS search_history (
    search_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Search Details
    template_id UUID REFERENCES saved_search_templates(template_id),
    entity_type VARCHAR(100) NOT NULL,
    filter_config JSONB NOT NULL,

    -- Execution Results
    result_count INTEGER,
    execution_time_ms INTEGER,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- User Context
    executed_by VARCHAR(255),
    search_context TEXT, -- Free-form notes about why this search was run

    -- User Feedback
    was_helpful BOOLEAN,
    is_bookmarked BOOLEAN DEFAULT FALSE,

    -- Export Tracking
    exported_format VARCHAR(50), -- 'csv', 'excel', 'pdf', null if not exported
    exported_at TIMESTAMP WITH TIME ZONE
);

-- Search Facet Cache
-- Pre-computed facet values for fast filtering
CREATE TABLE IF NOT EXISTS search_facet_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    entity_type VARCHAR(100) NOT NULL,
    facet_name VARCHAR(100) NOT NULL, -- 'category', 'material', 'municipality', etc.
    facet_value VARCHAR(500) NOT NULL,
    record_count INTEGER NOT NULL,

    -- Cache Management
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,

    UNIQUE(entity_type, facet_name, facet_value)
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_saved_search_templates_entity_type
    ON saved_search_templates(entity_type) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_saved_search_templates_category
    ON saved_search_templates(category) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_saved_search_templates_public
    ON saved_search_templates(is_public) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_saved_search_templates_usage
    ON saved_search_templates(usage_count DESC);

CREATE INDEX IF NOT EXISTS idx_search_history_entity_type
    ON search_history(entity_type);

CREATE INDEX IF NOT EXISTS idx_search_history_executed_at
    ON search_history(executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_search_history_bookmarked
    ON search_history(is_bookmarked) WHERE is_bookmarked = TRUE;

CREATE INDEX IF NOT EXISTS idx_search_facet_cache_lookup
    ON search_facet_cache(entity_type, facet_name) WHERE is_valid = TRUE;

-- Full-text Search
CREATE INDEX IF NOT EXISTS idx_saved_search_templates_fts
    ON saved_search_templates USING gin(
        to_tsvector('english',
            COALESCE(template_name, '') || ' ' ||
            COALESCE(template_description, '') || ' ' ||
            COALESCE(category, '')
        )
    );

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_saved_search_templates_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_saved_search_templates_timestamp
    BEFORE UPDATE ON saved_search_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_saved_search_templates_timestamp();

-- Trigger to track usage
CREATE OR REPLACE FUNCTION track_search_template_usage()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.template_id IS NOT NULL THEN
        UPDATE saved_search_templates
        SET usage_count = usage_count + 1,
            last_used_at = CURRENT_TIMESTAMP
        WHERE template_id = NEW.template_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_track_search_template_usage
    AFTER INSERT ON search_history
    FOR EACH ROW
    EXECUTE FUNCTION track_search_template_usage();

-- Function to rebuild facet cache for an entity type
CREATE OR REPLACE FUNCTION rebuild_facet_cache(p_entity_type VARCHAR)
RETURNS INTEGER AS $$
DECLARE
    v_rows_updated INTEGER := 0;
BEGIN
    -- Mark existing cache as invalid
    UPDATE search_facet_cache
    SET is_valid = FALSE
    WHERE entity_type = p_entity_type;

    -- Rebuild based on entity type
    -- This is a template - actual implementation would query real tables

    IF p_entity_type = 'utility_structures' THEN
        -- Category facet
        INSERT INTO search_facet_cache (entity_type, facet_name, facet_value, record_count)
        SELECT
            'utility_structures',
            'structure_type',
            COALESCE(sts.type_name, us.structure_type, 'Unknown'),
            COUNT(*)
        FROM utility_structures us
        LEFT JOIN structure_type_standards sts ON us.structure_type_id = sts.type_id
        WHERE us.is_active = TRUE
        GROUP BY COALESCE(sts.type_name, us.structure_type, 'Unknown')
        ON CONFLICT (entity_type, facet_name, facet_value)
        DO UPDATE SET
            record_count = EXCLUDED.record_count,
            last_updated = CURRENT_TIMESTAMP,
            is_valid = TRUE;

        GET DIAGNOSTICS v_rows_updated = ROW_COUNT;
    END IF;

    RETURN v_rows_updated;
END;
$$ LANGUAGE plpgsql;
