-- ============================================================================
-- STANDARD CATEGORIES MANAGEMENT SYSTEM
-- ============================================================================
-- Purpose: Centralized category management for all CAD standards
-- Replaces free-form text entry with controlled vocabulary dropdowns
-- ============================================================================

-- Main categories table
CREATE TABLE IF NOT EXISTS standard_categories (
    category_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'CIVIL', 'SURVEY', 'UTILITIES'
    category_name VARCHAR(255) NOT NULL,        -- e.g., 'Civil Engineering', 'Survey Monuments'
    description TEXT,
    parent_category_id UUID REFERENCES standard_categories(category_id),  -- For future hierarchy
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table: maps categories to standard types
CREATE TABLE IF NOT EXISTS standard_category_applications (
    category_application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES standard_categories(category_id) ON DELETE CASCADE,
    standard_type VARCHAR(50) NOT NULL,  -- 'layers', 'blocks', 'details', 'hatches', 'materials', 'notes', etc.
    is_primary BOOLEAN DEFAULT FALSE,    -- Is this a primary/recommended category for this standard type?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, standard_type),
    CHECK (standard_type IN ('layers', 'blocks', 'details', 'hatches', 'materials', 'notes', 'linetypes', 'text_styles', 'dimension_styles', 'abbreviations'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_standard_categories_code ON standard_categories(category_code);
CREATE INDEX IF NOT EXISTS idx_standard_categories_active ON standard_categories(is_active);
CREATE INDEX IF NOT EXISTS idx_category_applications_type ON standard_category_applications(standard_type);
CREATE INDEX IF NOT EXISTS idx_category_applications_category ON standard_category_applications(category_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_standard_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_standard_categories_updated_at
    BEFORE UPDATE ON standard_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_standard_categories_updated_at();

COMMENT ON TABLE standard_categories IS 'Centralized category management for CAD standards - replaces free-form text entry';
COMMENT ON TABLE standard_category_applications IS 'Maps categories to specific standard types (layers, blocks, etc.)';
