-- Migration 039: Create Municipality and Owner Standards Tables
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Create controlled vocabularies for municipalities and utility owners
-- Enables FK constraints to enforce truth-driven architecture

-- ============================================================================
-- MUNICIPALITIES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS municipalities (
    municipality_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID,

    -- Core identification
    municipality_name VARCHAR(255) NOT NULL UNIQUE,
    short_name VARCHAR(50),
    municipality_code VARCHAR(20),

    -- Classification
    municipality_type VARCHAR(50),                     -- 'City', 'County', 'State Agency', 'Federal Agency', 'Special District', etc.
    county VARCHAR(100),
    state VARCHAR(2),                                  -- Two-letter state code

    -- Contact information
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    website VARCHAR(500),

    -- Address
    address VARCHAR(500),
    city VARCHAR(100),
    zip_code VARCHAR(20),

    -- Metadata
    jurisdiction_notes TEXT,
    regulatory_authority TEXT,                         -- Description of authority/jurisdiction

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_municipalities_name ON municipalities(municipality_name) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_municipalities_type ON municipalities(municipality_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_municipalities_state ON municipalities(state);
CREATE INDEX IF NOT EXISTS idx_municipalities_active ON municipalities(is_active);

-- Comments
COMMENT ON TABLE municipalities IS 'Controlled vocabulary for municipalities and jurisdictions - enforces truth-driven architecture';
COMMENT ON COLUMN municipalities.municipality_name IS 'Official municipality name (e.g., City of San Jose, Santa Clara County)';
COMMENT ON COLUMN municipalities.municipality_type IS 'Type of jurisdiction (City, County, State Agency, etc.)';
COMMENT ON COLUMN municipalities.state IS 'Two-letter state code (e.g., CA, TX, NY)';

-- Update trigger
CREATE OR REPLACE FUNCTION update_municipalities_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_municipalities_timestamp ON municipalities;
CREATE TRIGGER trigger_update_municipalities_timestamp
    BEFORE UPDATE ON municipalities
    FOR EACH ROW
    EXECUTE FUNCTION update_municipalities_timestamp();

-- ============================================================================
-- OWNER STANDARDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS owner_standards (
    owner_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID,

    -- Core identification
    owner_code VARCHAR(20) NOT NULL UNIQUE,
    owner_name VARCHAR(255) NOT NULL,
    owner_full_name TEXT,

    -- Classification
    owner_type VARCHAR(50),                            -- 'MUNICIPAL', 'PRIVATE', 'HOA', 'UTILITY_COMPANY', 'STATE', 'FEDERAL'
    category VARCHAR(50),                              -- 'Public', 'Private', 'Quasi-Public'

    -- Organization details
    parent_organization VARCHAR(255),
    municipality_id UUID REFERENCES municipalities(municipality_id) ON DELETE SET NULL,

    -- Contact information
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    website VARCHAR(500),
    emergency_contact VARCHAR(255),
    emergency_phone VARCHAR(50),

    -- Operational details
    maintenance_responsibility TEXT,
    inspection_requirements TEXT,
    permitting_authority BOOLEAN DEFAULT false,

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_owner_code_uppercase CHECK (owner_code = UPPER(owner_code))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_owner_standards_code ON owner_standards(owner_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_owner_standards_type ON owner_standards(owner_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_owner_standards_municipality ON owner_standards(municipality_id);
CREATE INDEX IF NOT EXISTS idx_owner_standards_active ON owner_standards(is_active);

-- Comments
COMMENT ON TABLE owner_standards IS 'Controlled vocabulary for utility owners - enforces truth-driven architecture';
COMMENT ON COLUMN owner_standards.owner_code IS 'Unique short code (e.g., CITY, PRIVATE, PGE) - must be uppercase';
COMMENT ON COLUMN owner_standards.owner_name IS 'Owner display name (e.g., City of San Jose, Private Owner)';
COMMENT ON COLUMN owner_standards.owner_type IS 'Type of ownership (MUNICIPAL, PRIVATE, HOA, UTILITY_COMPANY, etc.)';

-- Update trigger
CREATE OR REPLACE FUNCTION update_owner_standards_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_owner_standards_timestamp ON owner_standards;
CREATE TRIGGER trigger_update_owner_standards_timestamp
    BEFORE UPDATE ON owner_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_owner_standards_timestamp();

-- ============================================================================
-- SEED DATA - Standard Municipalities
-- ============================================================================

-- Note: These are placeholder examples. Replace with actual jurisdictions for your region.
INSERT INTO municipalities (municipality_name, short_name, municipality_type, state) VALUES
('City of San Jose', 'San Jose', 'City', 'CA'),
('Santa Clara County', 'SCC', 'County', 'CA'),
('California Department of Transportation', 'Caltrans', 'State Agency', 'CA'),
('Santa Clara Valley Water District', 'Valley Water', 'Special District', 'CA'),
('San Jose Water Company', 'SJWC', 'Water District', 'CA')
ON CONFLICT (municipality_name) DO NOTHING;

-- ============================================================================
-- SEED DATA - Standard Owners
-- ============================================================================

INSERT INTO owner_standards (owner_code, owner_name, owner_type, category) VALUES
-- Municipal Owners
('CITY', 'City (Municipal)', 'MUNICIPAL', 'Public'),
('COUNTY', 'County', 'MUNICIPAL', 'Public'),
('STATE', 'State', 'STATE', 'Public'),
('FEDERAL', 'Federal Government', 'FEDERAL', 'Public'),

-- Utility Companies
('PGE', 'Pacific Gas & Electric', 'UTILITY_COMPANY', 'Quasi-Public'),
('ATT', 'AT&T', 'UTILITY_COMPANY', 'Private'),
('COMCAST', 'Comcast', 'UTILITY_COMPANY', 'Private'),

-- Private Owners
('PRIVATE', 'Private Owner', 'PRIVATE', 'Private'),
('HOA', 'Homeowners Association', 'HOA', 'Private'),
('DEVELOPER', 'Developer', 'PRIVATE', 'Private'),

-- Special Districts
('WATER_DISTRICT', 'Water District', 'UTILITY_COMPANY', 'Public'),
('SANITATION', 'Sanitation District', 'UTILITY_COMPANY', 'Public'),

-- Other
('UNKNOWN', 'Unknown Owner', 'PRIVATE', 'Unknown'),
('MULTIPLE', 'Multiple Owners', 'PRIVATE', 'Mixed')
ON CONFLICT (owner_code) DO NOTHING;

-- Verify seed data
DO $$
DECLARE
    municipality_count INTEGER;
    owner_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO municipality_count FROM municipalities;
    SELECT COUNT(*) INTO owner_count FROM owner_standards;
    RAISE NOTICE 'Municipalities table created with % records', municipality_count;
    RAISE NOTICE 'Owner standards table created with % records', owner_count;
END $$;
