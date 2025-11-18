-- Migration 021: Enhance import_mapping_patterns table
-- Adds provenance tracking, status management, and performance indexes
-- Based on Phase 2 DXF Name Translator Audit

-- Add provenance and lifecycle columns
ALTER TABLE import_mapping_patterns
    ADD COLUMN IF NOT EXISTS created_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS modified_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS modified_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1,
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255),
    ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

-- Backfill created_by for existing records
UPDATE import_mapping_patterns
SET created_by = 'system'
WHERE created_by IS NULL;

-- Backfill status for existing active patterns
UPDATE import_mapping_patterns
SET status = 'active', approved_by = 'system', approved_at = created_at
WHERE is_active = TRUE AND status = 'active' AND approved_by IS NULL;

-- Add check constraint for status values
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_import_mapping_status'
    ) THEN
        ALTER TABLE import_mapping_patterns
        ADD CONSTRAINT check_import_mapping_status
        CHECK (status IN ('draft', 'pending', 'approved', 'active', 'deprecated'));
    END IF;
END $$;

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_import_mapping_is_active
    ON import_mapping_patterns(is_active) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_import_mapping_confidence
    ON import_mapping_patterns(confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_import_mapping_status
    ON import_mapping_patterns(status);

CREATE INDEX IF NOT EXISTS idx_import_mapping_discipline
    ON import_mapping_patterns(target_discipline_id);

-- Create trigger to update modified_at and modified_by
CREATE OR REPLACE FUNCTION update_import_mapping_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_import_mapping_patterns_modified') THEN
        CREATE TRIGGER update_import_mapping_patterns_modified
        BEFORE UPDATE ON import_mapping_patterns
        FOR EACH ROW EXECUTE FUNCTION update_import_mapping_modified();
    END IF;
END $$;

-- Add comments
COMMENT ON COLUMN import_mapping_patterns.created_by IS 'User who created this pattern';
COMMENT ON COLUMN import_mapping_patterns.modified_by IS 'User who last modified this pattern';
COMMENT ON COLUMN import_mapping_patterns.modified_at IS 'Timestamp of last modification';
COMMENT ON COLUMN import_mapping_patterns.status IS 'Lifecycle status: draft, pending, approved, active, deprecated';
COMMENT ON COLUMN import_mapping_patterns.version IS 'Version number for tracking pattern changes';
COMMENT ON COLUMN import_mapping_patterns.description IS 'Detailed description of pattern purpose';
COMMENT ON COLUMN import_mapping_patterns.approved_by IS 'User who approved this pattern for production';
COMMENT ON COLUMN import_mapping_patterns.approved_at IS 'Timestamp when pattern was approved';
