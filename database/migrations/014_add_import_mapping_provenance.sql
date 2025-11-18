-- ==============================================================================
-- Migration 014: Add Provenance Fields to import_mapping_patterns
-- ==============================================================================
-- Purpose: Add audit trail and provenance tracking to import mapping patterns
-- Created: 2025-11-18
-- Part of: Phase 1 - DXF Name Translator Foundation
--
-- Changes:
-- 1. Add created_by, modified_by, modified_at columns
-- 2. Add indexes for performance
-- 3. Add trigger to auto-update modified_at
-- ==============================================================================

-- Add provenance columns
ALTER TABLE import_mapping_patterns
ADD COLUMN IF NOT EXISTS created_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS modified_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS modified_at TIMESTAMP;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_import_mapping_patterns_is_active
    ON import_mapping_patterns(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_import_mapping_patterns_confidence
    ON import_mapping_patterns(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_import_mapping_patterns_created_at
    ON import_mapping_patterns(created_at DESC);

-- Create trigger to auto-update modified_at and modified_by
CREATE OR REPLACE FUNCTION update_import_mapping_modified() RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    -- If modified_by is not explicitly set in the UPDATE, keep the old value
    IF NEW.modified_by IS NULL THEN
        NEW.modified_by = OLD.modified_by;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS import_mapping_patterns_modified_trigger ON import_mapping_patterns;

CREATE TRIGGER import_mapping_patterns_modified_trigger
    BEFORE UPDATE ON import_mapping_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_import_mapping_modified();

-- Add comments for documentation
COMMENT ON COLUMN import_mapping_patterns.created_by IS 'User who created this pattern';
COMMENT ON COLUMN import_mapping_patterns.modified_by IS 'User who last modified this pattern';
COMMENT ON COLUMN import_mapping_patterns.modified_at IS 'Timestamp of last modification';

-- ==============================================================================
-- End of Migration 014
-- ==============================================================================
