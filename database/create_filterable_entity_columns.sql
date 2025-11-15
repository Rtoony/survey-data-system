-- Filterable Entity Columns Registry
-- Part of Reference Data Hub
-- Defines which columns can be used for filtering in Project Relationship Sets

CREATE TABLE IF NOT EXISTS filterable_entity_columns (
    column_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entity linkage
    entity_type VARCHAR(100) NOT NULL,
    entity_table VARCHAR(100) NOT NULL,
    
    -- Column metadata
    column_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('text', 'numeric', 'date', 'boolean', 'uuid')),
    
    -- Operator configuration
    operators_supported JSONB NOT NULL DEFAULT '["equals"]'::jsonb,
    
    -- Optional vocabulary linkage
    vocabulary_link VARCHAR(200),
    
    -- Documentation
    description TEXT,
    help_text TEXT,
    
    -- UI configuration
    sort_order INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    -- Constraints
    UNIQUE(entity_type, column_name)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_filterable_columns_entity ON filterable_entity_columns(entity_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_filterable_columns_active ON filterable_entity_columns(is_active);

-- Comments
COMMENT ON TABLE filterable_entity_columns IS 'Registry of columns available for filtering in Project Relationship Sets - authoritative source for filter UI';
COMMENT ON COLUMN filterable_entity_columns.entity_type IS 'Entity type identifier (e.g., utility_line, bmp)';
COMMENT ON COLUMN filterable_entity_columns.entity_table IS 'Actual database table name (e.g., utility_lines, bmps)';
COMMENT ON COLUMN filterable_entity_columns.column_name IS 'Database column name used in WHERE clauses';
COMMENT ON COLUMN filterable_entity_columns.display_name IS 'Human-readable column name shown in UI';
COMMENT ON COLUMN filterable_entity_columns.data_type IS 'Data type category for operator validation';
COMMENT ON COLUMN filterable_entity_columns.operators_supported IS 'JSON array of supported operators: ["equals", "gt", "gte", "lt", "lte", "like", "in"]';
COMMENT ON COLUMN filterable_entity_columns.vocabulary_link IS 'Optional reference to controlled vocabulary table/field';

-- Update trigger
CREATE OR REPLACE FUNCTION update_filterable_columns_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_filterable_columns_timestamp
    BEFORE UPDATE ON filterable_entity_columns
    FOR EACH ROW
    EXECUTE FUNCTION update_filterable_columns_timestamp();
