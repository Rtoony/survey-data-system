-- Migration 035: Create Survey Point Description Standards
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Create controlled vocabulary for survey point descriptions (EP, TW, BC, etc.)
-- Prevents inconsistent entry like "EP" vs "Edge Pavement" vs "edge pave"

-- ============================================================================
-- SURVEY POINT DESCRIPTION STANDARDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS survey_point_description_standards (
    description_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID,

    -- Core identification
    description_code VARCHAR(20) NOT NULL UNIQUE,
    description_text VARCHAR(200) NOT NULL,
    description_full TEXT,

    -- Classification
    category VARCHAR(100) NOT NULL,                    -- 'Pavement', 'Utility', 'Structure', 'Vegetation', 'Terrain', 'Control'
    subcategory VARCHAR(100),
    feature_type VARCHAR(100),                         -- 'Point', 'Line', 'Area'

    -- CAD representation
    point_code VARCHAR(50),                            -- Links to survey_code_library
    cad_layer_name VARCHAR(100),                       -- Suggested layer name
    cad_symbol VARCHAR(100),                           -- Block name for visualization
    color_hex VARCHAR(7) DEFAULT '#00FF00',            -- Green for topo points

    -- Metadata
    is_control_point BOOLEAN DEFAULT false,            -- Is this a control/benchmark type?
    typical_accuracy VARCHAR(50),                      -- Expected accuracy level
    requires_elevation BOOLEAN DEFAULT true,           -- Does this feature require Z value?

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

DROP TRIGGER IF EXISTS trigger_update_survey_desc_timestamp ON survey_point_description_standards;
CREATE TRIGGER trigger_update_survey_desc_timestamp
    BEFORE UPDATE ON survey_point_description_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_survey_desc_timestamp();

-- ============================================================================
-- SEED DATA - Standard Survey Point Descriptions
-- ============================================================================

INSERT INTO survey_point_description_standards
(description_code, description_text, description_full, category, subcategory, feature_type, point_code, cad_symbol, color_hex, is_control_point, requires_elevation)
VALUES

-- PAVEMENT FEATURES
('EP', 'Edge of Pavement', 'Edge of paved surface (asphalt or concrete)', 'Pavement', 'Edges', 'Line', 'EP', 'POINT', '#FF0000', false, true),
('CL', 'Centerline', 'Centerline of roadway or lane', 'Pavement', 'Centerlines', 'Line', 'CL', 'POINT', '#FFFF00', false, true),
('PC', 'Pavement Crown', 'High point of pavement cross-slope', 'Pavement', 'Profiles', 'Point', 'PC', 'POINT', '#FFA500', false, true),
('CRACK', 'Pavement Crack', 'Crack in pavement surface', 'Pavement', 'Condition', 'Line', 'CRACK', 'X-MARK', '#FF0000', false, false),
('STRIPE', 'Pavement Stripe', 'Painted pavement marking', 'Pavement', 'Markings', 'Line', 'STRIPE', 'POINT', '#FFFFFF', false, false),

-- CURB & GUTTER
('FG', 'Face of Curb', 'Face of vertical curb', 'Curb & Gutter', 'Vertical', 'Line', 'FG', 'POINT', '#00FFFF', false, true),
('BC', 'Back of Curb', 'Back edge of curb', 'Curb & Gutter', 'Edges', 'Line', 'BC', 'POINT', '#00FFFF', false, true),
('TG', 'Top of Gutter', 'Top edge of gutter pan', 'Curb & Gutter', 'Edges', 'Line', 'TG', 'POINT', '#00FF00', false, true),
('FL', 'Flowline', 'Low point of gutter or drainage path', 'Curb & Gutter', 'Drainage', 'Line', 'FL', 'POINT', '#0000FF', false, true),

-- STRUCTURES & WALLS
('TW', 'Top of Wall', 'Top of retaining wall or similar structure', 'Structures', 'Walls', 'Line', 'TW', 'POINT', '#A52A2A', false, true),
('BW', 'Bottom of Wall', 'Base/toe of wall', 'Structures', 'Walls', 'Line', 'BW', 'POINT', '#8B4513', false, true),
('FW', 'Face of Wall', 'Face of wall (vertical surface)', 'Structures', 'Walls', 'Line', 'FW', 'POINT', '#CD853F', false, true),
('BLDG', 'Building Corner', 'Corner of building or structure', 'Structures', 'Buildings', 'Point', 'BLDG', 'SQUARE', '#FF00FF', false, true),
('FENCE', 'Fence Line', 'Chain link, wood, or other fence', 'Structures', 'Fences', 'Line', 'FENCE', 'POINT', '#808080', false, false),

-- UTILITIES
('MH', 'Manhole', 'Utility manhole (storm, sewer, etc.)', 'Utilities', 'Structures', 'Point', 'MH', 'CIRCLE-FILLED', '#00BCD4', false, true),
('CB', 'Catch Basin', 'Storm drain catch basin', 'Utilities', 'Storm', 'Point', 'CB', 'SQUARE', '#0000FF', false, true),
('WV', 'Water Valve', 'Water distribution valve', 'Utilities', 'Water', 'Point', 'WV', 'VALVE', '#00BFFF', false, true),
('HYDRANT', 'Fire Hydrant', 'Fire hydrant', 'Utilities', 'Water', 'Point', 'HYDRANT', 'HYDRANT', '#FF0000', false, true),
('POLE', 'Utility Pole', 'Electric, telephone, or other utility pole', 'Utilities', 'Overhead', 'Point', 'POLE', 'CIRCLE', '#FFD700', false, false),

-- VEGETATION
('TREE', 'Tree Trunk', 'Tree trunk at DBH height', 'Vegetation', 'Trees', 'Point', 'TREE', 'TREE', '#228B22', false, false),
('CANOPY', 'Tree Canopy Edge', 'Drip line / canopy extent', 'Vegetation', 'Trees', 'Line', 'CANOPY', 'POINT', '#90EE90', false, false),
('SHRUB', 'Shrub', 'Shrub or bush', 'Vegetation', 'Shrubs', 'Point', 'SHRUB', 'X-MARK', '#32CD32', false, false),

-- TERRAIN
('TOB', 'Top of Bank', 'Top edge of slope or creek bank', 'Terrain', 'Slopes', 'Line', 'TOB', 'POINT', '#8B4513', false, true),
('BOB', 'Bottom of Bank', 'Toe of slope or creek bottom', 'Terrain', 'Slopes', 'Line', 'BOB', 'POINT', '#654321', false, true),
('TOS', 'Top of Slope', 'Top of designed or natural slope', 'Terrain', 'Slopes', 'Line', 'TOS', 'POINT', '#D2691E', false, true),
('BOS', 'Bottom of Slope', 'Toe of designed or natural slope', 'Terrain', 'Slopes', 'Line', 'BOS', 'POINT', '#8B7355', false, true),
('TOPO', 'Topographic Point', 'General ground surface point', 'Terrain', 'Surface', 'Point', 'TOPO', 'POINT', '#00FF00', false, true),

-- CONTROL POINTS
('BENCHMARK', 'Benchmark', 'Vertical control monument', 'Control', 'Vertical', 'Point', 'BM', 'BENCHMARK', '#FF0000', true, true),
('CONTROL', 'Control Point', 'Horizontal/3D control monument', 'Control', 'Horizontal', 'Point', 'CTRL', 'CONTROL', '#FF00FF', true, true),
('MONUMENT', 'Survey Monument', 'Property corner monument', 'Control', 'Property', 'Point', 'MON', 'MONUMENT', '#FFD700', true, true),

-- ADDITIONAL COMMON CODES
('SIGN', 'Sign Post', 'Traffic or informational sign', 'Structures', 'Signs', 'Point', 'SIGN', 'SIGN', '#FFFF00', false, false),
('LP', 'Light Post', 'Street light or parking lot light', 'Utilities', 'Lighting', 'Point', 'LP', 'CIRCLE', '#FFFF00', false, false),
('INLET', 'Storm Inlet', 'Storm water inlet structure', 'Utilities', 'Storm', 'Point', 'INLET', 'SQUARE', '#0066CC', false, true)

ON CONFLICT (description_code) DO NOTHING;

-- Verify seed data
DO $$
DECLARE
    record_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM survey_point_description_standards;
    RAISE NOTICE 'Survey point description standards table created with % records', record_count;
END $$;
