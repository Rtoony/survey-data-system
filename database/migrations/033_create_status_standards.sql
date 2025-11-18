-- Migration 033: Create Status Standards Table
-- Part of Truth-Driven Architecture Phase 2
-- Date: 2025-11-18
--
-- Purpose: Create controlled vocabulary for status codes (EXISTING, PROPOSED, ABANDONED, etc.)
-- Used by utilities, projects, and other entities throughout the system

-- ============================================================================
-- STATUS STANDARDS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS status_standards (
    status_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entity_id UUID,

    -- Core identification
    status_code VARCHAR(20) NOT NULL UNIQUE,
    status_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Classification
    applies_to VARCHAR(50) NOT NULL,                  -- 'UTILITY', 'DRAWING', 'PROJECT', 'ALL'
    status_category VARCHAR(50),                      -- 'Active', 'Inactive', 'Planning', 'Historical'

    -- Visual representation
    color_hex VARCHAR(7) DEFAULT '#808080',            -- Color for status indicator
    icon VARCHAR(50),                                  -- Icon name for UI
    display_order INTEGER,

    -- Workflow
    is_terminal BOOLEAN DEFAULT false,                 -- Is this a final state?
    allows_editing BOOLEAN DEFAULT true,               -- Can records with this status be edited?
    next_valid_statuses TEXT[],                        -- Array of status_codes that can follow this one

    -- Business rules
    requires_approval BOOLEAN DEFAULT false,           -- Does transition to this status require approval?
    approval_role VARCHAR(50),                         -- Role required to approve (if requires_approval=true)

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_deprecated BOOLEAN DEFAULT false,
    replaced_by_id UUID REFERENCES status_standards(status_id) ON DELETE SET NULL,

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_status_code_uppercase CHECK (status_code = UPPER(status_code)),
    CONSTRAINT check_color_format_status CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$'),
    CONSTRAINT check_applies_to_valid CHECK (applies_to IN ('UTILITY', 'DRAWING', 'PROJECT', 'ALL'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_status_code ON status_standards(status_code) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_status_applies_to ON status_standards(applies_to) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_status_active ON status_standards(is_active);

-- Comments
COMMENT ON TABLE status_standards IS 'Controlled vocabulary for status codes across all entity types - enforces truth-driven architecture';
COMMENT ON COLUMN status_standards.status_code IS 'Unique status code (e.g., EXISTING, PROPOSED, ABANDONED) - must be uppercase';
COMMENT ON COLUMN status_standards.status_name IS 'Full status name displayed in UI';
COMMENT ON COLUMN status_standards.applies_to IS 'Which entity types can use this status (UTILITY, DRAWING, PROJECT, ALL)';
COMMENT ON COLUMN status_standards.is_terminal IS 'Is this a final state that cannot be changed?';
COMMENT ON COLUMN status_standards.next_valid_statuses IS 'Array of status_codes that can follow this status (workflow validation)';

-- Update trigger
CREATE OR REPLACE FUNCTION update_status_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_status_timestamp
    BEFORE UPDATE ON status_standards
    FOR EACH ROW
    EXECUTE FUNCTION update_status_timestamp();

-- ============================================================================
-- SEED DATA - Standard Status Codes
-- ============================================================================

INSERT INTO status_standards (status_code, status_name, applies_to, status_category, color_hex, display_order, is_terminal, allows_editing, description) VALUES
-- Utility Status Codes
('EXISTING', 'Existing', 'UTILITY', 'Active', '#008000', 1, false, true, 'Utility currently in service and operational'),
('PROPOSED', 'Proposed', 'UTILITY', 'Planning', '#0000FF', 2, false, true, 'Utility planned for future construction'),
('ABANDONED', 'Abandoned', 'UTILITY', 'Historical', '#808080', 3, true, false, 'Utility no longer in service, left in place'),
('REMOVED', 'Removed', 'UTILITY', 'Historical', '#000000', 4, true, false, 'Utility removed from service and physically removed'),
('TEMPORARY', 'Temporary', 'UTILITY', 'Active', '#FFAA00', 5, false, true, 'Temporary utility installation'),
('RELOCATED', 'Relocated', 'UTILITY', 'Historical', '#FF00FF', 6, true, false, 'Utility was relocated to new location'),
('FUTURE', 'Future', 'UTILITY', 'Planning', '#ADD8E6', 7, false, true, 'Utility for long-term future development'),

-- Project Status Codes
('ACTIVE', 'Active', 'PROJECT', 'Active', '#00CC00', 11, false, true, 'Project currently in progress'),
('PLANNING', 'Planning', 'PROJECT', 'Planning', '#3399FF', 12, false, true, 'Project in planning phase'),
('COMPLETE', 'Complete', 'PROJECT', 'Inactive', '#006600', 13, true, false, 'Project completed and closed'),
('ON_HOLD', 'On Hold', 'PROJECT', 'Inactive', '#FFAA00', 14, false, true, 'Project temporarily paused'),
('CANCELLED', 'Cancelled', 'PROJECT', 'Inactive', '#CC0000', 15, true, false, 'Project cancelled and will not proceed'),
('ARCHIVED', 'Archived', 'PROJECT', 'Inactive', '#666666', 16, true, false, 'Project archived for historical record'),

-- Drawing Status Codes
('DRAFT', 'Draft', 'DRAWING', 'Planning', '#FFFF00', 21, false, true, 'Drawing in draft stage'),
('REVIEW', 'Under Review', 'DRAWING', 'Planning', '#FFA500', 22, false, true, 'Drawing submitted for review'),
('APPROVED', 'Approved', 'DRAWING', 'Active', '#00AA00', 23, false, false, 'Drawing approved for use'),
('ISSUED', 'Issued', 'DRAWING', 'Active', '#0066CC', 24, false, false, 'Drawing officially issued'),
('SUPERSEDED', 'Superseded', 'DRAWING', 'Historical', '#999999', 25, true, false, 'Drawing replaced by newer version'),
('VOID', 'Void', 'DRAWING', 'Historical', '#FF0000', 26, true, false, 'Drawing voided and should not be used'),

-- Universal Status Codes (can be used by any entity type)
('UNKNOWN', 'Unknown', 'ALL', 'Active', '#CCCCCC', 91, false, true, 'Status not yet determined'),
('VERIFY', 'Needs Verification', 'ALL', 'Active', '#FF9900', 92, false, true, 'Status needs to be verified in field'),
('CONFLICT', 'Conflict', 'ALL', 'Active', '#CC00CC', 93, false, true, 'Conflicting information needs resolution')
ON CONFLICT (status_code) DO NOTHING;

-- Verify seed data
DO $$
DECLARE
    record_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM status_standards;
    RAISE NOTICE 'Status standards table created with % records', record_count;
END $$;

-- ============================================================================
-- ADD STATUS COLUMN TO UTILITY TABLES
-- ============================================================================

-- Add status column to utility_lines if it doesn't exist
ALTER TABLE utility_lines
ADD COLUMN IF NOT EXISTS status VARCHAR(20);

-- Add status column to utility_structures if it doesn't exist
ALTER TABLE utility_structures
ADD COLUMN IF NOT EXISTS status VARCHAR(20);

-- Set default status for existing records (those without a status value)
UPDATE utility_lines
SET status = 'EXISTING'
WHERE status IS NULL;

UPDATE utility_structures
SET status = 'EXISTING'
WHERE status IS NULL;

-- Add comments
COMMENT ON COLUMN utility_lines.status IS 'Status of utility line - must match status_standards.status_code where applies_to IN (UTILITY, ALL)';
COMMENT ON COLUMN utility_structures.status IS 'Status of utility structure - must match status_standards.status_code where applies_to IN (UTILITY, ALL)';

-- Verify columns were added
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'utility_lines' AND column_name = 'status'
    ) THEN
        RAISE NOTICE 'SUCCESS: status column added to utility_lines';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'utility_structures' AND column_name = 'status'
    ) THEN
        RAISE NOTICE 'SUCCESS: status column added to utility_structures';
    END IF;
END $$;
