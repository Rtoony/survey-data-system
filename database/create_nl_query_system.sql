-- ============================================================================
-- Natural Language Query System
-- ============================================================================
-- Purpose: Store and manage natural language queries and their SQL translations
-- Enables users to query CAD/GIS data using plain English
-- ============================================================================

CREATE TABLE IF NOT EXISTS nl_query_history (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User query
    natural_language_query TEXT NOT NULL,

    -- LLM processing
    generated_sql TEXT,
    sql_explanation TEXT,
    model_used VARCHAR(100) DEFAULT 'gpt-4',
    tokens_used INTEGER,
    processing_time_ms INTEGER,

    -- Execution results
    execution_status VARCHAR(50) DEFAULT 'pending',   -- 'pending', 'success', 'error', 'timeout'
    result_count INTEGER,
    execution_time_ms INTEGER,
    error_message TEXT,

    -- Query classification
    query_intent VARCHAR(100),                        -- 'select', 'count', 'aggregate', 'spatial', 'complex'
    tables_accessed JSONB DEFAULT '[]'::jsonb,        -- Array of table names
    complexity_score NUMERIC(3, 2),                   -- 0.0 - 1.0 rating

    -- User interaction
    user_feedback VARCHAR(50),                        -- 'helpful', 'not_helpful', 'incorrect'
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_comment TEXT,
    is_favorite BOOLEAN DEFAULT false,

    -- Sharing and templates
    is_template BOOLEAN DEFAULT false,
    template_name VARCHAR(200),
    template_description TEXT,
    template_parameters JSONB,                        -- For parameterized queries
    is_public BOOLEAN DEFAULT false,

    -- Security and audit
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_nl_query_created ON nl_query_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_nl_query_user ON nl_query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_nl_query_status ON nl_query_history(execution_status);
CREATE INDEX IF NOT EXISTS idx_nl_query_favorites ON nl_query_history(is_favorite) WHERE is_favorite = true;
CREATE INDEX IF NOT EXISTS idx_nl_query_templates ON nl_query_history(is_template) WHERE is_template = true;
CREATE INDEX IF NOT EXISTS idx_nl_query_intent ON nl_query_history(query_intent);

-- Full-text search on queries
CREATE INDEX IF NOT EXISTS idx_nl_query_fulltext ON nl_query_history USING gin(to_tsvector('english', natural_language_query));

-- Comments
COMMENT ON TABLE nl_query_history IS 'Natural language query history with LLM-generated SQL translations';
COMMENT ON COLUMN nl_query_history.natural_language_query IS 'User input in plain English (e.g., "Show me all storm drains within 100 feet of residential parcels")';
COMMENT ON COLUMN nl_query_history.generated_sql IS 'LLM-generated SQL query from natural language input';
COMMENT ON COLUMN nl_query_history.sql_explanation IS 'Human-readable explanation of what the SQL does';
COMMENT ON COLUMN nl_query_history.query_intent IS 'Classification of query type for analytics and optimization';
COMMENT ON COLUMN nl_query_history.complexity_score IS 'Estimated query complexity (0=simple SELECT, 1=complex multi-table join)';
COMMENT ON COLUMN nl_query_history.is_template IS 'Can this query be reused as a template with parameters?';

-- Update trigger
CREATE OR REPLACE FUNCTION update_nl_query_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_nl_query_timestamp
    BEFORE UPDATE ON nl_query_history
    FOR EACH ROW
    EXECUTE FUNCTION update_nl_query_timestamp();


-- ============================================================================
-- Query Templates (for common/saved queries)
-- ============================================================================

CREATE TABLE IF NOT EXISTS nl_query_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Template metadata
    template_name VARCHAR(200) NOT NULL,
    template_description TEXT,
    category VARCHAR(100),                            -- 'Utilities', 'Survey', 'Compliance', 'Spatial'

    -- Template query
    natural_language_template TEXT NOT NULL,
    sql_template TEXT NOT NULL,
    sql_explanation TEXT,

    -- Parameters (for dynamic values)
    parameters JSONB DEFAULT '[]'::jsonb,             -- [{"name": "distance", "type": "number", "default": 100}]
    example_values JSONB,                             -- Example parameter values for testing

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    avg_execution_time_ms INTEGER,
    avg_result_count INTEGER,

    -- Metadata
    tags JSONB DEFAULT '[]'::jsonb,
    is_featured BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_nl_templates_category ON nl_query_templates(category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_nl_templates_featured ON nl_query_templates(is_featured) WHERE is_featured = true;
CREATE INDEX IF NOT EXISTS idx_nl_templates_usage ON nl_query_templates(usage_count DESC);

-- Full-text search on templates
CREATE INDEX IF NOT EXISTS idx_nl_templates_fulltext ON nl_query_templates USING gin(
    to_tsvector('english', template_name || ' ' || COALESCE(template_description, '') || ' ' || natural_language_template)
);

-- Comments
COMMENT ON TABLE nl_query_templates IS 'Reusable query templates for common natural language queries';
COMMENT ON COLUMN nl_query_templates.parameters IS 'JSON array of parameter definitions with name, type, default value';
COMMENT ON COLUMN nl_query_templates.sql_template IS 'SQL with placeholders like {distance}, {project_id}, etc.';

-- Update trigger
CREATE TRIGGER trigger_update_nl_template_timestamp
    BEFORE UPDATE ON nl_query_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_nl_query_timestamp();
