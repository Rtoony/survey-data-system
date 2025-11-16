-- ============================================================================
-- Structure Type Standards Table
-- Part of Truth-Driven Architecture - Reference Data Hub
-- ============================================================================
-- Purpose: Controlled vocabulary for utility structure types
-- Prevents free-text entry like "Manhole" vs "MH" vs "manhole"
-- Links to specialized tools for automatic tool launching
-- ============================================================================

CREATE TABLE IF NOT EXISTS structure_type_standards (
    type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identification
    type_code VARCHAR(20) NOT NULL UNIQUE,
    type_name VARCHAR(100) NOT NULL,
    type_description TEXT,

    -- Classification
    category VARCHAR(100) NOT NULL,                    -- 'Storm Drainage', 'Sanitary Sewer', 'Water', etc.
    subcategory VARCHAR(100),

    -- Visual representation
    icon_class VARCHAR(100),                           -- Font Awesome class like 'fa-circle-dot'
    color_hex VARCHAR(7) DEFAULT '#00BCD4',           -- Default accent cyan
    symbol_name VARCHAR(100),                          -- Reference to block_definitions

    -- Tool integration
    specialized_tool_id UUID,                          -- Link to specialized_tools_registry
    specialized_tool_name VARCHAR(100),                -- Friendly tool name for UI

    -- Standard attributes
    typical_depth_range VARCHAR(50),                   -- e.g., '4-8 feet'
    typical_diameter_range VARCHAR(50),                -- e.g., '48-72 inches'
    common_materials JSONB DEFAULT '[]'::jsonb,        -- Array of typical materials: ["Concrete", "Brick", "Plastic"]
    required_attributes JSONB DEFAULT '[]'::jsonb,     -- Array of required attribute fields

    -- Compliance
    requires_inspection BOOLEAN DEFAULT false,
    inspection_frequency VARCHAR(50),                  -- 'Annual', 'Biennial', etc.
    related_standards TEXT,                            -- Reference to applicable codes/standards

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    replaced_by_type_id UUID REFERENCES structure_type_standards(type_id) ON DELETE SET NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_type_code_uppercase CHECK (type_code = UPPER(type_code)),
    CONSTRAINT check_color_format CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_structure_types_category ON structure_type_standards(category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_structure_types_active ON structure_type_standards(is_active);
CREATE INDEX IF NOT EXISTS idx_structure_types_tool ON structure_type_standards(specialized_tool_id) WHERE specialized_tool_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_structure_types_code ON structure_type_standards(type_code) WHERE is_active = true;

-- Comments
COMMENT ON TABLE structure_type_standards IS 'Controlled vocabulary for utility structure types - enforces truth-driven architecture';
COMMENT ON COLUMN structure_type_standards.type_code IS 'Unique code identifier (e.g., MH, CB, CLNOUT) - must be uppercase';
COMMENT ON COLUMN structure_type_standards.type_name IS 'Full descriptive name (e.g., Manhole, Catch Basin, Cleanout)';
COMMENT ON COLUMN structure_type_standards.category IS 'High-level category for grouping (Storm Drainage, Sanitary Sewer, etc.)';
COMMENT ON COLUMN structure_type_standards.specialized_tool_id IS 'FK to specialized_tools_registry for auto-launching management tools';
COMMENT ON COLUMN structure_type_standards.common_materials IS 'JSON array of typical materials used for this structure type';
COMMENT ON COLUMN structure_type_standards.required_attributes IS 'JSON array of required metadata fields for compliance';

-- Update trigger
CREATE OR REPLACE FUNCTION update_structure_types_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_structure_types_timestamp
    BEFORE UPDATE ON structure_type_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_structure_types_timestamp();

-- Usage tracking trigger (increment when structure is created)
CREATE OR REPLACE FUNCTION increment_structure_type_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE structure_type_standards
    SET usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE type_id = NEW.structure_type_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger will be created after utility_structures table is updated
