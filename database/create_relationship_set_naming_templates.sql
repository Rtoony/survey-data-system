-- Relationship Set Naming Templates
-- Part of Reference Data Hub
-- Defines standard naming conventions for Project Relationship Sets
-- Enforces truth-driven architecture by preventing free-text naming

CREATE TABLE IF NOT EXISTS relationship_set_naming_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template metadata
    template_name VARCHAR(200) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    
    -- Naming formats (with token placeholders like {PROJECT_CODE}, {SYSTEM}, {SEQ})
    name_format VARCHAR(500) NOT NULL,
    short_code_format VARCHAR(200) NOT NULL,
    
    -- Documentation
    description TEXT,
    usage_instructions TEXT,
    
    -- Examples showing token replacement
    example_name VARCHAR(500),
    example_code VARCHAR(200),
    example_tokens JSONB,
    
    -- Validation rules
    required_tokens JSONB DEFAULT '[]'::jsonb,
    optional_tokens JSONB DEFAULT '[]'::jsonb,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_default BOOLEAN NOT NULL DEFAULT false,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_naming_templates_category ON relationship_set_naming_templates(category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_naming_templates_active ON relationship_set_naming_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_naming_templates_default ON relationship_set_naming_templates(is_default) WHERE is_default = true;

-- Comments
COMMENT ON TABLE relationship_set_naming_templates IS 'Standard naming templates for Project Relationship Sets - enforces truth-driven naming conventions';
COMMENT ON COLUMN relationship_set_naming_templates.template_name IS 'Unique template identifier (e.g., "Storm System Compliance")';
COMMENT ON COLUMN relationship_set_naming_templates.category IS 'Template category (e.g., "Utilities", "Compliance", "Materials")';
COMMENT ON COLUMN relationship_set_naming_templates.name_format IS 'Format string with tokens like {PROJECT_CODE}-{SYSTEM}-Compliance';
COMMENT ON COLUMN relationship_set_naming_templates.short_code_format IS 'Format string for short codes like {DISC}-{CAT}-{SEQ}';
COMMENT ON COLUMN relationship_set_naming_templates.required_tokens IS 'JSON array of required token names that must be provided';
COMMENT ON COLUMN relationship_set_naming_templates.optional_tokens IS 'JSON array of optional token names';
COMMENT ON COLUMN relationship_set_naming_templates.example_tokens IS 'JSON object showing example token values';

-- Update trigger
CREATE OR REPLACE FUNCTION update_naming_templates_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_naming_templates_timestamp
    BEFORE UPDATE ON relationship_set_naming_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_naming_templates_timestamp();

-- Ensure only one default per category
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_default_per_category 
    ON relationship_set_naming_templates(category) 
    WHERE is_default = true;
