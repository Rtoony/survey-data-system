-- ==============================================================================
-- Attribute Codes Reference Table
-- ==============================================================================
-- Purpose: Normalize and manage all valid ATTRIBUTE values used in layer classification
-- Created: 2025-11-16
--
-- This table elevates ATTRIBUTE from passive metadata in layer patterns to a
-- first-class reference dimension that specialized tools can filter on.
--
-- Examples:
-- - Size: 12IN, 8IN, 24IN
-- - Material: PVC, RCP, CONC
-- - Type: STORAGE, TREATMENT, DETENTION, TOPO, CONTROL
-- ==============================================================================

CREATE TABLE IF NOT EXISTS attribute_codes (
    attribute_id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Categorization
    attribute_type VARCHAR(50),  -- size, material, type, function, custom
    
    -- Lock status (prevents deletion/modification of system-critical attributes)
    is_locked BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Sorting
    sort_order INTEGER DEFAULT 100,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_attribute_code_uppercase CHECK (code = UPPER(code))
);

CREATE INDEX idx_attribute_codes_code ON attribute_codes(code);
CREATE INDEX idx_attribute_codes_active ON attribute_codes(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_attribute_codes_type ON attribute_codes(attribute_type) WHERE attribute_type IS NOT NULL;
CREATE INDEX idx_attribute_codes_locked ON attribute_codes(is_locked);

COMMENT ON TABLE attribute_codes IS 'Reference table for all valid ATTRIBUTE values used in layer classification';
COMMENT ON COLUMN attribute_codes.code IS 'Attribute code as used in layer names (e.g., 12IN, PVC, STORAGE)';
COMMENT ON COLUMN attribute_codes.attribute_type IS 'Category: size, material, type, function, custom';
COMMENT ON COLUMN attribute_codes.is_locked IS 'System-critical attributes cannot be deleted or renamed';

-- ==============================================================================
-- Trigger for updated_at timestamp
-- ==============================================================================
CREATE OR REPLACE FUNCTION update_attribute_codes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_attribute_codes_updated_at ON attribute_codes;
CREATE TRIGGER update_attribute_codes_updated_at
BEFORE UPDATE ON attribute_codes
FOR EACH ROW
EXECUTE FUNCTION update_attribute_codes_updated_at();
