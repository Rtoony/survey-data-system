-- ============================================================================
-- Survey Standards Tables
-- Part of Truth-Driven Architecture - Reference Data Hub
-- ============================================================================
-- Purpose: Controlled vocabulary for survey point descriptions and methods
-- Prevents inconsistent entry like "GPS" vs "gps" vs "RTK GPS" vs "GNSS"
-- ============================================================================

-- ============================================================================
-- SURVEY POINT DESCRIPTION STANDARDS
-- ============================================================================

CREATE TABLE IF NOT EXISTS survey_point_description_standards (
    description_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identification
    description_code VARCHAR(20) NOT NULL UNIQUE,
    description_text VARCHAR(200) NOT NULL,
    description_full TEXT,

    -- Classification
    category VARCHAR(100) NOT NULL,                    -- 'Pavement', 'Utility', 'Structure', 'Vegetation', 'Terrain'
    subcategory VARCHAR(100),
    feature_type VARCHAR(100),                         -- 'Point', 'Line', 'Area'

    -- CAD representation
    point_code VARCHAR(50),                            -- Links to survey_code_library
    cad_layer_name VARCHAR(100),                       -- Suggested layer name
    cad_symbol VARCHAR(100),                           -- Block name for visualization
    color_hex VARCHAR(7) DEFAULT '#00FF00',           -- Green for topo points

    -- Metadata
    is_control_point BOOLEAN DEFAULT false,           -- Is this a control/benchmark type?
    typical_accuracy VARCHAR(50),                      -- Expected accuracy level
    requires_elevation BOOLEAN DEFAULT true,          -- Does this feature require Z value?

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    replaced_by_id UUID REFERENCES survey_point_description_standards(description_id) ON DELETE SET NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_description_code_uppercase CHECK (description_code = UPPER(description_code)),
    CONSTRAINT check_color_format_survey_desc CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_survey_desc_category ON survey_point_description_standards(category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_survey_desc_code ON survey_point_description_standards(description_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_survey_desc_active ON survey_point_description_standards(is_active);

-- Comments
COMMENT ON TABLE survey_point_description_standards IS 'Controlled vocabulary for survey point descriptions - enforces truth-driven architecture';
COMMENT ON COLUMN survey_point_description_standards.description_code IS 'Unique short code (e.g., EP, TW, BC) - must be uppercase';
COMMENT ON COLUMN survey_point_description_standards.description_text IS 'Standard description text (e.g., Edge of Pavement, Top of Wall)';
COMMENT ON COLUMN survey_point_description_standards.point_code IS 'Links to survey_code_library for field codes';
COMMENT ON COLUMN survey_point_description_standards.cad_symbol IS 'Block name for CAD visualization';

-- Update trigger
CREATE OR REPLACE FUNCTION update_survey_desc_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_survey_desc_timestamp
    BEFORE UPDATE ON survey_point_description_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_desc_timestamp();


-- ============================================================================
-- SURVEY METHOD TYPES
-- ============================================================================

CREATE TABLE IF NOT EXISTS survey_method_types (
    method_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identification
    method_code VARCHAR(20) NOT NULL UNIQUE,
    method_name VARCHAR(100) NOT NULL,
    method_description TEXT,

    -- Classification
    category VARCHAR(100) NOT NULL,                    -- 'GNSS', 'Terrestrial', 'Leveling', 'Photogrammetry'
    subcategory VARCHAR(100),

    -- Technical specifications
    equipment_type VARCHAR(100),                       -- 'RTK GPS', 'Total Station', 'Digital Level', 'Drone'
    typical_horizontal_accuracy NUMERIC(8, 4),         -- In feet
    typical_vertical_accuracy NUMERIC(8, 4),           -- In feet
    accuracy_units VARCHAR(20) DEFAULT 'Feet',
    accuracy_class VARCHAR(50),                        -- 'Survey Grade', 'Mapping Grade', 'Navigation Grade'

    -- Operational details
    requires_base_station BOOLEAN DEFAULT false,
    requires_line_of_sight BOOLEAN DEFAULT false,
    effective_range_ft NUMERIC(10, 2),
    typical_time_per_point VARCHAR(50),                -- e.g., '5-10 seconds', '1-2 minutes'

    -- Standards & compliance
    related_standards TEXT,                            -- Reference to applicable standards
    certification_required BOOLEAN DEFAULT false,

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    replaced_by_id UUID REFERENCES survey_method_types(method_id) ON DELETE SET NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_method_code_uppercase CHECK (method_code = UPPER(method_code))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_survey_method_category ON survey_method_types(category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_survey_method_code ON survey_method_types(method_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_survey_method_active ON survey_method_types(is_active);

-- Comments
COMMENT ON TABLE survey_method_types IS 'Controlled vocabulary for survey methods - enforces truth-driven architecture';
COMMENT ON COLUMN survey_method_types.method_code IS 'Unique method code (e.g., RTK-GPS, TS-ROBOTIC, LEVEL-DIGI) - must be uppercase';
COMMENT ON COLUMN survey_method_types.method_name IS 'Full method name (e.g., RTK GPS, Robotic Total Station)';
COMMENT ON COLUMN survey_method_types.typical_horizontal_accuracy IS 'Expected horizontal accuracy in feet';
COMMENT ON COLUMN survey_method_types.typical_vertical_accuracy IS 'Expected vertical accuracy in feet';
COMMENT ON COLUMN survey_method_types.accuracy_class IS 'Classification of accuracy (Survey Grade, Mapping Grade, etc.)';

-- Update trigger
CREATE OR REPLACE FUNCTION update_survey_method_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_survey_method_timestamp
    BEFORE UPDATE ON survey_method_types
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_method_timestamp();
