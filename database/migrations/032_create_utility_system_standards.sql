-- Migration 032: Create Utility System Standards Table
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Create controlled vocabulary for utility system types (STORM, SEWER, WATER, etc.)
-- Replaces free-text utility_system column with FK-backed dropdown

-- ============================================================================
-- UTILITY SYSTEM STANDARDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS utility_system_standards (
    system_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID,

    -- Core identification
    system_code VARCHAR(20) NOT NULL UNIQUE,
    system_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Classification
    category VARCHAR(50),                              -- 'Drainage', 'Potable', 'Communication', 'Energy'
    subcategory VARCHAR(50),

    -- Visual representation
    color_hex VARCHAR(7) DEFAULT '#808080',            -- Default gray
    line_style VARCHAR(50) DEFAULT 'Continuous',      -- 'Continuous', 'Dashed', 'Hidden'
    display_order INTEGER,

    -- CAD standards
    default_layer_prefix VARCHAR(50),                  -- e.g., 'STORM-', 'SEWER-'
    cad_color_index INTEGER,                          -- AutoCAD color index (1-255)

    -- Metadata
    typical_materials TEXT[],                          -- Common materials for this system
    regulatory_authority VARCHAR(100),                 -- e.g., 'EPA', 'Local Municipality'
    related_codes TEXT,                                -- Reference to applicable codes

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    replaced_by_id UUID REFERENCES utility_system_standards(system_id) ON DELETE SET NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_system_code_uppercase CHECK (system_code = UPPER(system_code)),
    CONSTRAINT check_color_format_utility_system CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$')
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_utility_system_code ON utility_system_standards(system_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_utility_system_category ON utility_system_standards(category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_utility_system_active ON utility_system_standards(is_active);

-- Comments
COMMENT ON TABLE utility_system_standards IS 'Controlled vocabulary for utility system types - enforces truth-driven architecture';
COMMENT ON COLUMN utility_system_standards.system_code IS 'Unique system code (e.g., STORM, SEWER, WATER) - must be uppercase';
COMMENT ON COLUMN utility_system_standards.system_name IS 'Full system name (e.g., Storm Drainage, Sanitary Sewer)';
COMMENT ON COLUMN utility_system_standards.color_hex IS 'Standard color for this system in hex format (#RRGGBB)';
COMMENT ON COLUMN utility_system_standards.default_layer_prefix IS 'Default CAD layer prefix for this utility system';

-- Update trigger
CREATE OR REPLACE FUNCTION update_utility_system_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_utility_system_timestamp
    BEFORE UPDATE ON utility_system_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_utility_system_timestamp();

-- ============================================================================
-- SEED DATA - Standard Utility Systems
-- ============================================================================

INSERT INTO utility_system_standards (system_code, system_name, category, color_hex, display_order, default_layer_prefix, description) VALUES
-- Drainage Systems
('STORM', 'Storm Drainage', 'Drainage', '#0066CC', 1, 'STORM-', 'Storm water drainage system including pipes, inlets, and outfalls'),
('SEWER', 'Sanitary Sewer', 'Drainage', '#8B4513', 2, 'SEWER-', 'Sanitary sewer collection system for wastewater'),

-- Water Systems
('WATER', 'Water Distribution', 'Potable', '#0099FF', 3, 'WATER-', 'Potable water distribution system including mains and services'),
('RECLAIM', 'Reclaimed Water', 'Potable', '#9933FF', 4, 'RECLAIM-', 'Reclaimed/recycled water distribution system for irrigation'),
('FIRE', 'Fire Protection', 'Potable', '#FF0000', 5, 'FIRE-', 'Fire protection water system including hydrants and sprinklers'),

-- Energy Systems
('GAS', 'Natural Gas', 'Energy', '#FFCC00', 6, 'GAS-', 'Natural gas distribution system'),
('ELECTRIC', 'Electric', 'Energy', '#FF0000', 7, 'ELEC-', 'Electrical power distribution including overhead and underground'),
('STEAM', 'Steam', 'Energy', '#FF6600', 8, 'STEAM-', 'District steam heating system'),

-- Communication Systems
('TELECOM', 'Telecommunications', 'Communication', '#00CC00', 9, 'TELE-', 'Telecommunications including fiber optic, phone, and data'),
('CABLE', 'Cable TV', 'Communication', '#00FF00', 10, 'CATV-', 'Cable television distribution system'),
('FIBER', 'Fiber Optic', 'Communication', '#00FFFF', 11, 'FIBER-', 'Fiber optic data transmission lines'),

-- Other/Special
('IRRIGATION', 'Irrigation', 'Other', '#66CC66', 12, 'IRR-', 'Irrigation water distribution system for landscaping'),
('FUEL', 'Fuel', 'Energy', '#CC6600', 13, 'FUEL-', 'Fuel distribution lines (oil, propane, etc.)'),
('COMPRESSED_AIR', 'Compressed Air', 'Other', '#CCCCCC', 14, 'AIR-', 'Compressed air distribution system'),
('UNKNOWN', 'Unknown Utility', 'Other', '#808080', 99, 'UTIL-', 'Utility system type not yet determined')
ON CONFLICT (system_code) DO NOTHING;

-- Verify seed data
DO $$
DECLARE
    record_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM utility_system_standards;
    RAISE NOTICE 'Utility system standards table created with % records', record_count;
END $$;
